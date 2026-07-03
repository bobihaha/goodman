"""
定时任务调度器
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.database import AsyncSessionLocal
from app.services.sync_service import sync_service
from app.services.card_expiry_reminder_service import card_expiry_reminder_service
from app.crud.supplier_crud import supplier_crud
from app.utils.timezone import CHINA_TZ
from app.utils.logger import logger

scheduler = AsyncIOScheduler()


async def sync_supplier_usage(supplier_id: int = None):
    """同步供应商流量"""
    async with AsyncSessionLocal() as db:
        try:
            result = await sync_service.sync_usage(
                db=db,
                supplier_id=supplier_id,
                iccid_list=None,
                triggered_by=None
            )
            logger.info(f"定时同步完成 - 供应商ID: {supplier_id}, 成功: {result['success']}, 失败: {result['failed']}")
        except Exception as e:
            logger.error(f"定时同步失败 - 供应商ID: {supplier_id}, 错误: {str(e)}")


async def send_card_expiry_reminders():
    """发送本月到期卡邮件提醒"""
    async with AsyncSessionLocal() as db:
        try:
            result = await card_expiry_reminder_service.send_monthly_expiry_reminders(db)
            logger.info(
                "到期卡邮件提醒完成 - 用户: %s, 卡片: %s, 已发送: %s, 跳过: %s, 失败: %s",
                result["users"],
                result["cards"],
                result["sent"],
                result["skipped"],
                result["failed"],
            )
        except Exception as e:
            logger.error(f"到期卡邮件提醒失败 - 错误: {str(e)}")


async def load_sync_tasks():
    """加载所有供应商的同步任务"""
    async with AsyncSessionLocal() as db:
        suppliers = await supplier_crud.get_all_enabled(db)

        for supplier in suppliers:
            if supplier.sync_interval and supplier.sync_interval > 0:
                # 根据同步间隔创建cron表达式
                interval = supplier.sync_interval
                if interval >= 60:
                    # 转换为小时
                    hours = interval // 60
                    if hours >= 24:
                        logger.warning(f"供应商 {supplier.name} 的同步间隔过大({interval}分钟)，跳过")
                        continue
                    cron_expr = f"0 */{hours} * * *"
                else:
                    cron_expr = f"*/{interval} * * * *"

                # 添加定时任务
                scheduler.add_job(
                    sync_supplier_usage,
                    CronTrigger.from_crontab(cron_expr),
                    args=[supplier.id],
                    id=f"sync_supplier_{supplier.id}",
                    replace_existing=True
                )
                logger.info(f"已加载同步任务 - 供应商: {supplier.name}, 间隔: {supplier.sync_interval}分钟")


def start_scheduler():
    """启动调度器"""
    scheduler.add_job(
        send_card_expiry_reminders,
        CronTrigger(day="10,15", hour=9, minute=0, timezone=CHINA_TZ),
        id="card_expiry_reminders",
        replace_existing=True
    )
    scheduler.start()
    logger.info("✅ 定时任务调度器已启动")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown()
    logger.info("✅ 定时任务调度器已关闭")
