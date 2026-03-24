"""
账户余额服务
当前版本复用 sys_users.quota JSON 存储余额信息，减少数据库改造范围。
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.system_crud import SysOperationLogCRUD
from app.db.models.sys_user import SysUserModel, UserLevel
from app.schemas.auth import CurrentUser
from app.utils.exceptions import BusinessException, PermissionDeniedException, UserNotFoundException


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


def _quota_dict(raw_quota: Any) -> Dict[str, Any]:
    return dict(raw_quota or {})


class AccountBalanceService:
    """余额服务"""

    @staticmethod
    def get_balance_from_quota(quota: Any) -> Decimal:
        data = _quota_dict(quota)
        return _to_decimal(data.get("account_balance", 0))

    @staticmethod
    def _set_balance_fields(quota: Any, balance: Decimal, amount: Optional[Decimal] = None, field_prefix: str = "last_grant") -> Dict[str, Any]:
        data = _quota_dict(quota)
        data["account_balance"] = float(balance)
        if amount is not None:
            data[f"{field_prefix}_at"] = datetime.now().isoformat()
            data[f"{field_prefix}_amount"] = float(amount)
        return data

    @staticmethod
    async def _get_user(db: AsyncSession, user_id: int, for_update: bool = False) -> SysUserModel:
        stmt = select(SysUserModel).where(SysUserModel.id == user_id, SysUserModel.is_deleted == 0)
        if for_update:
            stmt = stmt.with_for_update()
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundException()
        return user

    @staticmethod
    def _check_grant_permission(operator: CurrentUser, target: SysUserModel) -> None:
        if operator.user_level == UserLevel.SUPER_ADMIN.value and target.user_level != UserLevel.SUPER_ADMIN.value:
            return
        if (
            operator.user_level == UserLevel.USER.value
            and target.user_level == UserLevel.SUB_USER.value
            and target.parent_id == operator.id
        ):
            return
        raise PermissionDeniedException()

    @classmethod
    async def get_balance_info(cls, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        user = await cls._get_user(db, user_id)
        quota = _quota_dict(user.quota)
        balance = cls.get_balance_from_quota(quota)
        alert_threshold = _to_decimal(quota.get("balance_alert_threshold", 1000))
        return {
            "balance": float(balance),
            "alert_threshold": float(alert_threshold),
            "is_alert": balance <= alert_threshold,
            "last_recharge_at": quota.get("last_grant_at"),
            "last_recharge_amount": float(_to_decimal(quota.get("last_grant_amount", 0))),
        }

    @classmethod
    async def grant_balance(
        cls,
        db: AsyncSession,
        operator: CurrentUser,
        target_user_id: int,
        amount: Decimal,
        remark: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if amount <= 0:
            raise BusinessException(code=400, msg="分配金额必须大于0")

        target = await cls._get_user(db, target_user_id, for_update=True)
        cls._check_grant_permission(operator, target)

        quota = _quota_dict(target.quota)
        if (
            request_id
            and quota.get("last_grant_request_id") == request_id
            and quota.get("last_grant_operator_id") == operator.id
        ):
            return {
                "target_user_id": target.id,
                "target_user_name": target.name,
                "before_balance": float(_to_decimal(quota.get("last_grant_before_balance", 0))),
                "amount": float(_to_decimal(quota.get("last_grant_amount", 0))),
                "after_balance": float(cls.get_balance_from_quota(quota)),
                "duplicated": True,
            }

        old_balance = cls.get_balance_from_quota(quota)
        new_balance = (old_balance + amount).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        target.quota = cls._set_balance_fields(quota, new_balance, amount, "last_grant")
        target.quota["last_grant_before_balance"] = float(old_balance)
        target.quota["last_grant_operator_id"] = operator.id
        if request_id:
            target.quota["last_grant_request_id"] = request_id

        await db.flush()

        await SysOperationLogCRUD.create(
            db=db,
            module="balance",
            action="grant",
            user_id=operator.id,
            user_name=operator.name,
            target_type="user",
            target_id=target.id,
            target_name=target.name,
            detail=(
                f"账户余额分配 {amount} 元，分配前 {old_balance} 元，分配后 {new_balance} 元。"
                f"备注：{remark or ''}"
            )
        )
        return {
            "target_user_id": target.id,
            "target_user_name": target.name,
            "before_balance": float(old_balance),
            "amount": float(amount),
            "after_balance": float(new_balance),
            "duplicated": False,
        }

    @classmethod
    async def consume_balance(
        cls,
        db: AsyncSession,
        user_id: int,
        amount: Decimal,
        detail: str,
        target_type: str,
        target_id: int,
        target_name: str
    ) -> Dict[str, Any]:
        if amount <= 0:
            raise BusinessException(code=400, msg="消费金额必须大于0")

        user = await cls._get_user(db, user_id, for_update=True)
        old_balance = cls.get_balance_from_quota(user.quota)
        if old_balance < amount:
            raise BusinessException(code=400, msg=f"余额不足，当前余额 {old_balance} 元")

        new_balance = (old_balance - amount).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        user.quota = cls._set_balance_fields(user.quota, new_balance)

        await db.flush()

        await SysOperationLogCRUD.create(
            db=db,
            module="balance",
            action="consume",
            user_id=user.id,
            user_name=user.name,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            detail=f"{detail}，消费 {amount} 元，消费前 {old_balance} 元，消费后 {new_balance} 元"
        )

        return {
            "before_balance": float(old_balance),
            "amount": float(amount),
            "after_balance": float(new_balance),
        }


account_balance_service = AccountBalanceService()
