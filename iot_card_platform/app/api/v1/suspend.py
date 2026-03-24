"""
停卡策略 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.utils.auth import get_current_user, require_super_admin
from app.schemas.common import ResponseModel
from app.schemas.suspend import (
    PolicyCreate, PolicyUpdate, ManualSuspend, ManualResume, AlertHandle
)
from app.services.suspend_service import (
    SuspendPolicyService, SuspendActionService, 
    SuspendLogService, AlertLogService
)
from app.crud.sys_user_crud_enhanced import SysUserCRUDEnhanced

router = APIRouter()


async def _get_accessible_user_ids(current_user, db: AsyncSession):
    if current_user.user_level == 1:
        return None
    if current_user.user_level == 3:
        return [current_user.id]

    sys_user_crud = SysUserCRUDEnhanced()
    child_ids = await sys_user_crud.get_children_ids(db, current_user.id)
    return [current_user.id, *child_ids]


# ============ 停卡策略管理 ============

@router.get("/policies", summary="获取停卡策略列表")
async def get_policies(
    policy_type: Optional[str] = Query(None, description="策略类型: expired/pool_exceed/card_exceed"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取停卡策略列表"""
    # 普通用户只能看到全局策略和自己的策略 (user_level: 1=超级管理员)
    user_id = None if current_user.user_level == 1 else current_user.id
    
    policies, total = await SuspendPolicyService.get_policies(
        db=db,
        policy_type=policy_type,
        user_id=user_id,
        is_enabled=is_enabled,
        page=page,
        page_size=page_size
    )
    
    return ResponseModel(data={
        "items": policies,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.post("/policies", summary="创建停卡策略")
async def create_policy(
    data: PolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """创建停卡策略 (仅管理员)"""
    policy = await SuspendPolicyService.create_policy(
        db=db,
        data=data,
        created_by=current_user.id
    )
    return ResponseModel(data=policy.to_dict(), msg="创建成功")


@router.get("/policies/{policy_id}", summary="获取策略详情")
async def get_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取策略详情"""
    policy = await SuspendPolicyService.get_policy(db, policy_id)
    if not policy:
        return ResponseModel(code=404, msg="策略不存在")
    return ResponseModel(data=policy.to_dict())


@router.put("/policies/{policy_id}", summary="更新停卡策略")
async def update_policy(
    policy_id: int,
    data: PolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """更新停卡策略 (仅管理员)"""
    policy = await SuspendPolicyService.update_policy(db, policy_id, data)
    if not policy:
        return ResponseModel(code=404, msg="策略不存在")
    return ResponseModel(data=policy.to_dict(), msg="更新成功")


@router.delete("/policies/{policy_id}", summary="删除停卡策略")
async def delete_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """删除停卡策略 (仅管理员)"""
    success = await SuspendPolicyService.delete_policy(db, policy_id)
    if not success:
        return ResponseModel(code=404, msg="策略不存在")
    return ResponseModel(msg="删除成功")


# ============ 手动停卡/复机 ============

@router.post("/cards/suspend", summary="手动停卡")
async def manual_suspend(
    data: ManualSuspend,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """手动停卡"""
    is_admin = current_user.user_level == 1
    user_id = current_user.id
    user_ids = await _get_accessible_user_ids(current_user, db)
    
    result = await SuspendActionService.manual_suspend(
        db=db,
        data=data,
        operator_id=user_id,
        user_id=user_id,
        user_ids=user_ids,
        is_admin=is_admin
    )
    
    return ResponseModel(
        data={
            "success_count": result.success_count,
            "fail_count": result.fail_count,
            "success_cards": result.success_cards,
            "fail_cards": result.fail_cards
        },
        msg=f"停卡完成，成功{result.success_count}张，失败{result.fail_count}张"
    )


@router.post("/cards/resume", summary="手动复机")
async def manual_resume(
    data: ManualResume,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """手动复机"""
    is_admin = current_user.user_level == 1
    user_id = current_user.id
    user_ids = await _get_accessible_user_ids(current_user, db)

    result = await SuspendActionService.manual_resume(
        db=db,
        data=data,
        operator_id=user_id,
        user_id=user_id,
        user_ids=user_ids,
        is_admin=is_admin
    )

    return ResponseModel(
        data={
            "success_count": result.success_count,
            "fail_count": result.fail_count,
            "success_cards": result.success_cards,
            "fail_cards": result.fail_cards
        },
        msg=f"复机完成，成功{result.success_count}张，失败{result.fail_count}张"
    )


@router.post("/cards/force-activate", summary="批量强制激活")
async def force_activate(
    data: ManualResume,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """批量强制激活 (仅超级管理员)"""
    result = await SuspendActionService.manual_resume(
        db=db,
        data=data,
        operator_id=current_user.id,
        user_id=current_user.id,
        is_admin=True,
        force=True
    )

    return ResponseModel(
        data={
            "success_count": result.success_count,
            "fail_count": result.fail_count,
            "success_cards": result.success_cards,
            "fail_cards": result.fail_cards
        },
        msg=f"强制激活完成，成功{result.success_count}张，失败{result.fail_count}张"
    )


# ============ 自动任务触发 (管理员) ============

@router.post("/tasks/expired", summary="执行到期停卡任务")
async def run_expired_task(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """执行到期停卡任务 (仅管理员)"""
    result = await SuspendActionService.auto_suspend_expired(db)
    return ResponseModel(
        data=result,
        msg=f"任务完成，停卡{result['suspended_count']}张"
    )


@router.post("/tasks/card-exceed", summary="执行单卡超量检查任务")
async def run_card_exceed_task(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """执行单卡超量检查任务 (仅管理员)"""
    result = await SuspendActionService.auto_suspend_card_exceed(db)
    return ResponseModel(
        data=result,
        msg=f"任务完成，停卡{result['suspended_count']}张，新增告警{result['alerts_created']}条"
    )


# ============ 停卡记录 ============

@router.get("/logs", summary="获取停卡记录")
async def get_suspend_logs(
    card_id: Optional[int] = Query(None, description="卡片ID"),
    action: Optional[str] = Query(None, description="操作: suspend/resume"),
    suspend_type: Optional[str] = Query(None, description="停卡类型"),
    pool_id: Optional[int] = Query(None, description="流量池ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取停卡记录"""
    logs, total = await SuspendLogService.get_logs(
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
    
    return ResponseModel(data={
        "items": logs,
        "total": total,
        "page": page,
        "page_size": page_size
    })


# ============ 告警管理 ============

@router.get("/alerts", summary="获取告警列表")
async def get_alerts(
    target_type: Optional[str] = Query(None, description="目标类型: card/pool"),
    alert_level: Optional[str] = Query(None, description="告警级别: warning/critical/exceed"),
    handled: Optional[bool] = Query(None, description="是否已处理"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取告警列表"""
    # 普通用户只能看自己的告警 (user_level: 1=超级管理员)
    user_id = None if current_user.user_level == 1 else current_user.id
    
    alerts, total = await AlertLogService.get_alerts(
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
    
    return ResponseModel(data={
        "items": alerts,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/alerts/stats", summary="获取未处理告警统计")
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取未处理告警统计"""
    user_id = None if current_user.user_level == 1 else current_user.id
    
    stats = await AlertLogService.get_unhandled_count(db, user_id)
    return ResponseModel(data=stats)


@router.post("/alerts/{alert_id}/handle", summary="处理告警")
async def handle_alert(
    alert_id: int,
    data: AlertHandle,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """处理告警"""
    alert = await AlertLogService.handle_alert(
        db=db,
        alert_id=alert_id,
        handled_by=current_user.id,
        handle_remark=data.handle_remark
    )
    
    if not alert:
        return ResponseModel(code=404, msg="告警不存在")
    
    return ResponseModel(data=alert, msg="处理成功")
