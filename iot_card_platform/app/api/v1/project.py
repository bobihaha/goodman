"""
项目管理接口
"""
from fastapi import APIRouter, Depends, Body, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.crud.project_crud import project_crud
from app.db.database import get_db
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("", summary="项目列表", response_model=ResponseModel)
async def get_project_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取当前用户的项目列表"""
    items, total = await project_crud.get_list(
        db, user_id=current_user.id, keyword=keyword, page=page, page_size=page_size
    )
    return ResponseModel(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.get("/all", summary="所有项目（下拉选择）", response_model=ResponseModel)
async def get_all_projects(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取当前用户的所有项目（不分页）"""
    projects = await project_crud.get_all_by_user(db, current_user.id)
    return ResponseModel(data=[{"id": p.id, "name": p.name} for p in projects])


@router.get("/{project_id}", summary="项目详情", response_model=ResponseModel)
async def get_project_detail(
    project_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取项目详情"""
    project = await project_crud.get_by_id(db, project_id)
    if not project:
        return ResponseModel(code=404, msg="项目不存在")
    if project.user_id != current_user.id:
        return ResponseModel(code=403, msg="无权查看此项目")
    return ResponseModel(data={
        "id": project.id,
        "name": project.name,
        "user_id": project.user_id,
        "remark": project.remark,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    })


@router.post("", summary="创建项目", response_model=ResponseModel)
async def create_project(
    data: ProjectCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """创建项目"""
    project = await project_crud.create(db, user_id=current_user.id, name=data.name, remark=data.remark)
    return ResponseModel(msg="创建成功", data={
        "id": project.id,
        "name": project.name,
        "user_id": project.user_id,
        "remark": project.remark,
        "created_at": project.created_at.isoformat() if project.created_at else None,
    })


@router.put("/{project_id}", summary="更新项目", response_model=ResponseModel)
async def update_project(
    project_id: int = Path(...),
    data: ProjectUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """更新项目"""
    project = await project_crud.get_by_id(db, project_id)
    if not project:
        return ResponseModel(code=404, msg="项目不存在")
    if project.user_id != current_user.id:
        return ResponseModel(code=403, msg="无权修改此项目")
    project = await project_crud.update(db, project, name=data.name, remark=data.remark)
    return ResponseModel(msg="更新成功", data={
        "id": project.id,
        "name": project.name,
        "user_id": project.user_id,
        "remark": project.remark,
    })


@router.delete("/{project_id}", summary="删除项目", response_model=ResponseModel)
async def delete_project(
    project_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """删除项目"""
    project = await project_crud.get_by_id(db, project_id)
    if not project:
        return ResponseModel(code=404, msg="项目不存在")
    if project.user_id != current_user.id:
        return ResponseModel(code=403, msg="无权删除此项目")
    await project_crud.delete(db, project)
    return ResponseModel(msg="删除成功")
