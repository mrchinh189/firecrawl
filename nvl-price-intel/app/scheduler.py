"""Bộ lập lịch chạy pipeline định kỳ (APScheduler)."""
from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import Settings
from .logging_config import get_logger
from .pipeline import run_all_and_notify

logger = get_logger(__name__)


def build_scheduler(settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    trigger = CronTrigger.from_crontab(settings.schedule_cron, timezone=settings.timezone)

    async def _job() -> None:
        logger.info("⏰ Chạy pipeline theo lịch (%s)", settings.schedule_cron)
        await run_all_and_notify(settings)

    scheduler.add_job(_job, trigger, id="daily_price_update", replace_existing=True)
    logger.info(
        "Đã đăng ký lịch '%s' (%s) cho mã: %s",
        settings.schedule_cron,
        settings.timezone,
        ", ".join(settings.ticker_list),
    )
    return scheduler
