import os
from pathlib import Path

from dotenv import load_dotenv

from libs.handler.telegram_handler import TelegramHandler
from libs.utils.file_path import LOG_PATH
from libs.utils.logger import log

load_dotenv()

TELEGRAM_ADMIN_ID = os.environ.get("telegram_admin_id")


def send_daily_log():
    """Send Daily Log to Telegram Admin"""

    filenames = os.listdir(LOG_PATH)

    for filename in filenames:
        log_path = Path(LOG_PATH, filename)
        TelegramHandler().send_document(
            TELEGRAM_ADMIN_ID, log_path, "[Daily Log] " + filename
        )
        log_path.unlink()


def send_exception_log(e):
    """Send Exception Log to Telegram Admin

    Args:
        `e`: Exception
    """
    log("=" * 80)
    log("=" * 80)

    filename = log("[main]", e, return_filename=True)

    log("=" * 80)
    log("=" * 80)

    log_path = Path(LOG_PATH, filename)
    TelegramHandler().send_document(
        TELEGRAM_ADMIN_ID, log_path, "[Exception] " + filename
    )


def find_raw_content_by_user_id(owner_id, plurks):
    """Find raw content by user id

    Args:
        `owner_id`: User id.
        `plurks`: Plurk results.

    Returns:
        Raw content list.
    """

    raw_contents = []
    for plurk in plurks:
        if plurk["owner_id"] == int(owner_id):
            raw_contents.append(plurk["content_raw"])

    return raw_contents


def find_plurk_id_by_user_id(owner_id, plurks):
    """Find plurk id by user id

    Args:
        `owner_id`: User id.
        `plurks`: Plurk results.

    Returns:
        Plurk id list.
    """

    plurk_ids = []
    for plurk in plurks:
        if plurk["owner_id"] == int(owner_id):
            plurk_ids.append(plurk["plurk_id"])

    return plurk_ids
