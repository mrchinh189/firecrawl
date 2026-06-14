# -*- coding: utf-8 -*-
"""scheduler.py — bộ lập lịch cho self-host bằng Docker (thay GitHub Actions cron).
Chạy run_pipeline 1 lần khi khởi động + theo lịch SCHEDULE_CRON. Dùng trong service 'pipeline'."""
import os
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent))


def main():
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    import run_pipeline

    cron = os.getenv("SCHEDULE_CRON", "0 2 * * 3")          # mặc định 02:00 UTC thứ Tư
    tz = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")

    print(f"[scheduler] chạy ngay 1 lần rồi theo lịch '{cron}' ({tz})")
    try:
        run_pipeline.run()
    except Exception as e:  # noqa: BLE001
        print(f"[scheduler] lần chạy đầu lỗi: {e}")

    sched = BlockingScheduler(timezone=tz)
    sched.add_job(run_pipeline.run, CronTrigger.from_crontab(cron, timezone=tz),
                  id="pipeline", replace_existing=True)
    sched.start()


if __name__ == "__main__":
    main()
