"""
卡片状态自动转换服务
"""
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.iot_card import IotCardModel, CardStatus, SuspendType
from app.utils.date_utils import calculate_expiry_date


async def check_and_update_card_status(
    db: AsyncSession,
    card: IotCardModel
) -> bool:
    """
    检查并更新单张卡片状态

    Args:
        db: 数据库会话
        card: 卡片对象

    Returns:
        是否发生了状态变更
    """
    today = date.today()
    status_changed = False

    # 规则1: testing → silent (测试期到期)
    if card.status == CardStatus.testing:
        if card.test_expire_date and today > card.test_expire_date:
            card.status = CardStatus.silent
            status_changed = True

    # 规则2: testing/silent → activated (检测到流量使用)
    if card.status in [CardStatus.testing, CardStatus.silent]:
        if card.data_used > 0 and not card.activated_at:
            card.status = CardStatus.activated
            card.activated_at = today

            # 计算到期日期
            if card.period_type:
                card.expired_at = calculate_expiry_date(
                    start_date=today,
                    period_type=card.period_type.value,
                    period_months=card.period_count if card.period_type.value == "monthly" else None,
                    period_days=card.period_count * 360 if card.period_type.value == "yearly" else None
                )

            status_changed = True

    # 规则3: 修复已激活但缺少日期的卡片
    if card.status == CardStatus.activated and not card.activated_at and card.data_used > 0:
        card.activated_at = today
        if card.period_type:
            card.expired_at = calculate_expiry_date(
                start_date=today,
                period_type=card.period_type.value,
                period_months=card.period_count if card.period_type.value == "monthly" else None,
                period_days=card.period_count * 360 if card.period_type.value == "yearly" else None
            )
        status_changed = True

    # 规则4: activated → suspended (到期停机)
    if card.status == CardStatus.activated:
        if card.expired_at and today > card.expired_at:
            card.status = CardStatus.suspended
            card.suspend_type = SuspendType.expired
            status_changed = True

    return status_changed


card_status_service = None
