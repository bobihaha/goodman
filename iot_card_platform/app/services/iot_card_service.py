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
        flow_size: Optional[int] = None,
        period_type: Optional[str] = None,
        card_type: Optional[str] = None,
        pool_id: Optional[int] = None,
        is_pool_member: Optional[bool] = None,
        over_usage: Optional[bool] = None,
        remark: Optional[str] = None,
        customer_id: Optional[int] = None,
        batch_id: Optional[int] = None,
        project_id: Optional[int] = None,
        stock_out_start: Optional[str] = None,
        stock_out_end: Optional[str] = None,
        activated_start: Optional[str] = None,
        activated_end: Optional[str] = None,
        expired_start: Optional[str] = None,
        expired_end: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取卡片列表 (根据用户权限过滤)"""
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id

        items, total = await iot_card_crud.get_list(
            db=db,
            user_id=user_filter,
            keyword=keyword,
            status=status,
            carrier=carrier,
            flow_size=flow_size,
            period_type=period_type,
            card_type=card_type,
            pool_id=pool_id,
            is_pool_member=is_pool_member,
            over_usage=over_usage,
            remark=remark,
            customer_id=customer_id,
            batch_id=batch_id,
            project_id=project_id,
            stock_out_start=stock_out_start,
            stock_out_end=stock_out_end,
            activated_start=activated_start,
            activated_end=activated_end,
            expired_start=expired_start,
            expired_end=expired_end,
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
            raise BusinessException(code=404, msg="卡片不存在或无权访问")
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
        from app.utils.const import sanitize_text
        remark = sanitize_text(remark)
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        card = await iot_card_crud.update_remark(db, card_id, remark, user_filter)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权操作")
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
        if len(card_ids) > settings.max_batch_operation_size:
            raise BusinessException(code=400, msg=f"单次最多操作{settings.max_batch_operation_size}张卡片")

        from app.utils.const import sanitize_text
        remark = sanitize_text(remark)
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
        from sqlalchemy import select
        from app.db.models.sys_user import SysUserModel

        # 用户只能划拨自己的卡给子用户
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权划拨卡片")

        # 验证目标用户存在
        target_user_result = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
        target_user = target_user_result.scalar_one_or_none()
        if not target_user:
            raise BusinessException(code=422, msg="目标用户不存在")

        # 验证目标用户状态
        from app.db.models.sys_user import UserStatus
        if target_user.status != UserStatus.enable:
            raise BusinessException(code=422, msg="目标用户已被禁用")

        # 验证目标用户是当前用户的子用户
        if user_level != UserLevel.SUPER_ADMIN.value and target_user.parent_id != current_user_id:
            raise BusinessException(code=422, msg="只能划拨给直属子用户")

        from_user_id = current_user_id
        if user_level == UserLevel.SUPER_ADMIN.value:
            # 超级管理员可以操作任意卡片，需要先获取卡片当前归属
            card = await iot_card_crud.get_by_id(db, card_id, None)
            if not card:
                raise BusinessException(code=404, msg="卡片不存在")
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
            raise BusinessException(code=404, msg="卡片不存在或无权操作")

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
        if len(card_ids) > settings.max_batch_operation_size:
            raise BusinessException(code=400, msg=f"单次最多操作{settings.max_batch_operation_size}张卡片")

        from sqlalchemy import select
        from app.db.models.sys_user import SysUserModel

        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权划拨卡片")

        # 验证目标用户存在
        target_user_result = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
        target_user = target_user_result.scalar_one_or_none()
        if not target_user:
            raise BusinessException(code=422, msg="目标用户不存在")

        # 验证目标用户状态
        from app.db.models.sys_user import UserStatus
        if target_user.status != UserStatus.enable:
            raise BusinessException(code=422, msg="目标用户已被禁用")

        # 验证目标用户是当前用户的子用户
        if user_level != UserLevel.SUPER_ADMIN.value and target_user.parent_id != current_user_id:
            raise BusinessException(code=422, msg="只能划拨给直属子用户")

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
                page_size=settings.max_export_size
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
            raise BusinessException(code=404, msg="卡片不存在或无权访问")

        items, total = await card_transfer_crud.get_list(
            db=db, card_id=card_id, page=page, page_size=page_size
        )
        return [item.to_dict() for item in items], total

    async def query_renew_price(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """批量查询续费价格"""
        from sqlalchemy import select

        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id

        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )

        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)

        result = await db.execute(query)
        cards = result.scalars().all()

        found_iccids = set()
        found_list = []
        for card in cards:
            found_iccids.add(card.iccid)
            card_dict = card.to_dict()
            # 使用卡片记录的单价，如果为空则查询套餐价格作为兜底
            if card.sale_price:
                card_dict["price_sale"] = float(card.sale_price)
            elif card.sale_package_id:
                from app.db.models.package import SalePackageModel
                pkg_query = select(SalePackageModel.price_sale).where(SalePackageModel.id == card.sale_package_id)
                pkg_result = await db.execute(pkg_query)
                price = pkg_result.scalar_one_or_none()
                card_dict["price_sale"] = float(price) if price else None
            else:
                card_dict["price_sale"] = None
            found_list.append(card_dict)

        not_found = [iccid for iccid in iccids if iccid not in found_iccids]

        return {
            "found": found_list,
            "not_found": not_found
        }

    async def batch_query_cards(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """批量查询卡片"""
        from sqlalchemy import select
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        found_cards = list(result.scalars().all())
        
        # 找到的ICCID
        found_iccids = {card.iccid for card in found_cards}
        
        # 未找到的ICCID
        not_found = [iccid for iccid in iccids if iccid not in found_iccids]
        
        return {
            "found": [card.to_dict() for card in found_cards],
            "not_found": not_found
        }

    async def batch_transfer_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        to_user_id: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """通过ICCID批量划拨"""
        from sqlalchemy import select, update
        from app.db.models.sys_user import SysUserModel
        
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权划拨卡片")
        
        # 验证目标用户存在
        target_user = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
        if not target_user.scalar_one_or_none():
            raise BusinessException(code=404, msg="目标用户不存在")
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                # 更新卡片归属
                old_user_id = card.user_id
                card.user_id = to_user_id
                
                # 记录划拨日志
                from app.db.models.iot_card import CardTransferModel
                transfer_log = CardTransferModel(
                    card_id=card.id,
                    iccid=card.iccid,
                    from_user_id=old_user_id,
                    to_user_id=to_user_id,
                    operator_id=current_user_id,
                    remark=remark
                )
                db.add(transfer_log)
                
                # 获取目标用户名称
                target_user_obj = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
                target_user_name = target_user_obj.scalar_one().name
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "to_user_name": target_user_name,
                    "message": "划拨成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_remark_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        remark: str,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量备注"""
        from sqlalchemy import select
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.remark = remark
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "remark": remark
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_renew_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        renew_months: int,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量续费"""
        from sqlalchemy import select
        from datetime import datetime, timedelta, date
        from app.crud.package_crud import sale_package_crud
        from app.utils.date_utils import calculate_expiry_date
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                # 续费逻辑：延长到期日期
                package = await sale_package_crud.get_by_id(db, card.sale_package_id) if card.sale_package_id else None
                if package:
                    base_date = card.expired_at if card.expired_at else date.today()
                    card.expired_at = calculate_expiry_date(
                        base_date,
                        package.period_type.value,
                        package.period_months,
                        package.period_days
                    )
                else:
                    # 兼容旧逻辑：无套餐信息时按30天/月计算
                    if card.expired_at:
                        card.expired_at = card.expired_at + timedelta(days=renew_months * 30)
                    else:
                        card.expired_at = date.today() + timedelta(days=renew_months * 30)
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": f"续费{renew_months}个月成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_suspend_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        reason: Optional[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量停机"""
        from sqlalchemy import select
        from datetime import datetime
        from app.db.models.iot_card import CardStatus, SuspendType
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.status = CardStatus.suspended
                card.suspend_type = SuspendType.manual
                card.suspend_at = datetime.now()
                card.suspend_reason = reason or "手动停机"
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": "停机成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_resume_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量复机"""
        from sqlalchemy import select
        from app.db.models.iot_card import CardStatus, SuspendType
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.status = CardStatus.activated
                card.suspend_type = SuspendType.none
                card.suspend_at = None
                card.suspend_reason = None
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": "复机成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_query_cards(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """批量查询卡片"""
        from sqlalchemy import select
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        found_cards = list(result.scalars().all())
        
        # 找到的ICCID
        found_iccids = {card.iccid for card in found_cards}
        
        # 未找到的ICCID
        not_found = [iccid for iccid in iccids if iccid not in found_iccids]
        
        return {
            "found": [card.to_dict() for card in found_cards],
            "not_found": not_found
        }

    async def batch_transfer_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        to_user_id: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """通过ICCID批量划拨"""
        from sqlalchemy import select, update
        from app.db.models.sys_user import SysUserModel
        
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权划拨卡片")
        
        # 验证目标用户存在
        target_user = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
        if not target_user.scalar_one_or_none():
            raise BusinessException(code=404, msg="目标用户不存在")
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                # 更新卡片归属
                old_user_id = card.user_id
                card.user_id = to_user_id
                
                # 记录划拨日志
                from app.db.models.iot_card import CardTransferModel
                transfer_log = CardTransferModel(
                    card_id=card.id,
                    iccid=card.iccid,
                    from_user_id=old_user_id,
                    to_user_id=to_user_id,
                    operator_id=current_user_id,
                    remark=remark
                )
                db.add(transfer_log)
                
                # 获取目标用户名称
                target_user_obj = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
                target_user_name = target_user_obj.scalar_one().name
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "to_user_name": target_user_name,
                    "message": "划拨成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_remark_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        remark: str,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量备注"""
        from sqlalchemy import select
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.remark = remark
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "remark": remark
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_renew_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        renew_months: int,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量续费"""
        from sqlalchemy import select
        from datetime import datetime, timedelta, date
        from app.crud.package_crud import sale_package_crud
        from app.utils.date_utils import calculate_expiry_date
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                # 续费逻辑：延长到期日期
                package = await sale_package_crud.get_by_id(db, card.sale_package_id) if card.sale_package_id else None
                if package:
                    base_date = card.expired_at if card.expired_at else date.today()
                    card.expired_at = calculate_expiry_date(
                        base_date,
                        package.period_type.value,
                        package.period_months,
                        package.period_days
                    )
                else:
                    # 兼容旧逻辑：无套餐信息时按30天/月计算
                    if card.expired_at:
                        card.expired_at = card.expired_at + timedelta(days=renew_months * 30)
                    else:
                        card.expired_at = date.today() + timedelta(days=renew_months * 30)
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": f"续费{renew_months}个月成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_suspend_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        reason: Optional[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量停机"""
        from sqlalchemy import select
        from datetime import datetime
        from app.db.models.iot_card import CardStatus, SuspendType
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.status = CardStatus.suspended
                card.suspend_type = SuspendType.manual
                card.suspend_at = datetime.now()
                card.suspend_reason = reason or "手动停机"
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": "停机成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_resume_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量复机"""
        from sqlalchemy import select
        from app.db.models.iot_card import CardStatus, SuspendType
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.status = CardStatus.activated
                card.suspend_type = SuspendType.none
                card.suspend_at = None
                card.suspend_reason = None
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": "复机成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_query_cards(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """批量查询卡片"""
        from sqlalchemy import select
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        found_cards = list(result.scalars().all())
        
        # 找到的ICCID
        found_iccids = {card.iccid for card in found_cards}
        
        # 未找到的ICCID
        not_found = [iccid for iccid in iccids if iccid not in found_iccids]
        
        return {
            "found": [card.to_dict() for card in found_cards],
            "not_found": not_found
        }

    async def batch_transfer_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        to_user_id: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """通过ICCID批量划拨"""
        from sqlalchemy import select, update
        from app.db.models.sys_user import SysUserModel
        
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权划拨卡片")
        
        # 验证目标用户存在
        target_user = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
        if not target_user.scalar_one_or_none():
            raise BusinessException(code=404, msg="目标用户不存在")
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                # 更新卡片归属
                old_user_id = card.user_id
                card.user_id = to_user_id
                
                # 记录划拨日志
                from app.db.models.iot_card import CardTransferModel
                transfer_log = CardTransferModel(
                    card_id=card.id,
                    iccid=card.iccid,
                    from_user_id=old_user_id,
                    to_user_id=to_user_id,
                    operator_id=current_user_id,
                    remark=remark
                )
                db.add(transfer_log)
                
                # 获取目标用户名称
                target_user_obj = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
                target_user_name = target_user_obj.scalar_one().name
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "to_user_name": target_user_name,
                    "message": "划拨成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_remark_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        remark: str,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量备注"""
        from sqlalchemy import select
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.remark = remark
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "remark": remark
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_renew_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        renew_months: int,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量续费"""
        from sqlalchemy import select
        from datetime import datetime, timedelta, date
        from app.crud.package_crud import sale_package_crud
        from app.utils.date_utils import calculate_expiry_date
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                # 续费逻辑：延长到期日期
                package = await sale_package_crud.get_by_id(db, card.sale_package_id) if card.sale_package_id else None
                if package:
                    base_date = card.expired_at if card.expired_at else date.today()
                    card.expired_at = calculate_expiry_date(
                        base_date,
                        package.period_type.value,
                        package.period_months,
                        package.period_days
                    )
                else:
                    # 兼容旧逻辑：无套餐信息时按30天/月计算
                    if card.expired_at:
                        card.expired_at = card.expired_at + timedelta(days=renew_months * 30)
                    else:
                        card.expired_at = date.today() + timedelta(days=renew_months * 30)
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": f"续费{renew_months}个月成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_suspend_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        reason: Optional[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量停机"""
        from sqlalchemy import select
        from datetime import datetime
        from app.db.models.iot_card import CardStatus, SuspendType
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.status = CardStatus.suspended
                card.suspend_type = SuspendType.manual
                card.suspend_at = datetime.now()
                card.suspend_reason = reason or "手动停机"
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": "停机成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_resume_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量复机"""
        from sqlalchemy import select
        from app.db.models.iot_card import CardStatus, SuspendType
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.status = CardStatus.activated
                card.suspend_type = SuspendType.none
                card.suspend_at = None
                card.suspend_reason = None
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": "复机成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_query_cards(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """批量查询卡片"""
        from sqlalchemy import select
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        found_cards = list(result.scalars().all())
        
        # 找到的ICCID
        found_iccids = {card.iccid for card in found_cards}
        
        # 未找到的ICCID
        not_found = [iccid for iccid in iccids if iccid not in found_iccids]
        
        return {
            "found": [card.to_dict() for card in found_cards],
            "not_found": not_found
        }

    async def batch_transfer_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        to_user_id: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """通过ICCID批量划拨"""
        from sqlalchemy import select, update
        from app.db.models.sys_user import SysUserModel
        
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权划拨卡片")
        
        # 验证目标用户存在
        target_user = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
        if not target_user.scalar_one_or_none():
            raise BusinessException(code=404, msg="目标用户不存在")
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                # 更新卡片归属
                old_user_id = card.user_id
                card.user_id = to_user_id
                
                # 记录划拨日志
                from app.db.models.iot_card import CardTransferModel
                transfer_log = CardTransferModel(
                    card_id=card.id,
                    iccid=card.iccid,
                    from_user_id=old_user_id,
                    to_user_id=to_user_id,
                    operator_id=current_user_id,
                    remark=remark
                )
                db.add(transfer_log)
                
                # 获取目标用户名称
                target_user_obj = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
                target_user_name = target_user_obj.scalar_one().name
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "to_user_name": target_user_name,
                    "message": "划拨成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_remark_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        remark: str,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量备注"""
        from sqlalchemy import select
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.remark = remark
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "remark": remark
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_renew_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        renew_months: int,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量续费"""
        from sqlalchemy import select
        from datetime import datetime, timedelta, date
        from app.crud.package_crud import sale_package_crud
        from app.utils.date_utils import calculate_expiry_date
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                # 续费逻辑：延长到期日期
                package = await sale_package_crud.get_by_id(db, card.sale_package_id) if card.sale_package_id else None
                if package:
                    base_date = card.expired_at if card.expired_at else date.today()
                    card.expired_at = calculate_expiry_date(
                        base_date,
                        package.period_type.value,
                        package.period_months,
                        package.period_days
                    )
                else:
                    # 兼容旧逻辑：无套餐信息时按30天/月计算
                    if card.expired_at:
                        card.expired_at = card.expired_at + timedelta(days=renew_months * 30)
                    else:
                        card.expired_at = date.today() + timedelta(days=renew_months * 30)
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": f"续费{renew_months}个月成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_suspend_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        reason: Optional[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量停机"""
        from sqlalchemy import select
        from datetime import datetime
        from app.db.models.iot_card import CardStatus, SuspendType
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.status = CardStatus.suspended
                card.suspend_type = SuspendType.manual
                card.suspend_at = datetime.now()
                card.suspend_reason = reason or "手动停机"
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": "停机成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_resume_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量复机"""
        from sqlalchemy import select
        from app.db.models.iot_card import CardStatus, SuspendType
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        
        success_list = []
        failed_list = []
        
        for iccid in iccids:
            card = next((c for c in cards if c.iccid == iccid), None)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                card.status = CardStatus.activated
                card.suspend_type = SuspendType.none
                card.suspend_at = None
                card.suspend_reason = None
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "message": "复机成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def get_card_usage_history(
        self,
        db: AsyncSession,
        card_id: int,
        current_user_id: int,
        user_level: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """获取卡片用量历史"""
        from app.crud.iot_card_crud import card_usage_history_crud
        from datetime import datetime

        card = await iot_card_crud.get_by_id(db, card_id)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在")

        if user_level != UserLevel.SUPER_ADMIN.value:
            if card.user_id != current_user_id:
                raise BusinessException(code=403, msg="无权查看此卡片历史")

        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        history = await card_usage_history_crud.get_card_history(db, card_id, start, end)
        return [h.to_dict() for h in history]

    async def export_cards_with_history(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int,
        card_ids: List[int],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """导出卡片历史用量"""
        from app.crud.iot_card_crud import card_usage_history_crud
        from datetime import datetime

        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        cards = await iot_card_crud.get_by_ids(db, card_ids, user_filter)
        if not cards:
            return []

        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        card_ids_list = [c.id for c in cards]
        history_records = await card_usage_history_crud.get_cards_history(db, card_ids_list, start, end)

        history_map = {}
        for h in history_records:
            if h.card_id not in history_map:
                history_map[h.card_id] = []
            history_map[h.card_id].append(h)

        export_data = []
        for card in cards:
            d = card.to_dict()
            histories = history_map.get(card.id, [])

            if histories:
                for h in histories:
                    export_data.append({
                        "ICCID": d["iccid"],
                        "运营商": d["carrier_name"],
                        "套餐规格": d["spec_name"],
                        "快照日期": h.snapshot_date.strftime("%Y-%m-%d"),
                        "快照类型": "月末" if h.snapshot_type == "month_end" else "周期末",
                        "快照月份": h.snapshot_month or "",
                        "已用流量(MB)": h.data_used,
                        "总流量(MB)": h.data_total,
                        "使用率(%)": round((h.data_used / h.data_total * 100), 2) if h.data_total else 0,
                    })
            else:
                export_data.append({
                    "ICCID": d["iccid"],
                    "运营商": d["carrier_name"],
                    "套餐规格": d["spec_name"],
                    "快照日期": "当前",
                    "快照类型": "",
                    "快照月份": "",
                    "已用流量(MB)": d["data_used"],
                    "总流量(MB)": d["data_total"],
                    "使用率(%)": d["data_usage_percent"],
                })

        return export_data


iot_card_service = IotCardService()
