from datetime import date

import pytest

from app.db.models.iot_card import CardStatus
from app.services.card_status_service import check_and_update_card_status


class DummyPeriodType:
    def __init__(self, value: str):
        self.value = value


class DummyCarrier:
    def __init__(self, value: str):
        self.value = value


class DummyCard:
    def __init__(self):
        self.status = CardStatus.activated
        self.activated_at = None
        self.expired_at = date(2027, 8, 31)
        self.data_used = 1
        self.period_type = DummyPeriodType("monthly")
        self.period_count = 12
        self.carrier = DummyCarrier("cmcc")
        self.test_expire_date = None
        self.silent_expire_date = None
        self.suspend_type = None


@pytest.mark.asyncio
async def test_check_and_update_card_status_keeps_existing_expiry_when_backfilling_activation():
    card = DummyCard()

    changed = await check_and_update_card_status(None, card)

    assert changed is True
    assert card.activated_at == date.today()
    assert card.expired_at == date(2027, 8, 31)
