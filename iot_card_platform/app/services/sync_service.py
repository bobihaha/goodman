"""
数据同步服务层
"""
from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
import asyncio
from app.crud.sync_crud import sync_log_crud, sync_task_crud
from app.db.models.sync import SyncType, SyncStatus
from app.db.models.iot_card import IotCardModel, CardStatus
from app.db.models.supplier import SupplierModel
from app.clients.supplier_api import get_supplier_client
from app.flow_packages import get_current_flow_cycle_month, is_flow_cycle_active
from app.utils.exceptions import BusinessException


class SyncService:
    """数据同步服务"""

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # 秒

    async def _record_usage_snapshot(self, db: AsyncSession, card, snapshot_type: str):
        """记录用量快照"""
        from app.crud.iot_card_crud import card_usage_history_crud
        import logging
        logger = logging.getLogger(__name__)
        try:
            snapshot_date = date.today()
            snapshot_month = None
            if card.period_type.value == "monthly":
                snapshot_month = snapshot_date.strftime("%Y-%m")
            await card_usage_history_crud.create_snapshot(
                db=db,
                card_id=card.id,
                iccid=card.iccid,
                data_used=card.data_used,
                data_total=card.data_total,
                period_type=card.period_type.value,
                snapshot_date=snapshot_date,
                snapshot_type=snapshot_type,
                snapshot_month=snapshot_month
            )
        except Exception as e:
            logger.error(f"记录用量快照失败 - ICCID: {card.iccid}", exc_info=True)


    async def _retry_api_call(self, func, *args, **kwargs):
        """API调用重试包装器"""
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
        raise last_error

    # ============ 流量用量同步 ============

    async def sync_usage(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        iccid_list: Optional[List[str]] = None,
        triggered_by: Optional[int] = None
    ) -> dict:
        """
        同步流量用量
        
        Args:
            supplier_id: 供应商ID (None=全部)
            iccid_list: 指定ICCID列表 (None=全部)
            triggered_by: 触发人ID
        """
        # 创建同步日志
        log = await sync_log_crud.create(
            db=db,
            sync_type=SyncType.usage,
            supplier_id=supplier_id,
            triggered_by=triggered_by,
            trigger_type="manual"
        )

        try:
            # 更新状态为执行中
            await sync_log_crud.update_status(db, log.id, SyncStatus.running)

            # 获取需要同步的卡片
            cards = await self._get_cards_for_sync(db, supplier_id, iccid_list)
            
            if not cards:
                await sync_log_crud.update_status(
                    db, log.id, SyncStatus.success,
                    total_count=0, success_count=0, fail_count=0
                )
                return {
                    "sync_no": log.sync_no,
                    "sync_type": "usage",
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "status": "success"
                }

            # 按供应商分组同步
            supplier_cards = {}
            for card in cards:
                if card.supplier_id not in supplier_cards:
                    supplier_cards[card.supplier_id] = []
                supplier_cards[card.supplier_id].append(card)

            total_count = len(cards)
            success_count = 0
            fail_count = 0
            sync_details = []

            for sup_id, sup_cards in supplier_cards.items():
                # 获取供应商信息
                supplier = await self._get_supplier(db, sup_id)
                if not supplier:
                    fail_count += len(sup_cards)
                    continue

                # 获取API客户端
                try:
                    client = get_supplier_client(
                        supplier_id=sup_id,
                        api_url=supplier.api_url or "",
                        api_key=supplier.api_key or "",
                        api_secret=supplier.api_secret or ""
                    )

                    # 批量获取流量数据（带重试）
                    iccids = [card.iccid for card in sup_cards]
                    usage_data = await self._retry_api_call(client.get_batch_usage, iccids)

                    # 更新卡片流量
                    usage_map = {item["iccid"]: item for item in usage_data}
                    for card in sup_cards:
                        if card.iccid in usage_map:
                            data = usage_map[card.iccid]
                            card.data_used = data.get("data_used", 0)
                            supplier_total = data.get("data_total")
                            if supplier_total is not None:
                                supplier_total = int(supplier_total)
                                if card.addon_flow and not card.addon_flow_month:
                                    card.addon_flow_month = get_current_flow_cycle_month()
                                effective_addon = int(card.addon_flow or 0) if is_flow_cycle_active(card.addon_flow_month) else 0
                                if not effective_addon and card.addon_flow:
                                    card.addon_flow = 0
                                    card.addon_flow_month = None
                                if card.period_type.value == "monthly" and card.flow_size:
                                    base_total = max(card.flow_size, supplier_total)
                                else:
                                    base_total = supplier_total
                                card.data_total = base_total + effective_addon
                            if card.period_type.value == "monthly":
                                card.data_used_month = card.data_used
                            card.data_sync_at = datetime.now()

                            # 检查并更新卡片状态
                            from app.services.card_status_service import check_and_update_card_status
                            await check_and_update_card_status(db, card)

                            # 每次同步都记录当日日快照，供详情页日用量图使用
                            await self._record_usage_snapshot(db, card, "daily")

                            # 月包：月末额外记录月末快照
                            if card.period_type.value == "monthly":
                                from datetime import date
                                import calendar
                                today = date.today()
                                last_day = calendar.monthrange(today.year, today.month)[1]
                                if today.day == last_day:
                                    await self._record_usage_snapshot(db, card, "month_end")

                            success_count += 1
                            sync_details.append({
                                "iccid": card.iccid,
                                "data_used": card.data_used,
                                "status": "success"
                            })
                        else:
                            fail_count += 1
                            sync_details.append({
                                "iccid": card.iccid,
                                "status": "failed",
                                "reason": "未返回数据"
                            })

                except Exception as e:
                    fail_count += len(sup_cards)
                    for card in sup_cards:
                        sync_details.append({
                            "iccid": card.iccid,
                            "status": "failed",
                            "reason": str(e)
                        })

            await db.commit()

            # 更新流量池统计
            pool_ids = set()
            for card in cards:
                if card.pool_id:
                    pool_ids.add(card.pool_id)
            
            if pool_ids:
                from app.crud.pool_crud import pool_crud
                for pool_id in pool_ids:
                    await pool_crud.update_stats(db, pool_id)

            # 日快照只保留最近180天，避免历史表无限增长
            from app.crud.iot_card_crud import card_usage_history_crud
            retention_cutoff = date.today() - timedelta(days=180)
            await card_usage_history_crud.prune_old_snapshots(
                db=db,
                snapshot_type="daily",
                before_date=retention_cutoff
            )


            # 更新同步日志
            final_status = SyncStatus.success if fail_count == 0 else (
                SyncStatus.partial if success_count > 0 else SyncStatus.failed
            )
            await sync_log_crud.update_status(
                db, log.id, final_status,
                total_count=total_count,
                success_count=success_count,
                fail_count=fail_count,
                sync_data={"details": sync_details[:100]}  # 只保存前100条详情
            )

            return {
                "sync_no": log.sync_no,
                "sync_type": "usage",
                "total": total_count,
                "success": success_count,
                "failed": fail_count,
                "status": final_status.value
            }

        except Exception as e:
            await sync_log_crud.update_status(
                db, log.id, SyncStatus.failed,
                error_message=str(e)
            )
            raise BusinessException(code=500, msg=f"同步失败: {str(e)}")

    # ============ 生命周期同步 ============

    async def sync_lifecycle(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        iccid_list: Optional[List[str]] = None,
        triggered_by: Optional[int] = None
    ) -> dict:
        """同步生命周期数据"""
        # 创建同步日志
        log = await sync_log_crud.create(
            db=db,
            sync_type=SyncType.lifecycle,
            supplier_id=supplier_id,
            triggered_by=triggered_by,
            trigger_type="manual"
        )

        try:
            await sync_log_crud.update_status(db, log.id, SyncStatus.running)

            cards = await self._get_cards_for_sync(db, supplier_id, iccid_list)
            
            if not cards:
                await sync_log_crud.update_status(
                    db, log.id, SyncStatus.success,
                    total_count=0, success_count=0, fail_count=0
                )
                return {
                    "sync_no": log.sync_no,
                    "sync_type": "lifecycle",
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "status": "success"
                }

            # 按供应商分组
            supplier_cards = {}
            for card in cards:
                if card.supplier_id not in supplier_cards:
                    supplier_cards[card.supplier_id] = []
                supplier_cards[card.supplier_id].append(card)

            total_count = len(cards)
            success_count = 0
            fail_count = 0
            sync_details = []

            for sup_id, sup_cards in supplier_cards.items():
                supplier = await self._get_supplier(db, sup_id)
                if not supplier:
                    fail_count += len(sup_cards)
                    continue

                try:
                    client = get_supplier_client(
                        supplier_id=sup_id,
                        api_url=supplier.api_url or "",
                        api_key=supplier.api_key or "",
                        api_secret=supplier.api_secret or ""
                    )

                    iccids = [card.iccid for card in sup_cards]
                    lifecycle_data = await self._retry_api_call(client.get_batch_lifecycle, iccids)

                    lifecycle_map = {item["iccid"]: item for item in lifecycle_data}
                    for card in sup_cards:
                        if card.iccid in lifecycle_map:
                            data = lifecycle_map[card.iccid]
                            
                            # 记录旧状态
                            old_status = card.status
                            old_expired_at = card.expired_at

                            # 更新生命周期日期
                            if data.get("test_expire_date"):
                                card.test_expire_date = datetime.strptime(
                                    data["test_expire_date"], "%Y-%m-%d"
                                ).date()
                            if data.get("silent_expire_date"):
                                card.silent_expire_date = datetime.strptime(
                                    data["silent_expire_date"], "%Y-%m-%d"
                                ).date()
                            if data.get("activated_at"):
                                card.activated_at = datetime.strptime(
                                    data["activated_at"], "%Y-%m-%d"
                                ).date()
                            if data.get("expired_at"):
                                new_expired_at = datetime.strptime(
                                    data["expired_at"], "%Y-%m-%d"
                                ).date()
                                # 年包：检测续费
                                if (card.period_type.value == "yearly" and
                                    old_expired_at and
                                    new_expired_at > old_expired_at):
                                    await self._record_usage_snapshot(db, card, "period_end")
                                card.expired_at = new_expired_at

                            # 更新状态
                            if data.get("status"):
                                card.status = CardStatus(data["status"])

                            # 检查并更新卡片状态（根据沉默期等规则）
                            from app.services.card_status_service import check_and_update_card_status
                            await check_and_update_card_status(db, card)

                            # 如果卡片从非激活状态变为激活状态，且是流量池卡，自动加入流量池
                            from app.db.models.iot_card import CardType
                            if (old_status != CardStatus.activated and 
                                card.status == CardStatus.activated and
                                card.card_type == CardType.pool and
                                card.pool_id is None and
                                card.user_id is not None):
                                await self._auto_join_pool(db, card)
                            
                            success_count += 1
                            sync_details.append({
                                "iccid": card.iccid,
                                "status": "success"
                            })
                        else:
                            fail_count += 1
                            sync_details.append({
                                "iccid": card.iccid,
                                "status": "failed",
                                "reason": "未返回数据"
                            })

                except Exception as e:
                    fail_count += len(sup_cards)
                    for card in sup_cards:
                        sync_details.append({
                            "iccid": card.iccid,
                            "status": "failed",
                            "reason": str(e)
                        })

            await db.commit()

            final_status = SyncStatus.success if fail_count == 0 else (
                SyncStatus.partial if success_count > 0 else SyncStatus.failed
            )
            await sync_log_crud.update_status(
                db, log.id, final_status,
                total_count=total_count,
                success_count=success_count,
                fail_count=fail_count,
                sync_data={"details": sync_details[:100]}
            )

            return {
                "sync_no": log.sync_no,
                "sync_type": "lifecycle",
                "total": total_count,
                "success": success_count,
                "failed": fail_count,
                "status": final_status.value
            }

        except Exception as e:
            await sync_log_crud.update_status(
                db, log.id, SyncStatus.failed,
                error_message=str(e)
            )
            raise BusinessException(code=500, msg=f"同步失败: {str(e)}")

    # ============ 单卡同步 ============

    async def sync_single_card(
        self,
        db: AsyncSession,
        iccid: str,
        triggered_by: Optional[int] = None,
        current_user = None
    ) -> dict:
        """同步单卡信息 (流量+生命周期)"""
        # 获取卡片
        card_query = select(IotCardModel).where(
            IotCardModel.iccid == iccid,
            IotCardModel.is_deleted == 0
        )
        card_result = await db.execute(card_query)
        card = card_result.scalar_one_or_none()

        if not card:
            raise BusinessException(code=404, msg="卡片不存在")

        # 权限校验：非超级管理员只能同步自己的卡片
        if current_user:
            from app.db.models.sys_user import UserLevel
            if current_user.user_level != UserLevel.SUPER_ADMIN.value:
                if card.user_id != current_user.id:
                    raise BusinessException(code=403, msg="无权同步此卡片")

        # 创建同步日志
        log = await sync_log_crud.create(
            db=db,
            sync_type=SyncType.single_card,
            card_id=card.id,
            iccid=iccid,
            triggered_by=triggered_by,
            trigger_type="manual"
        )

        try:
            await sync_log_crud.update_status(db, log.id, SyncStatus.running)

            # 获取供应商
            supplier = await self._get_supplier(db, card.supplier_id)
            if not supplier:
                raise BusinessException(code=404, msg="供应商不存在")

            client = get_supplier_client(
                supplier_id=card.supplier_id,
                api_url=supplier.api_url or "",
                api_key=supplier.api_key or "",
                api_secret=supplier.api_secret or ""
            )

            # 同步流量（带重试）
            usage_data = await self._retry_api_call(client.get_card_usage, iccid)
            card.data_used = usage_data.get("data_used", 0)
            card.data_total = usage_data.get("data_total", card.data_total)
            card.data_sync_at = datetime.now()

            # 检查并更新卡片状态
            from app.services.card_status_service import check_and_update_card_status
            await check_and_update_card_status(db, card)

            # 记录旧状态
            old_status = card.status

            # 同步生命周期（带重试）
            lifecycle_data = await self._retry_api_call(client.get_card_lifecycle, iccid)
            if lifecycle_data.get("test_expire_date"):
                card.test_expire_date = datetime.strptime(
                    lifecycle_data["test_expire_date"], "%Y-%m-%d"
                ).date()
            if lifecycle_data.get("silent_expire_date"):
                card.silent_expire_date = datetime.strptime(
                    lifecycle_data["silent_expire_date"], "%Y-%m-%d"
                ).date()
            if lifecycle_data.get("activated_at"):
                card.activated_at = datetime.strptime(
                    lifecycle_data["activated_at"], "%Y-%m-%d"
                ).date()
            if lifecycle_data.get("expired_at"):
                card.expired_at = datetime.strptime(
                    lifecycle_data["expired_at"], "%Y-%m-%d"
                ).date()
            if lifecycle_data.get("status"):
                card.status = CardStatus(lifecycle_data["status"])

            # 如果卡片从非激活状态变为激活状态，且是流量池卡，自动加入流量池
            from app.db.models.iot_card import CardType
            if (old_status != CardStatus.activated and 
                card.status == CardStatus.activated and
                card.card_type == CardType.pool and
                card.pool_id is None and
                card.user_id is not None):
                await self._auto_join_pool(db, card)

            await db.commit()

            await sync_log_crud.update_status(
                db, log.id, SyncStatus.success,
                total_count=1, success_count=1, fail_count=0,
                sync_data={
                    "usage": usage_data,
                    "lifecycle": lifecycle_data
                }
            )

            return {
                "sync_no": log.sync_no,
                "sync_type": "single_card",
                "total": 1,
                "success": 1,
                "failed": 0,
                "status": "success"
            }

        except Exception as e:
            await sync_log_crud.update_status(
                db, log.id, SyncStatus.failed,
                total_count=1, success_count=0, fail_count=1,
                error_message=str(e)
            )
            raise BusinessException(code=500, msg=f"同步失败: {str(e)}")

    # ============ 同步日志 ============

    async def get_sync_logs(
        self,
        db: AsyncSession,
        sync_type: Optional[str] = None,
        supplier_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取同步日志列表"""
        items, total = await sync_log_crud.get_list(
            db=db,
            sync_type=sync_type,
            supplier_id=supplier_id,
            status=status,
            page=page,
            page_size=page_size
        )
        return [item.to_dict() for item in items], total

    # ============ 同步任务 ============

    async def create_sync_task(
        self,
        db: AsyncSession,
        task_name: str,
        sync_type: str,
        supplier_id: Optional[int] = None,
        cron_expression: Optional[str] = None,
        is_enabled: int = 1,
        created_by: Optional[int] = None,
        remark: Optional[str] = None
    ) -> dict:
        """创建同步任务"""
        task = await sync_task_crud.create(
            db=db,
            task_name=task_name,
            sync_type=SyncType(sync_type),
            supplier_id=supplier_id,
            cron_expression=cron_expression,
            is_enabled=is_enabled,
            created_by=created_by,
            remark=remark
        )
        return task.to_dict()

    async def get_sync_tasks(
        self,
        db: AsyncSession,
        sync_type: Optional[str] = None,
        is_enabled: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取同步任务列表"""
        items, total = await sync_task_crud.get_list(
            db=db,
            sync_type=sync_type,
            is_enabled=is_enabled,
            page=page,
            page_size=page_size
        )
        return [item.to_dict() for item in items], total

    async def update_sync_task(
        self,
        db: AsyncSession,
        task_id: int,
        task_name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        is_enabled: Optional[int] = None,
        remark: Optional[str] = None
    ) -> dict:
        """更新同步任务"""
        task = await sync_task_crud.update(
            db=db,
            task_id=task_id,
            task_name=task_name,
            cron_expression=cron_expression,
            is_enabled=is_enabled,
            remark=remark
        )
        if not task:
            raise BusinessException(code=404, msg="任务不存在")
        return task.to_dict()

    async def delete_sync_task(self, db: AsyncSession, task_id: int) -> bool:
        """删除同步任务"""
        success = await sync_task_crud.delete(db, task_id)
        if not success:
            raise BusinessException(code=404, msg="任务不存在")
        return True

    # ============ 辅助方法 ============

    async def _get_cards_for_sync(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        iccid_list: Optional[List[str]] = None
    ) -> List[IotCardModel]:
        """获取需要同步的卡片"""
        query = select(IotCardModel).where(IotCardModel.is_deleted == 0)

        if supplier_id:
            query = query.where(IotCardModel.supplier_id == supplier_id)

        if iccid_list:
            query = query.where(IotCardModel.iccid.in_(iccid_list))
        else:
            # 同步已出库的卡片 或 已激活的库存卡
            query = query.where(
                or_(
                    IotCardModel.user_id.isnot(None),
                    and_(IotCardModel.user_id.is_(None), IotCardModel.status == CardStatus.activated)
                )
            )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def _get_supplier(self, db: AsyncSession, supplier_id: int) -> Optional[SupplierModel]:
        """获取供应商信息"""
        query = select(SupplierModel).where(
            SupplierModel.id == supplier_id,
            SupplierModel.is_deleted == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _auto_join_pool(self, db: AsyncSession, card: IotCardModel) -> None:
        """自动将流量池卡加入到对应的流量池"""
        try:
            from app.crud.pool_crud import pool_crud, pool_card_crud
            from app.db.models.iot_card import CardType
            
            # 确认是流量池卡
            if card.card_type != CardType.pool:
                return
            
            # 确认卡片已激活且有用户
            if card.status != CardStatus.activated or card.user_id is None:
                return
            
            # 确认卡片未加入流量池
            if card.pool_id is not None:
                return
            
            # 查找或创建对应的流量池
            pool = await pool_crud.find_or_create_pool(
                db=db,
                user_id=card.user_id,
                carrier=card.carrier.value,
                flow_size=card.flow_size,
                period_type=card.period_type.value,
                created_by=card.user_id,
                sale_package_id=card.sale_package_id
            )
            
            # 将卡片加入流量池
            card.pool_id = pool.id
            card.is_pool_member = 1
            
            # 记录日志
            from app.db.models.pool import PoolCardLogModel
            log = PoolCardLogModel(
                pool_id=pool.id,
                card_id=card.id,
                iccid=card.iccid,
                action="add",
                operator_id=card.user_id,
                remark="激活后自动加入流量池"
            )
            db.add(log)
            
            # 更新流量池统计（在commit后）
            await db.flush()
            await pool_crud.update_stats(db, pool.id)
            
        except Exception as e:
            # 自动加入失败不影响同步流程，只记录日志
            print(f"自动加入流量池失败 - ICCID: {card.iccid}, 错误: {str(e)}")


sync_service = SyncService()
