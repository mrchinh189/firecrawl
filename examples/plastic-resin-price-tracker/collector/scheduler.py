"""Lap lich chay thu thap gia (mac dinh: 07:00 thu Hai hang tuan)."""
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from run import run_once

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("scheduler")


def main() -> None:
    if config.RUN_ON_START:
        log.info("RUN_ON_START=true -> chay ngay mot lan")
        try:
            run_once()
        except Exception:  # noqa: BLE001
            log.exception("Loi khi chay luc khoi dong")

    scheduler = BackgroundScheduler(timezone=config.SCHEDULE_TZ)
    scheduler.add_job(
        run_once,
        CronTrigger(
            day_of_week=config.SCHEDULE_DAY_OF_WEEK,
            hour=config.SCHEDULE_HOUR,
            minute=config.SCHEDULE_MINUTE,
        ),
        id="weekly_collection",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    log.info(
        "Da lap lich: %s %02d:%02d (%s)",
        config.SCHEDULE_DAY_OF_WEEK,
        config.SCHEDULE_HOUR,
        config.SCHEDULE_MINUTE,
        config.SCHEDULE_TZ,
    )
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
