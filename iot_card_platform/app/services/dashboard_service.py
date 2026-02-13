"""
仪表盘服务层
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.db.models.iot_card import IotCardModel, CardStatus, CARD_STATUS_NAMES
from app.db.models.package import CarrierType, CARRIER_NAMES
from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.db.models.package import SupplierPackageModel, SalePackageModel
from app.db.models.pool import TrafficPoolModel
from app.db.models.suspend import AlertLogModel, SuspendLogModel, AlertLevel, ALERT_LEVEL_NAMES
from app.schemas.dashboard import (
    CardStats, CardStatsItem, UserStats, PackageStats, PoolStats, AlertStats,
    DashboardOverview, UsageTrend, UsageTrendItem
)


class DashboardService:
    """仪表盘服务"""

    @staticmethod
    async def get_card_stats(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> CardStats:
        """获取卡片统计"""
        # 基础查询条件
        base_condition = [IotCardModel.is_deleted == 0]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        # 总数
        total_result = await db.execute(
            select(func.count(IotCardModel.id)).where(*base_condition)
        )
        total = total_result.scalar() or 0

        # 按状态统计
        status_result = await db.execute(
            select(
                IotCardModel.status,
                func.count(IotCardModel.id).label('count')
            ).where(*base_condition).group_by(IotCardModel.status)
        )
        by_status = []
        for row in status_result.all():
            status_value = row[0].value if row[0] else "unknown"
            by_status.append(CardStatsItem(
                status=status_value,
                status_name=CARD_STATUS_NAMES.get(status_value, "未知"),
                count=row[1]
            ))

        # 按运营商统计
        carrier_result = await db.execute(
            select(
                IotCardModel.carrier,
                func.count(IotCardModel.id).label('count')
            ).where(*base_condition).group_by(IotCardModel.carrier)
        )
        by_carrier = []
        for row in carrier_result.all():
            carrier_value = row[0].value if row[0] else "unknown"
            by_carrier.append({
                "carrier": carrier_value,
                "carrier_name": CARRIER_NAMES.get(carrier_value, "未知"),
                "count": row[1]
            })

        return CardStats(
            total=total,
            by_status=by_status,
            by_carrier=by_carrier
        )

    @staticmethod
    async def get_user_stats(db: AsyncSession) -> UserStats:
        """获取用户统计"""
        # 用户总数 (user_level=2)
        users_result = await db.execute(
            select(func.count(SysUserModel.id)).where(
                SysUserModel.is_deleted == 0,
                SysUserModel.user_level == 2
            )
        )
        total_users = users_result.scalar() or 0

        # 子用户总数 (user_level=3)
        sub_users_result = await db.execute(
            select(func.count(SysUserModel.id)).where(
                SysUserModel.is_deleted == 0,
                SysUserModel.user_level == 3
            )
        )
        total_sub_users = sub_users_result.scalar() or 0

        # 活跃用户 (7天内有登录)
        seven_days_ago = datetime.now() - timedelta(days=7)
        active_result = await db.execute(
            select(func.count(SysUserModel.id)).where(
                SysUserModel.is_deleted == 0,
                SysUserModel.user_level.in_([2, 3]),
                SysUserModel.last_login_at >= seven_days_ago
            )
        )
        active_users = active_result.scalar() or 0

        return UserStats(
            total_users=total_users,
            total_sub_users=total_sub_users,
            active_users=active_users
        )

    @staticmethod
    async def get_package_stats(db: AsyncSession) -> PackageStats:
        """获取套餐统计"""
        # 底层套餐数
        supplier_result = await db.execute(
            select(func.count(SupplierPackageModel.id)).where(
                SupplierPackageModel.is_deleted == 0
            )
        )
        supplier_packages = supplier_result.scalar() or 0

        # 销售套餐数
        sale_result = await db.execute(
            select(func.count(SalePackageModel.id)).where(
                SalePackageModel.is_deleted == 0
            )
        )
        sale_packages = sale_result.scalar() or 0

        return PackageStats(
            supplier_packages=supplier_packages,
            sale_packages=sale_packages
        )

    @staticmethod
    async def get_pool_stats(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> PoolStats:
        """获取流量池统计"""
        base_condition = [TrafficPoolModel.is_deleted == 0]
        if user_id:
            base_condition.append(TrafficPoolModel.user_id == user_id)

        result = await db.execute(
            select(
                func.count(TrafficPoolModel.id).label('count'),
                func.sum(TrafficPoolModel.data_total).label('total'),
                func.sum(TrafficPoolModel.data_used).label('used')
            ).where(*base_condition)
        )
        row = result.first()
        
        total_pools = row[0] or 0
        total_data = row[1] or 0
        used_data = row[2] or 0
        usage_percent = round((used_data / total_data * 100), 2) if total_data > 0 else 0

        return PoolStats(
            total_pools=total_pools,
            total_data=total_data,
            used_data=used_data,
            usage_percent=usage_percent
        )

    @staticmethod
    async def get_alert_stats(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> AlertStats:
        """获取告警统计"""
        base_condition = [
            AlertLogModel.is_deleted == 0,
            AlertLogModel.handled == 0
        ]
        if user_id:
            base_condition.append(AlertLogModel.user_id == user_id)

        result = await db.execute(
            select(
                AlertLogModel.alert_level,
                func.count(AlertLogModel.id).label('count')
            ).where(*base_condition).group_by(AlertLogModel.alert_level)
        )
        
        stats = {"warning": 0, "critical": 0, "exceed": 0}
        total = 0
        for row in result.all():
            level = row[0].value if row[0] else "unknown"
            count = row[1]
            if level in stats:
                stats[level] = count
            total += count

        return AlertStats(
            warning=stats["warning"],
            critical=stats["critical"],
            exceed=stats["exceed"],
            unhandled=total
        )

    @staticmethod
    async def get_overview(
        db: AsyncSession,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> DashboardOverview:
        """获取仪表盘总览"""
        # 管理员看全部，普通用户只看自己的
        card_user_id = None if is_admin else user_id
        
        cards = await DashboardService.get_card_stats(db, card_user_id)
        users = await DashboardService.get_user_stats(db) if is_admin else UserStats()
        packages = await DashboardService.get_package_stats(db)
        pools = await DashboardService.get_pool_stats(db, card_user_id)
        alerts = await DashboardService.get_alert_stats(db, card_user_id)

        return DashboardOverview(
            cards=cards,
            users=users,
            packages=packages,
            pools=pools,
            alerts=alerts
        )

    @staticmethod
    async def get_usage_trend(
        db: AsyncSession,
        period: str = "daily",
        days: int = 7,
        user_id: Optional[int] = None
    ) -> UsageTrend:
        """获取流量趋势 (简化版 - 基于当前数据)"""
        # 注意：真实场景需要有流量历史记录表
        # 这里简化为返回当前卡片的用量分布
        
        base_condition = [
            IotCardModel.is_deleted == 0,
            IotCardModel.status == CardStatus.activated
        ]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        result = await db.execute(
            select(
                func.sum(IotCardModel.data_used).label('used'),
                func.sum(IotCardModel.data_total).label('total')
            ).where(*base_condition)
        )
        row = result.first()
        total_used = row[0] or 0
        total_data = row[1] or 0

        # 生成趋势数据 (模拟)
        data = []
        today = datetime.now().date()
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            # 简化：假设用量均匀分布
            daily_used = int(total_used / days) if days > 0 else 0
            daily_total = int(total_data / days) if days > 0 else 0
            data.append(UsageTrendItem(
                date=date.strftime("%Y-%m-%d"),
                used=daily_used,
                total=daily_total
            ))

        return UsageTrend(period=period, data=data)

    @staticmethod
    async def get_recent_alerts(
        db: AsyncSession,
        limit: int = 10,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取最近告警"""
        base_condition = [AlertLogModel.is_deleted == 0]
        if user_id:
            base_condition.append(AlertLogModel.user_id == user_id)

        result = await db.execute(
            select(AlertLogModel)
            .where(*base_condition)
            .order_by(AlertLogModel.created_at.desc())
            .limit(limit)
        )
        alerts = result.scalars().all()
        
        return [
            {
                "id": a.id,
                "target_type": a.target_type.value if a.target_type else None,
                "target_name": a.target_name,
                "alert_level": a.alert_level.value if a.alert_level else None,
                "alert_level_name": ALERT_LEVEL_NAMES.get(a.alert_level.value, "") if a.alert_level else "",
                "usage_percent": a.usage_percent,
                "handled": a.handled == 1,
                "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else None
            }
            for a in alerts
        ]

    @staticmethod
    async def get_recent_activities(
        db: AsyncSession,
        limit: int = 10,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取最近活动 (停卡/复机记录)"""
        from app.db.models.suspend import SUSPEND_ACTION_NAMES
        
        base_condition = [SuspendLogModel.is_deleted == 0]
        # 暂不按用户过滤活动记录

        result = await db.execute(
            select(SuspendLogModel)
            .where(*base_condition)
            .order_by(SuspendLogModel.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "action": log.action.value if log.action else None,
                "action_name": SUSPEND_ACTION_NAMES.get(log.action.value, "") if log.action else "",
                "target": log.iccid,
                "suspend_type": log.suspend_type,
                "reason": log.reason,
                "operator_id": log.operator_id,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None
            }
            for log in logs
        ]

    @staticmethod
    async def get_account_balance(
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """获取账户余额信息"""
        # 简化版：返回模拟数据
        # 实际应该从账户余额表中查询
        return {
            "balance": 0,
            "alert_threshold": 1000,
            "is_alert": False,
            "last_recharge_at": None,
            "last_recharge_amount": 0
        }

    @staticmethod
    async def get_pools_usage_percent(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取流量池用量百分比"""
        base_condition = [TrafficPoolModel.is_deleted == 0]
        if user_id:
            base_condition.append(TrafficPoolModel.user_id == user_id)

        result = await db.execute(
            select(TrafficPoolModel)
            .where(*base_condition)
            .order_by(TrafficPoolModel.id.desc())
            .limit(10)
        )
        pools = result.scalars().all()
        
        return [
            {
                "id": pool.id,
                "name": pool.name,
                "carrier": pool.carrier.value if pool.carrier else None,
                "data_total": pool.data_total,
                "data_used": pool.data_used,
                "usage_percent": pool.get_usage_percent(),
                "card_count": pool.card_count,
                "is_alert": pool.is_alert()
            }
            for pool in pools
        ]

    @staticmethod
    async def get_expiring_cards(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取本月到期卡明细"""
        # 本月底
        today = datetime.now()
        # 计算本月最后一天
        if today.month == 12:
            next_month = datetime(today.year + 1, 1, 1)
        else:
            next_month = datetime(today.year, today.month + 1, 1)
        month_end = next_month - timedelta(days=1)
        
        base_condition = [
            IotCardModel.is_deleted == 0,
            IotCardModel.status.in_([CardStatus.activated, CardStatus.testing, CardStatus.silent]),
            IotCardModel.silent_expire_date <= month_end.date()
        ]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        result = await db.execute(
            select(IotCardModel)
            .where(*base_condition)
            .order_by(IotCardModel.silent_expire_date.asc())
            .limit(50)
        )
        cards = result.scalars().all()
        
        return [
            {
                "id": card.id,
                "iccid": card.iccid,
                "msisdn": card.msisdn,
                "carrier": card.carrier.value if card.carrier else None,
                "expired_at": card.silent_expire_date.strftime("%Y-%m-%d") if card.silent_expire_date else None,
                "days_left": (card.silent_expire_date - today.date()).days if card.silent_expire_date else 0,
                "user_name": "",
                "package_name": ""
            }
            for card in cards
        ]

    @staticmethod
    async def get_over_usage_cards(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取超量卡明细"""
        base_condition = [
            IotCardModel.is_deleted == 0,
            IotCardModel.status == CardStatus.activated,
            IotCardModel.data_total > 0
        ]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        result = await db.execute(
            select(IotCardModel)
            .where(*base_condition)
        )
        cards = result.scalars().all()
        
        # 筛选超量卡（使用率 > 100%）
        over_usage_cards = []
        for card in cards:
            usage_percent = (card.data_used / card.data_total * 100) if card.data_total > 0 else 0
            if usage_percent > 100:
                over_usage_cards.append({
                    "id": card.id,
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "carrier": card.carrier.value if card.carrier else None,
                    "data_used": card.data_used,
                    "data_total": card.data_total,
                    "usage_percent": round(usage_percent, 2),
                    "over_usage": card.data_used - card.data_total,
                    "user_name": ""
                })
        
        # 按超量从大到小排序
        over_usage_cards.sort(key=lambda x: x["over_usage"], reverse=True)
        
        return over_usage_cards[:50]  # 最多返回50条

    @staticmethod
    async def get_account_balance(
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """获取账户余额信息"""
        # 简化版：返回模拟数据
        # 实际应该从账户余额表中查询
        return {
            "balance": 0,
            "alert_threshold": 1000,
            "is_alert": False,
            "last_recharge_at": None,
            "last_recharge_amount": 0
        }

    @staticmethod
    async def get_pools_usage_percent(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取流量池用量百分比"""
        base_condition = [TrafficPoolModel.is_deleted == 0]
        if user_id:
            base_condition.append(TrafficPoolModel.user_id == user_id)

        result = await db.execute(
            select(TrafficPoolModel)
            .where(*base_condition)
            .order_by(TrafficPoolModel.id.desc())
            .limit(10)
        )
        pools = result.scalars().all()
        
        return [
            {
                "id": pool.id,
                "name": pool.name,
                "carrier": pool.carrier.value if pool.carrier else None,
                "data_total": pool.data_total,
                "data_used": pool.data_used,
                "usage_percent": pool.get_usage_percent(),
                "card_count": pool.card_count,
                "is_alert": pool.is_alert()
            }
            for pool in pools
        ]

    @staticmethod
    async def get_expiring_cards(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取本月到期卡明细"""
        # 本月底
        today = datetime.now()
        # 计算本月最后一天
        if today.month == 12:
            next_month = datetime(today.year + 1, 1, 1)
        else:
            next_month = datetime(today.year, today.month + 1, 1)
        month_end = next_month - timedelta(days=1)
        
        base_condition = [
            IotCardModel.is_deleted == 0,
            IotCardModel.status.in_([CardStatus.activated, CardStatus.testing, CardStatus.silent]),
            IotCardModel.silent_expire_date <= month_end.date()
        ]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        result = await db.execute(
            select(IotCardModel)
            .where(*base_condition)
            .order_by(IotCardModel.silent_expire_date.asc())
            .limit(50)
        )
        cards = result.scalars().all()
        
        return [
            {
                "id": card.id,
                "iccid": card.iccid,
                "msisdn": card.msisdn,
                "carrier": card.carrier.value if card.carrier else None,
                "expired_at": card.silent_expire_date.strftime("%Y-%m-%d") if card.silent_expire_date else None,
                "days_left": (card.silent_expire_date - today.date()).days if card.silent_expire_date else 0,
                "user_name": "",
                "package_name": ""
            }
            for card in cards
        ]

    @staticmethod
    async def get_over_usage_cards(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取超量卡明细"""
        base_condition = [
            IotCardModel.is_deleted == 0,
            IotCardModel.status == CardStatus.activated,
            IotCardModel.data_total > 0
        ]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        result = await db.execute(
            select(IotCardModel)
            .where(*base_condition)
        )
        cards = result.scalars().all()
        
        # 筛选超量卡（使用率 > 100%）
        over_usage_cards = []
        for card in cards:
            usage_percent = (card.data_used / card.data_total * 100) if card.data_total > 0 else 0
            if usage_percent > 100:
                over_usage_cards.append({
                    "id": card.id,
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "carrier": card.carrier.value if card.carrier else None,
                    "data_used": card.data_used,
                    "data_total": card.data_total,
                    "usage_percent": round(usage_percent, 2),
                    "over_usage": card.data_used - card.data_total,
                    "user_name": ""
                })
        
        # 按超量从大到小排序
        over_usage_cards.sort(key=lambda x: x["over_usage"], reverse=True)
        
        return over_usage_cards[:50]  # 最多返回50条

    @staticmethod
    async def get_account_balance(
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """获取账户余额信息"""
        # 简化版：返回模拟数据
        # 实际应该从账户余额表中查询
        return {
            "balance": 0,
            "alert_threshold": 1000,
            "is_alert": False,
            "last_recharge_at": None,
            "last_recharge_amount": 0
        }

    @staticmethod
    async def get_pools_usage_percent(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取流量池用量百分比"""
        base_condition = [TrafficPoolModel.is_deleted == 0]
        if user_id:
            base_condition.append(TrafficPoolModel.user_id == user_id)

        result = await db.execute(
            select(TrafficPoolModel)
            .where(*base_condition)
            .order_by(TrafficPoolModel.id.desc())
            .limit(10)
        )
        pools = result.scalars().all()
        
        return [
            {
                "id": pool.id,
                "name": pool.name,
                "carrier": pool.carrier.value if pool.carrier else None,
                "data_total": pool.data_total,
                "data_used": pool.data_used,
                "usage_percent": pool.get_usage_percent(),
                "card_count": pool.card_count,
                "is_alert": pool.is_alert()
            }
            for pool in pools
        ]

    @staticmethod
    async def get_expiring_cards(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取本月到期卡明细"""
        # 本月底
        today = datetime.now()
        # 计算本月最后一天
        if today.month == 12:
            next_month = datetime(today.year + 1, 1, 1)
        else:
            next_month = datetime(today.year, today.month + 1, 1)
        month_end = next_month - timedelta(days=1)
        
        base_condition = [
            IotCardModel.is_deleted == 0,
            IotCardModel.status.in_([CardStatus.activated, CardStatus.testing, CardStatus.silent]),
            IotCardModel.silent_expire_date <= month_end.date()
        ]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        result = await db.execute(
            select(IotCardModel)
            .where(*base_condition)
            .order_by(IotCardModel.silent_expire_date.asc())
            .limit(50)
        )
        cards = result.scalars().all()
        
        return [
            {
                "id": card.id,
                "iccid": card.iccid,
                "msisdn": card.msisdn,
                "carrier": card.carrier.value if card.carrier else None,
                "expired_at": card.silent_expire_date.strftime("%Y-%m-%d") if card.silent_expire_date else None,
                "days_left": (card.silent_expire_date - today.date()).days if card.silent_expire_date else 0,
                "user_name": "",
                "package_name": ""
            }
            for card in cards
        ]

    @staticmethod
    async def get_over_usage_cards(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取超量卡明细"""
        base_condition = [
            IotCardModel.is_deleted == 0,
            IotCardModel.status == CardStatus.activated,
            IotCardModel.data_total > 0
        ]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        result = await db.execute(
            select(IotCardModel)
            .where(*base_condition)
        )
        cards = result.scalars().all()
        
        # 筛选超量卡（使用率 > 100%）
        over_usage_cards = []
        for card in cards:
            usage_percent = (card.data_used / card.data_total * 100) if card.data_total > 0 else 0
            if usage_percent > 100:
                over_usage_cards.append({
                    "id": card.id,
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "carrier": card.carrier.value if card.carrier else None,
                    "data_used": card.data_used,
                    "data_total": card.data_total,
                    "usage_percent": round(usage_percent, 2),
                    "over_usage": card.data_used - card.data_total,
                    "user_name": ""
                })
        
        # 按超量从大到小排序
        over_usage_cards.sort(key=lambda x: x["over_usage"], reverse=True)
        
        return over_usage_cards[:50]  # 最多返回50条

    @staticmethod
    async def get_account_balance(
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """获取账户余额信息"""
        # 简化版：返回模拟数据
        # 实际应该从账户余额表中查询
        return {
            "balance": 0,
            "alert_threshold": 1000,
            "is_alert": False,
            "last_recharge_at": None,
            "last_recharge_amount": 0
        }

    @staticmethod
    async def get_pools_usage_percent(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取流量池用量百分比"""
        base_condition = [TrafficPoolModel.is_deleted == 0]
        if user_id:
            base_condition.append(TrafficPoolModel.user_id == user_id)

        result = await db.execute(
            select(TrafficPoolModel)
            .where(*base_condition)
            .order_by(TrafficPoolModel.id.desc())
            .limit(10)
        )
        pools = result.scalars().all()
        
        return [
            {
                "id": pool.id,
                "name": pool.name,
                "carrier": pool.carrier.value if pool.carrier else None,
                "data_total": pool.data_total,
                "data_used": pool.data_used,
                "usage_percent": pool.get_usage_percent(),
                "card_count": pool.card_count,
                "is_alert": pool.is_alert()
            }
            for pool in pools
        ]

    @staticmethod
    async def get_expiring_cards(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取本月到期卡明细"""
        # 本月底
        today = datetime.now()
        # 计算本月最后一天
        if today.month == 12:
            next_month = datetime(today.year + 1, 1, 1)
        else:
            next_month = datetime(today.year, today.month + 1, 1)
        month_end = next_month - timedelta(days=1)
        
        base_condition = [
            IotCardModel.is_deleted == 0,
            IotCardModel.status.in_([CardStatus.activated, CardStatus.testing, CardStatus.silent]),
            IotCardModel.silent_expire_date <= month_end.date()
        ]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        result = await db.execute(
            select(IotCardModel)
            .where(*base_condition)
            .order_by(IotCardModel.silent_expire_date.asc())
            .limit(50)
        )
        cards = result.scalars().all()
        
        return [
            {
                "id": card.id,
                "iccid": card.iccid,
                "msisdn": card.msisdn,
                "carrier": card.carrier.value if card.carrier else None,
                "expired_at": card.silent_expire_date.strftime("%Y-%m-%d") if card.silent_expire_date else None,
                "days_left": (card.silent_expire_date - today.date()).days if card.silent_expire_date else 0,
                "user_name": "",
                "package_name": ""
            }
            for card in cards
        ]

    @staticmethod
    async def get_over_usage_cards(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取超量卡明细"""
        base_condition = [
            IotCardModel.is_deleted == 0,
            IotCardModel.status == CardStatus.activated,
            IotCardModel.data_total > 0
        ]
        if user_id:
            base_condition.append(IotCardModel.user_id == user_id)

        result = await db.execute(
            select(IotCardModel)
            .where(*base_condition)
        )
        cards = result.scalars().all()
        
        # 筛选超量卡（使用率 > 100%）
        over_usage_cards = []
        for card in cards:
            usage_percent = (card.data_used / card.data_total * 100) if card.data_total > 0 else 0
            if usage_percent > 100:
                over_usage_cards.append({
                    "id": card.id,
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "carrier": card.carrier.value if card.carrier else None,
                    "data_used": card.data_used,
                    "data_total": card.data_total,
                    "usage_percent": round(usage_percent, 2),
                    "over_usage": card.data_used - card.data_total,
                    "user_name": ""
                })
        
        # 按超量从大到小排序
        over_usage_cards.sort(key=lambda x: x["over_usage"], reverse=True)
        
        return over_usage_cards[:50]  # 最多返回50条
