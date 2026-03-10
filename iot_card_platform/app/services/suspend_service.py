"""
停卡策略服务层
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
import logging

from app.crud.suspend_crud import (
    SuspendPolicyCRUD, SuspendLogCRUD, AlertLogCRUD, CardSuspendCRUD
)
from app.db.models.suspend import (
    SuspendPolicyModel, SuspendLogModel, AlertLogModel,
    SuspendActionType, AlertLevel, AlertTargetType
)
from app.db.models.iot_card import IotCardModel, CardStatus, SuspendType
from app.db.models.supplier import SupplierModel
from app.schemas.suspend import (
    PolicyCreate, PolicyUpdate, ManualSuspend, ManualResume, SuspendResult
)
from app.clients.supplier_api import get_supplier_client
from sqlalchemy import select

logger = logging.getLogger(__name__)


class SuspendPolicyService:
    """停卡策略服务"""

    @staticmethod
    async def create_policy(
        db: AsyncSession,
        data: PolicyCreate,
        created_by: int
    ) -> SuspendPolicyModel:
        """创建策略"""
        return await SuspendPolicyCRUD.create(
            db=db,
            name=data.name,
            description=data.description,
            policy_type=data.policy_type,
            warning_threshold=data.warning_threshold,
            critical_threshold=data.critical_threshold,
            stop_threshold=data.stop_threshold,
            user_id=data.user_id,
            pool_id=data.pool_id,
            auto_suspend=data.auto_suspend,
            auto_resume=data.auto_resume,
            notify_warning=data.notify_warning,
            notify_critical=data.notify_critical,
            notify_suspend=data.notify_suspend,
            is_enabled=data.is_enabled,
            created_by=created_by
        )

    @staticmethod
    async def get_policy(db: AsyncSession, policy_id: int) -> Optional[SuspendPolicyModel]:
        """获取策略详情"""
        return await SuspendPolicyCRUD.get_by_id(db, policy_id)

    @staticmethod
    async def get_policies(
        db: AsyncSession,
        policy_type: Optional[str] = None,
        user_id: Optional[int] = None,
        is_enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取策略列表"""
        policies, total = await SuspendPolicyCRUD.get_list(
            db=db,
            policy_type=policy_type,
            user_id=user_id,
            is_enabled=is_enabled,
            page=page,
            page_size=page_size
        )
        return [p.to_dict() for p in policies], total

    @staticmethod
    async def update_policy(
        db: AsyncSession,
        policy_id: int,
        data: PolicyUpdate
    ) -> Optional[SuspendPolicyModel]:
        """更新策略"""
        update_data = data.model_dump(exclude_unset=True)
        return await SuspendPolicyCRUD.update(db, policy_id, **update_data)

    @staticmethod
    async def delete_policy(db: AsyncSession, policy_id: int) -> bool:
        """删除策略"""
        return await SuspendPolicyCRUD.delete(db, policy_id)


class SuspendActionService:
    """停卡/复机操作服务"""

    @staticmethod
    async def manual_suspend(
        db: AsyncSession,
        data: ManualSuspend,
        operator_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> SuspendResult:
        """手动停卡"""
        success_cards = []
        fail_cards = []

        # 获取卡片
        cards = await CardSuspendCRUD.get_cards_by_ids(
            db, data.card_ids,
            user_id=None if is_admin else user_id
        )
        card_map = {c.id: c for c in cards}

        # 预加载供应商信息（避免N+1查询）
        supplier_ids = {c.supplier_id for c in cards if c.supplier_id}
        supplier_query = select(SupplierModel).where(
            SupplierModel.id.in_(supplier_ids),
            SupplierModel.is_deleted == 0
        )
        supplier_result = await db.execute(supplier_query)
        supplier_map = {s.id: s for s in supplier_result.scalars().all()}

        for card_id in data.card_ids:
            card = card_map.get(card_id)
            
            if not card:
                fail_cards.append({"card_id": card_id, "iccid": "未知", "reason": "卡片不存在或无权限"})
                continue

            if card.status == CardStatus.suspended:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": "卡片已停机"})
                continue

            if card.status not in [CardStatus.activated, CardStatus.testing, CardStatus.silent]:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": f"卡片状态不支持停卡: {card.status.value}"})
                continue

            # 调用供应商API停机
            api_success = False
            supplier = supplier_map.get(card.supplier_id)
            if supplier:
                try:
                    supplier_client = get_supplier_client(
                        supplier_id=card.supplier_id,
                        api_url=supplier.api_url or "",
                        api_key=supplier.api_key or "",
                        api_secret=supplier.api_secret or ""
                    )
                    api_success = await supplier_client.suspend_card(card.iccid, data.reason)
                except Exception as e:
                    logger.error(f"供应商API停机失败: iccid={card.iccid}, error={e}")

            # 只有API成功才更新数据库
            if not api_success:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": "供应商API调用失败"})
                continue

            # 执行停卡
            await CardSuspendCRUD.suspend_card(
                db=db,
                card_id=card_id,
                suspend_type=SuspendType.manual,
                reason=data.reason
            )

            # 记录日志
            await SuspendLogCRUD.create(
                db=db,
                card_id=card_id,
                iccid=card.iccid,
                action=SuspendActionType.suspend,
                suspend_type="manual",
                reason=data.reason,
                operator_id=operator_id
            )

            success_cards.append(card.iccid)

        return SuspendResult(
            success_count=len(success_cards),
            fail_count=len(fail_cards),
            success_cards=success_cards,
            fail_cards=fail_cards
        )

    @staticmethod
    async def manual_resume(
        db: AsyncSession,
        data: ManualResume,
        operator_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> SuspendResult:
        """手动复机"""
        success_cards = []
        fail_cards = []

        # 获取卡片
        cards = await CardSuspendCRUD.get_cards_by_ids(
            db, data.card_ids,
            user_id=None if is_admin else user_id
        )
        card_map = {c.id: c for c in cards}

        # 预加载供应商信息（避免N+1查询）
        supplier_ids = {c.supplier_id for c in cards if c.supplier_id}
        supplier_query = select(SupplierModel).where(
            SupplierModel.id.in_(supplier_ids),
            SupplierModel.is_deleted == 0
        )
        supplier_result = await db.execute(supplier_query)
        supplier_map = {s.id: s for s in supplier_result.scalars().all()}

        for card_id in data.card_ids:
            card = card_map.get(card_id)
            
            if not card:
                fail_cards.append({"card_id": card_id, "iccid": "未知", "reason": "卡片不存在或无权限"})
                continue

            if card.status != CardStatus.suspended:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": "卡片未处于停机状态"})
                continue

            # 检查是否可以复机
            if card.suspend_type == SuspendType.expired:
                # 到期停卡需要续费才能复机
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": "到期停卡，请先续费"})
                continue

            # 调用供应商API复机
            api_success = False
            supplier = supplier_map.get(card.supplier_id)
            if supplier:
                try:
                    supplier_client = get_supplier_client(
                        supplier_id=card.supplier_id,
                        api_url=supplier.api_url or "",
                        api_key=supplier.api_key or "",
                        api_secret=supplier.api_secret or ""
                    )
                    api_success = await supplier_client.resume_card(card.iccid)
                except Exception as e:
                    logger.error(f"供应商API复机失败: iccid={card.iccid}, error={e}")

            # 只有API成功才更新数据库
            if not api_success:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": "供应商API调用失败"})
                continue

            # 执行复机
            old_suspend_type = card.suspend_type.value if card.suspend_type else "manual"
            await CardSuspendCRUD.resume_card(db=db, card_id=card_id)

            # 记录日志
            await SuspendLogCRUD.create(
                db=db,
                card_id=card_id,
                iccid=card.iccid,
                action=SuspendActionType.resume,
                suspend_type=old_suspend_type,
                reason=data.reason,
                operator_id=operator_id
            )

            success_cards.append(card.iccid)

        return SuspendResult(
            success_count=len(success_cards),
            fail_count=len(fail_cards),
            success_cards=success_cards,
            fail_cards=fail_cards
        )

    @staticmethod
    async def auto_suspend_expired(db: AsyncSession) -> Dict[str, Any]:
        """自动停卡：到期停卡"""
        cards = await CardSuspendCRUD.get_expired_cards(db)
        suspended_count = 0

        for card in cards:
            # 检查是否有生效的策略
            policies = await SuspendPolicyCRUD.get_active_policies(
                db, "expired", user_id=card.user_id
            )
            
            policy = policies[0] if policies else None
            if policy and policy.auto_suspend != 1:
                continue

            # 执行停卡
            await CardSuspendCRUD.suspend_card(
                db=db,
                card_id=card.id,
                suspend_type=SuspendType.expired,
                reason="套餐到期自动停卡"
            )

            # 记录日志
            await SuspendLogCRUD.create(
                db=db,
                card_id=card.id,
                iccid=card.iccid,
                action=SuspendActionType.suspend,
                suspend_type="expired",
                policy_id=policy.id if policy else None,
                reason="套餐到期自动停卡"
            )

            suspended_count += 1

        return {"suspended_count": suspended_count}

    @staticmethod
    async def auto_suspend_card_exceed(db: AsyncSession) -> Dict[str, Any]:
        """自动停卡：单卡超量"""
        suspended_count = 0
        alerts_created = 0

        # 获取所有启用的单卡超量策略
        policies, _ = await SuspendPolicyCRUD.get_list(
            db, policy_type="card_exceed", is_enabled=True, page_size=1000
        )

        if not policies:
            return {"suspended_count": 0, "alerts_created": 0}

        # 获取激活状态的非池卡
        from sqlalchemy import select
        from app.db.models.iot_card import IotCardModel, CardStatus
        
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.is_deleted == 0,
                IotCardModel.status == CardStatus.activated,
                IotCardModel.is_pool_member == 0,
                IotCardModel.data_total > 0
            )
        )
        cards = result.scalars().all()

        for card in cards:
            usage_percent = card.get_data_usage_percent()
            
            # 找到适用的策略
            policy = None
            for p in policies:
                if p.user_id is None or p.user_id == card.user_id:
                    policy = p
                    break
            
            if not policy:
                continue

            # 检查告警阈值
            if usage_percent >= policy.warning_threshold and usage_percent < policy.critical_threshold:
                # 警告级别
                exists = await AlertLogCRUD.check_exists(
                    db, AlertTargetType.card, card.id, AlertLevel.warning
                )
                if not exists:
                    await AlertLogCRUD.create(
                        db=db,
                        target_type=AlertTargetType.card,
                        target_id=card.id,
                        target_name=card.iccid,
                        alert_level=AlertLevel.warning,
                        usage_percent=int(usage_percent),
                        threshold=policy.warning_threshold,
                        policy_id=policy.id,
                        user_id=card.user_id
                    )
                    alerts_created += 1

            elif usage_percent >= policy.critical_threshold and usage_percent < policy.stop_threshold:
                # 紧急级别
                exists = await AlertLogCRUD.check_exists(
                    db, AlertTargetType.card, card.id, AlertLevel.critical
                )
                if not exists:
                    await AlertLogCRUD.create(
                        db=db,
                        target_type=AlertTargetType.card,
                        target_id=card.id,
                        target_name=card.iccid,
                        alert_level=AlertLevel.critical,
                        usage_percent=int(usage_percent),
                        threshold=policy.critical_threshold,
                        policy_id=policy.id,
                        user_id=card.user_id
                    )
                    alerts_created += 1

            elif usage_percent >= policy.stop_threshold:
                # 超限 - 执行停卡
                if policy.auto_suspend == 1:
                    await CardSuspendCRUD.suspend_card(
                        db=db,
                        card_id=card.id,
                        suspend_type=SuspendType.card_exceed,
                        reason=f"单卡流量超限({usage_percent}%)"
                    )

                    await SuspendLogCRUD.create(
                        db=db,
                        card_id=card.id,
                        iccid=card.iccid,
                        action=SuspendActionType.suspend,
                        suspend_type="card_exceed",
                        policy_id=policy.id,
                        reason=f"单卡流量超限自动停卡({usage_percent}%)"
                    )
                    suspended_count += 1

                # 记录超限告警
                exists = await AlertLogCRUD.check_exists(
                    db, AlertTargetType.card, card.id, AlertLevel.exceed
                )
                if not exists:
                    await AlertLogCRUD.create(
                        db=db,
                        target_type=AlertTargetType.card,
                        target_id=card.id,
                        target_name=card.iccid,
                        alert_level=AlertLevel.exceed,
                        usage_percent=int(usage_percent),
                        threshold=policy.stop_threshold,
                        policy_id=policy.id,
                        user_id=card.user_id
                    )
                    alerts_created += 1

        return {"suspended_count": suspended_count, "alerts_created": alerts_created}


class SuspendLogService:
    """停卡记录服务"""

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        card_id: Optional[int] = None,
        action: Optional[str] = None,
        suspend_type: Optional[str] = None,
        pool_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取停卡记录列表"""
        logs, total = await SuspendLogCRUD.get_list(
            db=db,
            card_id=card_id,
            action=action,
            suspend_type=suspend_type,
            pool_id=pool_id,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        return [log.to_dict() for log in logs], total


class AlertLogService:
    """告警记录服务"""

    @staticmethod
    async def get_alerts(
        db: AsyncSession,
        target_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        user_id: Optional[int] = None,
        handled: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取告警记录列表"""
        alerts, total = await AlertLogCRUD.get_list(
            db=db,
            target_type=target_type,
            alert_level=alert_level,
            user_id=user_id,
            handled=handled,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        return [a.to_dict() for a in alerts], total

    @staticmethod
    async def handle_alert(
        db: AsyncSession,
        alert_id: int,
        handled_by: int,
        handle_remark: Optional[str] = None
    ) -> Optional[dict]:
        """处理告警"""
        alert = await AlertLogCRUD.handle_alert(
            db=db,
            alert_id=alert_id,
            handled_by=handled_by,
            handle_remark=handle_remark
        )
        return alert.to_dict() if alert else None

    @staticmethod
    async def get_unhandled_count(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> Dict[str, int]:
        """获取未处理告警统计"""
        from sqlalchemy import select
        from sqlalchemy.sql import func
        
        query = select(
            AlertLogModel.alert_level,
            func.count(AlertLogModel.id).label('count')
        ).where(
            AlertLogModel.is_deleted == 0,
            AlertLogModel.handled == 0
        )
        
        if user_id:
            query = query.where(AlertLogModel.user_id == user_id)
        
        query = query.group_by(AlertLogModel.alert_level)
        
        result = await db.execute(query)
        rows = result.all()
        
        stats = {"warning": 0, "critical": 0, "exceed": 0, "total": 0}
        for row in rows:
            level = row[0].value if row[0] else "unknown"
            count = row[1]
            if level in stats:
                stats[level] = count
            stats["total"] += count
        
        return stats
