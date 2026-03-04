"""
项目 CRUD
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.project import ProjectModel
from app.db.models.iot_card import IotCardModel


class ProjectCRUD:

    async def get_list(
        self,
        db: AsyncSession,
        user_id: int,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[dict], int]:
        """获取用户的项目列表（含卡片数量）"""
        conditions = [ProjectModel.is_deleted == 0, ProjectModel.user_id == user_id]

        if keyword:
            conditions.append(ProjectModel.name.like(f"%{keyword}%"))

        # 总数
        count_stmt = select(func.count(ProjectModel.id)).where(*conditions)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * page_size
        stmt = select(ProjectModel).where(*conditions).order_by(ProjectModel.id.desc()).offset(offset).limit(page_size)
        result = await db.execute(stmt)
        projects = list(result.scalars().all())

        # 查询每个项目的卡片数量
        items = []
        for p in projects:
            card_count_stmt = select(func.count(IotCardModel.id)).where(
                IotCardModel.project_id == p.id,
                IotCardModel.is_deleted == 0
            )
            card_count_result = await db.execute(card_count_stmt)
            card_count = card_count_result.scalar() or 0
            items.append({
                "id": p.id,
                "name": p.name,
                "user_id": p.user_id,
                "remark": p.remark,
                "card_count": card_count,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            })

        return items, total

    async def get_by_id(self, db: AsyncSession, project_id: int) -> Optional[ProjectModel]:
        stmt = select(ProjectModel).where(ProjectModel.id == project_id, ProjectModel.is_deleted == 0)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, user_id: int, name: str, remark: Optional[str] = None) -> ProjectModel:
        project = ProjectModel(name=name, user_id=user_id, remark=remark)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    async def update(self, db: AsyncSession, project: ProjectModel, name: Optional[str] = None, remark: Optional[str] = None) -> ProjectModel:
        if name is not None:
            project.name = name
        if remark is not None:
            project.remark = remark
        await db.commit()
        await db.refresh(project)
        return project

    async def delete(self, db: AsyncSession, project: ProjectModel) -> None:
        project.is_deleted = 1
        # 将该项目下的卡片的 project_id 置空
        from sqlalchemy import update
        await db.execute(
            update(IotCardModel).where(IotCardModel.project_id == project.id).values(project_id=None)
        )
        await db.commit()

    async def get_all_by_user(self, db: AsyncSession, user_id: int) -> List[ProjectModel]:
        """获取用户的所有项目（不分页，用于下拉选择）"""
        stmt = select(ProjectModel).where(
            ProjectModel.user_id == user_id,
            ProjectModel.is_deleted == 0
        ).order_by(ProjectModel.id.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())


project_crud = ProjectCRUD()
