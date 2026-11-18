"""本人卡片的项目分组；与卡片持有人划拨分离。"""
import json
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.iot_card import IotCardModel
from app.db.models.project import ProjectModel
from app.db.models.sys_log import SysOperationLogModel
from app.schemas.project import ProjectMoveRequest
from app.utils.exceptions import BusinessException


class ProjectService:
    async def get_owned_project(self, db, user_id, project_id, lock=False):
        stmt = select(ProjectModel).where(
            ProjectModel.id == project_id, ProjectModel.user_id == user_id,
            ProjectModel.is_deleted == 0,
        )
        if lock:
            stmt = stmt.with_for_update()
        project = (await db.execute(stmt)).scalar_one_or_none()
        if project is None:
            raise BusinessException(code=404, msg="项目不存在或无权操作")
        return project

    @staticmethod
    def add_move_log(db, card, user_id, old_project_id, new_project_id, original_user_id=None, action="move_project"):
        db.add(SysOperationLogModel(
            user_id=user_id, original_user_id=original_user_id,
            module="card", action=action, target_type="card",
            target_id=card.id, target_name=card.iccid, is_success=1,
            detail=json.dumps({"old_project_id": old_project_id, "new_project_id": new_project_id}, ensure_ascii=False),
        ))

    async def move_cards(self, db: AsyncSession, user_id: int, data: ProjectMoveRequest, original_user_id=None):
        if data.source_project_id is not None and data.source_ungrouped:
            raise BusinessException(msg="来源项目和未分组不能同时指定")
        # 锁定目标，避免与删除项目并发产生失效关联；卡片按 ID 顺序加锁。
        if data.project_id is not None:
            await self.get_owned_project(db, user_id, data.project_id, lock=True)
        if data.source_project_id is not None:
            await self.get_owned_project(db, user_id, data.source_project_id)
        iccids = list(dict.fromkeys(value.strip() for value in data.iccids))
        valid = [value for value in iccids if re.fullmatch(r"[0-9A-Za-z]{10,30}", value)]
        cards = (await db.execute(select(IotCardModel).where(
            IotCardModel.iccid.in_(valid), IotCardModel.user_id == user_id,
            IotCardModel.is_deleted == 0,
        ).order_by(IotCardModel.id).with_for_update())).scalars().all()
        card_map = {card.iccid: card for card in cards}
        success, skipped, failed = [], [], []
        for iccid in iccids:
            card = card_map.get(iccid)
            error = None
            if not re.fullmatch(r"[0-9A-Za-z]{10,30}", iccid):
                error = "卡号格式错误，需为 10–30 位字母或数字"
            elif card is None:
                error = "卡片不存在或不属于当前账号"
            elif data.source_project_id is not None and card.project_id != data.source_project_id:
                error = "卡片已不在当前项目，请刷新后重试"
            elif data.source_ungrouped and card.project_id is not None:
                error = "卡片已被分组，请刷新后重试"
            if error:
                failed.append({"iccid": iccid, "error": error})
            elif card.project_id == data.project_id:
                skipped.append({"iccid": iccid, "message": "已在目标项目" if data.project_id else "已是未分组"})
            else:
                self.add_move_log(db, card, user_id, card.project_id, data.project_id, original_user_id)
                card.project_id = data.project_id
                success.append({"iccid": iccid})
        # 更新与审计在同一事务提交；提交失败不返回部分成功。
        await db.commit()
        return {
            "success_count": len(success), "skipped_count": len(skipped), "failed_count": len(failed),
            "success_list": success, "skipped_list": skipped, "failed_list": failed,
            "duplicate_count": len(data.iccids) - len(iccids),
        }

    async def reorder(self, db, user_id, project_ids):
        projects = (await db.execute(select(ProjectModel).where(
            ProjectModel.user_id == user_id, ProjectModel.is_deleted == 0,
        ).order_by(ProjectModel.id).with_for_update())).scalars().all()
        if len(set(project_ids)) != len(project_ids) or set(project_ids) != {p.id for p in projects}:
            raise BusinessException(code=409, msg="项目列表已变化，请刷新后重新排序")
        order = {project_id: index for index, project_id in enumerate(project_ids)}
        for project in projects:
            project.sort_order = order[project.id]
        await db.commit()

    async def delete(self, db, user_id, project_id, original_user_id=None):
        project = await self.get_owned_project(db, user_id, project_id, lock=True)
        cards = (await db.execute(select(IotCardModel).where(
            IotCardModel.project_id == project.id,
        ).order_by(IotCardModel.id).with_for_update())).scalars().all()
        for card in cards:
            self.add_move_log(db, card, user_id, project.id, None, original_user_id, "delete_project")
            card.project_id = None
        project.is_deleted = 1
        await db.commit()


project_service = ProjectService()
