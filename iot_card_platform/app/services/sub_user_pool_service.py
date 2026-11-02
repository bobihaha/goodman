"""子账号流量池只读投影；不修改共享池统计或扩大写权限。"""
from datetime import datetime

from sqlalchemy import and_, case, func, or_, select

from app.crud.pool_crud import AUTO_POOL_REMARK, valid_pool_member_conditions, pool_flow_contributor_condition
from app.db.models.iot_card import IotCardModel, CardStatus
from app.db.models.pool import TrafficPoolModel
from app.db.models.sys_user import SysUserModel
from app.flow_packages import get_current_flow_cycle_month, is_flow_cycle_active
from app.utils.exceptions import BusinessException


class SubUserPoolService:
    async def get_pools(self, db, user_id, *, pool_id=None, name=None,
                        customer_name=None, carrier=None, status=None, is_alert=None):
        month = get_current_flow_cycle_month()
        contributes = pool_flow_contributor_condition()
        usage_contributes = and_(
            contributes,
            or_(
                TrafficPoolModel.period_type != "monthly",
                and_(IotCardModel.data_usage_month == month,
                     IotCardModel.data_source_at >= datetime.strptime(f"{month}-01", "%Y-%m-%d")),
            ),
        )
        query = select(
            TrafficPoolModel, SysUserModel.name,
            func.count(IotCardModel.id),
            func.coalesce(func.sum(case((contributes, IotCardModel.data_total), else_=0)), 0),
            func.coalesce(func.sum(case((usage_contributes, IotCardModel.data_used), else_=0)), 0),
            func.max(IotCardModel.data_sync_at),
            *[func.sum(case((IotCardModel.status == state, 1), else_=0)) for state in CardStatus],
        ).outerjoin(IotCardModel, and_(
            *valid_pool_member_conditions(TrafficPoolModel.id),
            IotCardModel.user_id == user_id,
        )).outerjoin(SysUserModel, and_(
            SysUserModel.id == TrafficPoolModel.user_id, SysUserModel.is_deleted == 0,
        )).where(TrafficPoolModel.is_deleted == 0).group_by(
            TrafficPoolModel.id, SysUserModel.name,
        ).having(or_(TrafficPoolModel.user_id == user_id, func.count(IotCardModel.id) > 0))
        query = query.having(or_(
            TrafficPoolModel.remark.is_(None), TrafficPoolModel.remark != AUTO_POOL_REMARK,
            func.count(IotCardModel.id) > 0,
        ))
        if pool_id is not None:
            query = query.where(TrafficPoolModel.id == pool_id)
        if name:
            query = query.where(TrafficPoolModel.name.contains(name))
        if customer_name and customer_name.strip():
            query = query.where(SysUserModel.name.contains(customer_name.strip(), autoescape=True))
        if carrier:
            query = query.where(TrafficPoolModel.carrier == carrier)
        if status:
            query = query.where(TrafficPoolModel.status == status)
        rows = (await db.execute(query.order_by(TrafficPoolModel.id.desc()))).all()
        pools = []
        for source, owner_name, count, total, used, sync_at, *counts in rows:
            addon_flow = int(source.addon_flow or 0) if (
                not source.addon_flow_month or is_flow_cycle_active(source.addon_flow_month)
            ) else 0
            # 独立瞬态模型复用序列化；绝不改动 session 中的真实池。
            pool = TrafficPoolModel(**{key: getattr(source, key) for key in (
                "id", "name", "carrier", "flow_size", "period_type", "user_id", "status",
                "alert_threshold_1", "alert_threshold_2", "alert_threshold_3",
            )}, card_count=count, data_total=int(total) + addon_flow, data_used=int(used),
                package_flow=int(total), addon_flow=addon_flow,
                addon_flow_month=source.addon_flow_month if addon_flow else None, last_sync_at=sync_at)
            if is_alert is not None and pool.is_alert() != is_alert:
                continue
            data = pool.to_dict(include_card_stats=True, card_stats={
                state.value: int(value or 0) for state, value in zip(CardStatus, counts)
            })
            data.update(user_name=owner_name, sale_package_name=None,
                        can_self_topup=False, read_only=True, statistics_scope="assigned_cards")
            pools.append(data)
        return pools

    async def get_pool(self, db, user_id, pool_id):
        pools = await self.get_pools(db, user_id, pool_id=pool_id)
        if not pools:
            raise BusinessException(code=404, msg="流量池不存在或无权访问")
        return pools[0]

    async def get_stats(self, db, user_id):
        pools = await self.get_pools(db, user_id)
        return {
            "total": len(pools),
            "enabled": sum(p["status"] == "enable" for p in pools),
            "disabled": sum(p["status"] == "disable" for p in pools),
            "alert_count": sum(p["is_alert"] for p in pools),
            "total_cards": sum(p["card_count"] for p in pools),
            "total_flow": sum(p["data_total"] for p in pools),
            "used_flow": sum(p["data_used"] for p in pools),
            "by_carrier": {c: sum(p["carrier"] == c for p in pools) for c in ("cmcc", "cucc", "ctcc")},
        }


sub_user_pool_service = SubUserPoolService()
