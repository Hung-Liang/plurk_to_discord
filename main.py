import pytz
from apscheduler.schedulers.blocking import BlockingScheduler

from libs.config import groups
from libs.utils.notify import send_plurk_updates
from libs.utils.tools import send_daily_log


def get_interval_str(interval):
    return '0-59/{}'.format(interval)


timezone = pytz.timezone('Asia/Taipei')

scheduler = BlockingScheduler(timezone=timezone)

for group_name, group in groups.items():
    interval = group['interval']
    scheduler.add_job(
        send_plurk_updates,
        'cron',
        minute=get_interval_str(interval),
        args=[group, interval],
    )

scheduler.add_job(
    send_daily_log,
    'cron',
    hour=0,
    minute=0,
)

scheduler.start()
