"""
流量池管理服务层
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.pool_crud import pool_crud, pool_card_crud, pool_log_crud
from app.db.models.pool import TrafficPoolModel
from app.db.models.iot_card import IotCardModel
from app.utils.exceptions import BusinessException


class PoolService:
    """流量池服务"""

    async def create_pool(
        self,
        db: AsyncSession,
        name: str,
        carrier: str,
        flow_size: int,
        period_type: str,
        user_id: Optional[int] = None,
        alert_threshold: Optional[int] = None,
        stop_threshold: Optional[int] = None,
        created_by: Optional[int] = None,
        remark: Optional[str] = None
    ) -> dict:
        """创建流量池"""
        pool = await pool_crud.create(
            db=db,
            name=name,
            carrier=carrier,
            flow_size=flow_size,
            period_type=period_type,
            user_id=user_id,
            alert_threshold=alert_threshold,
            stop_threshold=stop_threshold,
            created_by=created_by,
            remark=remark
        )
        return pool.to_dict()

    async def get_pool(self, db: AsyncSession, pool_id: int) -> dict:
        """获取流量池详情"""
        pool = await pool_crud.get_by_id(db, pool_id)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在")
        return pool.to_dict()

    async def get_pools(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        carrier: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取流量池列表"""
        items, total = await pool_crud.get_list(
            db=db,
            user_id=user_id,
            carrier=carrier,
            status=status,
            page=page,
            page_size=page_size
        )
        return [item.to_dict() for item in items], total

    async def update_pool(
        self,
        db: AsyncSession,
        pool_id: int,
        **kwargs
    ) -> dict:
        """更新流量池"""
        pool = await pool_crud.update(db, pool_id, **kwargs)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在")
        return pool.to_dict()

    async def delete_pool(self, db: AsyncSession, pool_id: int) -> bool:
        """删除流量池"""
        # 检查池内是否还有卡片
        pool = await pool_crud.get_by_id(db, pool_id)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在")

        if pool.card_count > 0:
            raise BusinessException(code=400, msg=f"流量池内还有 {pool.card_count} 张卡片，请先移除")

        success = await pool_crud.delete(db, pool_id)
        return success

    async def add_cards(
        self,
        db: AsyncSession,
        pool_id: int,
        card_ids: List[int],
        operator_id: int,
        remark: Optional[str] = None
    ) -> dict:
        """添加卡片到流量池"""
        pool = await pool_crud.get_by_id(db, pool_id)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在")

        if pool.status.value != "enable":
            raise BusinessException(code=400, msg="流量池已停用")

        success, failed, fail_details = await pool_card_crud.add_cards(
            db=db,
            pool=pool,
            card_ids=card_ids,
            operator_id=operator_id,
            remark=remark
        )

        return {
            "total": len(card_ids),
            "success": success,
            "failed": failed,
            "fail_details": fail_details if fail_details else None
        }

    async def remove_cards(
        self,
        db: AsyncSession,
        pool_id: int,
        card_ids: List[int],
        operator_id: int,
        remark: Optional[str] = None
    ) -> dict:
        """从流量池移除卡片"""
        pool = await pool_crud.get_by_id(db, pool_id)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在")

        success, failed, fail_details = await pool_card_crud.remove_cards(
            db=db,
            pool=pool,
            card_ids=card_ids,
            operator_id=operator_id,
            remark=remark
        )

        return {
            "total": len(card_ids),
            "success": success,
            "failed": failed,
            "fail_details": fail_details if fail_details else None
        }

    async def get_pool_cards(
        self,
        db: AsyncSession,
        pool_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取流量池内卡片列表"""
        pool = await pool_crud.get_by_id(db, pool_id)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在")

        items, total = await pool_card_crud.get_pool_cards(
            db=db, pool_id=pool_id, page=page, page_size=page_size
        )
        return [item.to_dict() for item in items], total

    async def get_pool_stats(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> dict:
        """获取流量池总体统计"""
        stats = await pool_crud.get_stats(db, user_id)
        return stats

    async def get_pool_usage(self, db: AsyncSession, pool_id: int) -> dict:
        """获取流量池用量统计"""
        pool = await pool_crud.get_by_id(db, pool_id)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在")

        # 先更新统计数据
        pool = await pool_crud.update_stats(db, pool_id)

        # 获取池内卡片用量明细
        cards, _ = await pool_card_crud.get_pool_cards(db, pool_id, page=1, page_size=1000)
        card_usage = []
        for card in cards:
            card_usage.append({
                "card_id": card.id,
                "iccid": card.iccid,
                "data_used": card.data_used,
                "data_total": card.data_total,
                "usage_percent": card.get_data_usage_percent()
            })

        return {
            "pool_id": pool.id,
            "pool_name": pool.name,
            "spec_name": pool.get_spec_name(),
            "card_count": pool.card_count,
            "data_total": pool.data_total,
            "data_used": pool.data_used,
            "data_remain": pool.get_data_remain(),
            "usage_percent": pool.get_usage_percent(),
            "alert_threshold": pool.alert_threshold,
            "stop_threshold": pool.stop_threshold,
            "is_alert": pool.is_alert(),
            "is_exceed": pool.is_exceed(),
            "cards": card_usage
        }

    async def get_pool_logs(
        self,
        db: AsyncSession,
        pool_id: int,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取流量池操作日志"""
        pool = await pool_crud.get_by_id(db, pool_id)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在")

        items, total = await pool_log_crud.get_logs(
            db=db, pool_id=pool_id, action=action, page=page, page_size=page_size
        )
        return [item.to_dict() for item in items], total


pool_service = PoolService()
