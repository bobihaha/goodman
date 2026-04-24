"""
停卡策略相关的 CRUD 操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.sql import func
from typing import Optional, List, Tuple
from datetime import datetime

from app.db.models.suspend import (
    SuspendPolicyModel, SuspendLogModel, SupplierSuspendOperationModel, AlertLogModel,
    SuspendActionType, AlertLevel, AlertTargetType
)
from app.db.models.iot_card import IotCardModel, CardStatus, SuspendType
from app.db.models.pool import TrafficPoolModel


class SuspendPolicyCRUD:
    """停卡策略 CRUD"""

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        policy_type: str,
        description: Optional[str] = None,
        warning_threshold: int = 80,
        critical_threshold: int = 90,
        stop_threshold: int = 100,
        user_id: Optional[int] = None,
        pool_id: Optional[int] = None,
        auto_suspend: bool = True,
        auto_resume: bool = False,
        notify_warning: bool = True,
        notify_critical: bool = True,
        notify_suspend: bool = True,
        is_enabled: bool = True,
        created_by: Optional[int] = None
    ) -> SuspendPolicyModel:
        """创建停卡策略"""
        policy = SuspendPolicyModel(
            name=name,
            description=description,
            policy_type=policy_type,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            stop_threshold=stop_threshold,
            user_id=user_id,
            pool_id=pool_id,
            auto_suspend=1 if auto_suspend else 0,
            auto_resume=1 if auto_resume else 0,
            notify_warning=1 if notify_warning else 0,
            notify_critical=1 if notify_critical else 0,
            notify_suspend=1 if notify_suspend else 0,
            is_enabled=1 if is_enabled else 0,
            created_by=created_by
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def get_by_id(db: AsyncSession, policy_id: int) -> Optional[SuspendPolicyModel]:
        """根据ID获取策略"""
        result = await db.execute(
            select(SuspendPolicyModel).where(
                SuspendPolicyModel.id == policy_id,
                SuspendPolicyModel.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        policy_type: Optional[str] = None,
        user_id: Optional[int] = None,
        is_enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SuspendPolicyModel], int]:
        """获取策略列表"""
        query = select(SuspendPolicyModel).where(SuspendPolicyModel.is_deleted == 0)
        count_query = select(func.count(SuspendPolicyModel.id)).where(SuspendPolicyModel.is_deleted == 0)

        if policy_type:
            query = query.where(SuspendPolicyModel.policy_type == policy_type)
            count_query = count_query.where(SuspendPolicyModel.policy_type == policy_type)

        if user_id is not None:
            query = query.where(
                or_(SuspendPolicyModel.user_id == user_id, SuspendPolicyModel.user_id.is_(None))
            )
            count_query = count_query.where(
                or_(SuspendPolicyModel.user_id == user_id, SuspendPolicyModel.user_id.is_(None))
            )

        if is_enabled is not None:
            query = query.where(SuspendPolicyModel.is_enabled == (1 if is_enabled else 0))
            count_query = count_query.where(SuspendPolicyModel.is_enabled == (1 if is_enabled else 0))

        # 总数
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(SuspendPolicyModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        policies = result.scalars().all()

        return list(policies), total

    @staticmethod
    async def update(
        db: AsyncSession,
        policy_id: int,
        **kwargs
    ) -> Optional[SuspendPolicyModel]:
        """更新策略"""
        policy = await SuspendPolicyCRUD.get_by_id(db, policy_id)
        if not policy:
            return None

        # 处理布尔值转换
        bool_fields = ['auto_suspend', 'auto_resume', 'notify_warning', 
                       'notify_critical', 'notify_suspend', 'is_enabled']
        for field in bool_fields:
            if field in kwargs and kwargs[field] is not None:
                kwargs[field] = 1 if kwargs[field] else 0

        for key, value in kwargs.items():
            if value is not None and hasattr(policy, key):
                setattr(policy, key, value)

        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def delete(db: AsyncSession, policy_id: int) -> bool:
        """删除策略(软删除)"""
        policy = await SuspendPolicyCRUD.get_by_id(db, policy_id)
        if not policy:
            return False
        policy.is_deleted = 1
        await db.commit()
        return True

    @staticmethod
    async def get_active_policies(
        db: AsyncSession,
        policy_type: str,
        user_id: Optional[int] = None,
        pool_id: Optional[int] = None
    ) -> List[SuspendPolicyModel]:
        """获取生效的策略"""
        query = select(SuspendPolicyModel).where(
            SuspendPolicyModel.is_deleted == 0,
            SuspendPolicyModel.is_enabled == 1,
            SuspendPolicyModel.policy_type == policy_type
        )

        # 匹配用户范围 (全局或指定用户)
        if user_id:
            query = query.where(
                or_(SuspendPolicyModel.user_id.is_(None), SuspendPolicyModel.user_id == user_id)
            )
        else:
            query = query.where(SuspendPolicyModel.user_id.is_(None))

        # 匹配流量池范围
        if pool_id:
            query = query.where(
                or_(SuspendPolicyModel.pool_id.is_(None), SuspendPolicyModel.pool_id == pool_id)
            )

        result = await db.execute(query)
        return list(result.scalars().all())


class SuspendLogCRUD:
    """停卡记录 CRUD"""

    @staticmethod
    async def create(
        db: AsyncSession,
        card_id: int,
        iccid: str,
        action: SuspendActionType,
        suspend_type: str,
        policy_id: Optional[int] = None,
        pool_id: Optional[int] = None,
        reason: Optional[str] = None,
        api_called: bool = False,
        api_result: Optional[str] = None,
        operator_id: Optional[int] = None
    ) -> SuspendLogModel:
        """创建停卡记录"""
        log = SuspendLogModel(
            card_id=card_id,
            iccid=iccid,
            action=action,
            suspend_type=suspend_type,
            policy_id=policy_id,
            pool_id=pool_id,
            reason=reason,
            api_called=1 if api_called else 0,
            api_result=api_result,
            operator_id=operator_id
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_list(
        db: AsyncSession,
        card_id: Optional[int] = None,
        action: Optional[str] = None,
        suspend_type: Optional[str] = None,
        pool_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SuspendLogModel], int]:
        """获取停卡记录列表"""
        query = select(SuspendLogModel).where(SuspendLogModel.is_deleted == 0)
        count_query = select(func.count(SuspendLogModel.id)).where(SuspendLogModel.is_deleted == 0)

        if card_id:
            query = query.where(SuspendLogModel.card_id == card_id)
            count_query = count_query.where(SuspendLogModel.card_id == card_id)

        if action:
            query = query.where(SuspendLogModel.action == action)
            count_query = count_query.where(SuspendLogModel.action == action)

        if suspend_type:
            query = query.where(SuspendLogModel.suspend_type == suspend_type)
            count_query = count_query.where(SuspendLogModel.suspend_type == suspend_type)

        if pool_id:
            query = query.where(SuspendLogModel.pool_id == pool_id)
            count_query = count_query.where(SuspendLogModel.pool_id == pool_id)

        if start_time:
            query = query.where(SuspendLogModel.created_at >= start_time)
            count_query = count_query.where(SuspendLogModel.created_at >= start_time)

        if end_time:
            query = query.where(SuspendLogModel.created_at <= end_time)
            count_query = count_query.where(SuspendLogModel.created_at <= end_time)

        # 总数
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(SuspendLogModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    @staticmethod
    async def get_latest_by_card_and_action(
        db: AsyncSession,
        card_id: int,
        action: SuspendActionType
    ) -> Optional[SuspendLogModel]:
        """获取某张卡最近一次指定操作日志。"""
        result = await db.execute(
            select(SuspendLogModel).where(
                SuspendLogModel.card_id == card_id,
                SuspendLogModel.action == action,
                SuspendLogModel.is_deleted == 0
            ).order_by(SuspendLogModel.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()


class AlertLogCRUD:
    """告警记录 CRUD"""

    @staticmethod
    async def create(
        db: AsyncSession,
        target_type: AlertTargetType,
        target_id: int,
        target_name: str,
        alert_level: AlertLevel,
        usage_percent: int,
        threshold: int,
        policy_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> AlertLogModel:
        """创建告警记录"""
        alert = AlertLogModel(
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            alert_level=alert_level,
            usage_percent=usage_percent,
            threshold=threshold,
            policy_id=policy_id,
            user_id=user_id,
            notified=0,
            handled=0
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert

    @staticmethod
    async def get_by_id(db: AsyncSession, alert_id: int) -> Optional[AlertLogModel]:
        """根据ID获取告警"""
        result = await db.execute(
            select(AlertLogModel).where(
                AlertLogModel.id == alert_id,
                AlertLogModel.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        target_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        user_id: Optional[int] = None,
        handled: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AlertLogModel], int]:
        """获取告警记录列表"""
        query = select(AlertLogModel).where(AlertLogModel.is_deleted == 0)
        count_query = select(func.count(AlertLogModel.id)).where(AlertLogModel.is_deleted == 0)

        if target_type:
            query = query.where(AlertLogModel.target_type == target_type)
            count_query = count_query.where(AlertLogModel.target_type == target_type)

        if alert_level:
            query = query.where(AlertLogModel.alert_level == alert_level)
            count_query = count_query.where(AlertLogModel.alert_level == alert_level)

        if user_id:
            query = query.where(AlertLogModel.user_id == user_id)
            count_query = count_query.where(AlertLogModel.user_id == user_id)

        if handled is not None:
            query = query.where(AlertLogModel.handled == (1 if handled else 0))
            count_query = count_query.where(AlertLogModel.handled == (1 if handled else 0))

        if start_time:
            query = query.where(AlertLogModel.created_at >= start_time)
            count_query = count_query.where(AlertLogModel.created_at >= start_time)

        if end_time:
            query = query.where(AlertLogModel.created_at <= end_time)
            count_query = count_query.where(AlertLogModel.created_at <= end_time)

        # 总数
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(AlertLogModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        alerts = result.scalars().all()

        return list(alerts), total

    @staticmethod
    async def handle_alert(
        db: AsyncSession,
        alert_id: int,
        handled_by: int,
        handle_remark: Optional[str] = None
    ) -> Optional[AlertLogModel]:
        """处理告警"""
        alert = await AlertLogCRUD.get_by_id(db, alert_id)
        if not alert:
            return None
        
        alert.handled = 1
        alert.handled_at = datetime.now()
        alert.handled_by = handled_by
        alert.handle_remark = handle_remark
        
        await db.commit()
        await db.refresh(alert)
        return alert

    @staticmethod
    async def mark_notified(db: AsyncSession, alert_id: int) -> Optional[AlertLogModel]:
        """标记已通知"""
        alert = await AlertLogCRUD.get_by_id(db, alert_id)
        if not alert:
            return None
        
        alert.notified = 1
        alert.notified_at = datetime.now()
        
        await db.commit()
        await db.refresh(alert)
        return alert

    @staticmethod
    async def check_exists(
        db: AsyncSession,
        target_type: AlertTargetType,
        target_id: int,
        alert_level: AlertLevel,
        hours: int = 24
    ) -> bool:
        """检查是否已存在相同告警(避免重复告警)"""
        from datetime import timedelta
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        result = await db.execute(
            select(func.count(AlertLogModel.id)).where(
                AlertLogModel.is_deleted == 0,
                AlertLogModel.target_type == target_type,
                AlertLogModel.target_id == target_id,
                AlertLogModel.alert_level == alert_level,
                AlertLogModel.created_at >= time_threshold
            )
        )
        count = result.scalar()
        return count > 0


class SupplierSuspendOperationCRUD:
    """供应商停复机操作记录 CRUD"""

    @staticmethod
    async def create(
        db: AsyncSession,
        card_id: int,
        supplier_id: Optional[int],
        iccid: str,
        msisdn: Optional[str],
        action: SuspendActionType,
        callback_no: str,
        request_payload: Optional[str] = None,
        operator_id: Optional[int] = None
    ) -> SupplierSuspendOperationModel:
        operation = SupplierSuspendOperationModel(
            card_id=card_id,
            supplier_id=supplier_id,
            iccid=iccid,
            msisdn=msisdn,
            action=action,
            callback_no=callback_no,
            request_payload=request_payload,
            operator_id=operator_id
        )
        db.add(operation)
        await db.commit()
        await db.refresh(operation)
        return operation

    @staticmethod
    async def get_by_callback_no(db: AsyncSession, callback_no: str) -> Optional[SupplierSuspendOperationModel]:
        result = await db.execute(
            select(SupplierSuspendOperationModel).where(
                SupplierSuspendOperationModel.callback_no == callback_no,
                SupplierSuspendOperationModel.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_request_result(
        db: AsyncSession,
        operation_id: int,
        request_result: str
    ) -> Optional[SupplierSuspendOperationModel]:
        operation = await db.get(SupplierSuspendOperationModel, operation_id)
        if not operation or operation.is_deleted == 1:
            return None
        operation.request_result = request_result
        await db.commit()
        await db.refresh(operation)
        return operation

    @staticmethod
    async def update_callback_result(
        db: AsyncSession,
        operation: SupplierSuspendOperationModel,
        callback_payload: str,
        callback_code: Optional[str],
        callback_msg: Optional[str],
        account_status: Optional[str],
        callback_status: str
    ) -> SupplierSuspendOperationModel:
        operation.callback_payload = callback_payload
        operation.callback_code = callback_code
        operation.callback_msg = callback_msg
        operation.account_status = account_status
        operation.callback_status = callback_status
        operation.completed_at = datetime.now()
        await db.commit()
        await db.refresh(operation)
        return operation


class CardSuspendCRUD:
    """卡片停卡操作 CRUD"""

    @staticmethod
    async def suspend_card(
        db: AsyncSession,
        card_id: int,
        suspend_type: SuspendType,
        reason: Optional[str] = None
    ) -> Optional[IotCardModel]:
        """停卡"""
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.is_deleted == 0
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            return None

        card.status = CardStatus.suspended
        card.suspend_type = suspend_type
        card.suspend_at = datetime.now()
        card.suspend_reason = reason

        await db.commit()
        await db.refresh(card)
        return card

    @staticmethod
    async def resume_card(
        db: AsyncSession,
        card_id: int
    ) -> Optional[IotCardModel]:
        """复机"""
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.is_deleted == 0
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            return None

        # 恢复到激活状态
        card.status = CardStatus.activated
        card.suspend_type = SuspendType.none
        card.suspend_at = None
        card.suspend_reason = None

        await db.commit()
        await db.refresh(card)
        return card

    @staticmethod
    async def get_cards_by_ids(
        db: AsyncSession,
        card_ids: List[int],
        user_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None
    ) -> List[IotCardModel]:
        """批量获取卡片"""
        query = select(IotCardModel).where(
            IotCardModel.id.in_(card_ids),
            IotCardModel.is_deleted == 0
        )
        if user_id:
            query = query.where(IotCardModel.user_id == user_id)
        elif user_ids is not None:
            query = query.where(IotCardModel.user_id.in_(user_ids))

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_expired_cards(db: AsyncSession) -> List[IotCardModel]:
        """获取已到期但未停卡的卡片"""
        from datetime import date
        today = date.today()
        
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.is_deleted == 0,
                IotCardModel.status == CardStatus.activated,
                IotCardModel.expired_at < today
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_exceed_cards(
        db: AsyncSession,
        threshold_percent: int = 100
    ) -> List[IotCardModel]:
        """获取超量的非池卡"""
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.is_deleted == 0,
                IotCardModel.status == CardStatus.activated,
                IotCardModel.is_pool_member == 0,
                IotCardModel.data_total > 0,
                (IotCardModel.data_used * 100 / IotCardModel.data_total) >= threshold_percent
            )
        )
        return list(result.scalars().all())
