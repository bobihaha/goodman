"""
物联网卡服务层
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.iot_card_crud import iot_card_crud, card_transfer_crud
from app.db.models.iot_card import IotCardModel
from app.db.models.sys_user import UserLevel
from app.utils.exceptions import BusinessException


class IotCardService:
    """物联网卡服务"""

    async def get_cards(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        carrier: Optional[str] = None,
        period_type: Optional[str] = None,
        pool_id: Optional[int] = None,
        is_pool_member: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取卡片列表 (根据用户权限过滤)"""
        # 超级管理员可以看全部，用户/子用户只能看自己的
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id

        items, total = await iot_card_crud.get_list(
            db=db,
            user_id=user_filter,
            keyword=keyword,
            status=status,
            carrier=carrier,
            period_type=period_type,
            pool_id=pool_id,
            is_pool_member=is_pool_member,
            page=page,
            page_size=page_size
        )

        return [item.to_dict() for item in items], total

    async def get_card_detail(
        self,
        db: AsyncSession,
        card_id: int,
        current_user_id: int,
        user_level: int
    ) -> Optional[dict]:
        """获取卡片详情"""
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        card = await iot_card_crud.get_by_id(db, card_id, user_filter)
        if not card:
            raise BusinessException(code=404, message="卡片不存在或无权访问")
        return card.to_dict()

    async def search_cards(
        self,
        db: AsyncSession,
        keyword: str,
        current_user_id: int,
        user_level: int,
        limit: int = 10
    ) -> List[dict]:
        """快速搜索卡片"""
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        items = await iot_card_crud.search(db, keyword, user_filter, limit)
        return [item.to_dict() for item in items]

    async def get_stats(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """获取卡片统计"""
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        return await iot_card_crud.get_stats(db, user_filter)

    async def update_remark(
        self,
        db: AsyncSession,
        card_id: int,
        remark: str,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """更新卡片备注"""
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        card = await iot_card_crud.update_remark(db, card_id, remark, user_filter)
        if not card:
            raise BusinessException(code=404, message="卡片不存在或无权操作")
        return card.to_dict()

    async def batch_update_remark(
        self,
        db: AsyncSession,
        card_ids: List[int],
        remark: str,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """批量更新备注"""
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        count = await iot_card_crud.batch_update_remark(db, card_ids, remark, user_filter)
        return {
            "success": count,
            "total": len(card_ids),
            "failed": len(card_ids) - count
        }

    async def transfer_card(
        self,
        db: AsyncSession,
        card_id: int,
        to_user_id: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """划拨卡片给子用户"""
        # 用户只能划拨自己的卡给子用户
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, message="子用户无权划拨卡片")

        from_user_id = current_user_id
        if user_level == UserLevel.SUPER_ADMIN.value:
            # 超级管理员可以操作任意卡片，需要先获取卡片当前归属
            card = await iot_card_crud.get_by_id(db, card_id, None)
            if not card:
                raise BusinessException(code=404, message="卡片不存在")
            from_user_id = card.user_id

        card = await iot_card_crud.transfer(
            db=db,
            card_id=card_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            operator_id=current_user_id,
            remark=remark
        )

        if not card:
            raise BusinessException(code=404, message="卡片不存在或无权操作")

        return card.to_dict()

    async def batch_transfer(
        self,
        db: AsyncSession,
        card_ids: List[int],
        to_user_id: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """批量划拨"""
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, message="子用户无权划拨卡片")

        from_user_id = current_user_id

        success, failed = await iot_card_crud.batch_transfer(
            db=db,
            card_ids=card_ids,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            operator_id=current_user_id,
            remark=remark
        )

        return {
            "success": success,
            "failed": failed,
            "total": len(card_ids)
        }

    async def export_cards(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int,
        card_ids: Optional[List[int]] = None,
        status: Optional[str] = None,
        carrier: Optional[str] = None
    ) -> List[dict]:
        """导出卡片数据"""
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id

        if card_ids:
            # 导出指定卡片
            items = await iot_card_crud.get_by_ids(db, card_ids, user_filter)
        else:
            # 导出全部 (根据筛选条件)
            items, _ = await iot_card_crud.get_list(
                db=db,
                user_id=user_filter,
                status=status,
                carrier=carrier,
                page=1,
                page_size=10000  # 最多导出1万条
            )

        # 转换为导出格式
        export_data = []
        for item in items:
            d = item.to_dict()
            export_data.append({
                "ICCID": d["iccid"],
                "IMSI": d["imsi"] or "",
                "号码": d["msisdn"] or "",
                "运营商": d["carrier_name"] or "",
                "套餐规格": d["spec_name"] or "",
                "状态": d["status_name"] or "",
                "已用流量(MB)": d["data_used"],
                "总流量(MB)": d["data_total"],
                "剩余流量(MB)": d["data_remain"],
                "使用率(%)": d["data_usage_percent"],
                "激活日期": d["activated_at"] or "",
                "到期日期": d["expired_at"] or "",
                "备注": d["remark"] or ""
            })

        return export_data

    async def get_card_transfers(
        self,
        db: AsyncSession,
        card_id: int,
        current_user_id: int,
        user_level: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取卡片划拨记录"""
        # 先验证卡片访问权限
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        card = await iot_card_crud.get_by_id(db, card_id, user_filter)
        if not card:
            raise BusinessException(code=404, message="卡片不存在或无权访问")

        items, total = await card_transfer_crud.get_list(
            db=db, card_id=card_id, page=page, page_size=page_size
        )
        return [item.to_dict() for item in items], total


iot_card_service = IotCardService()
