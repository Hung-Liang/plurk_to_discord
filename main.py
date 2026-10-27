from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.blocking import BlockingScheduler

from libs.config import groups
from libs.utils.logger import TIMEZONE, log
from libs.utils.notify import send_plurk_updates
from libs.utils.tools import (
    send_daily_log,
    send_exception_log,
    send_service_start_notification,
)


def schedule_group_jobs(scheduler, groups):
    for group_name, group in groups.items():
        interval = group['interval']
        scheduler.add_job(
            send_plurk_updates,
            'cron',
            minute=f'0-59/{interval}',
            args=[group_name, group],
        )


def on_job_error(event):
    # Keep the traceback in the local log; Telegram gets the exception text only
    log("[scheduler]", f"Job {event.job_id} traceback\n{event.traceback}")
    send_exception_log(
        f"[scheduler] Job {event.job_id} failed\n"
        f"{type(event.exception).__name__}: {event.exception}"
    )


def main():
    send_service_start_notification()

    # Default misfire grace is 1s, so a slightly late wakeup skips the run
    scheduler = BlockingScheduler(
        timezone=TIMEZONE,
        job_defaults={"misfire_grace_time": 30, "coalesce": True},
    )
    scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)

    schedule_group_jobs(scheduler, groups)

    scheduler.add_job(send_daily_log, 'cron', hour=0, minute=0)

    scheduler.start()


if __name__ == "__main__":
    main()
