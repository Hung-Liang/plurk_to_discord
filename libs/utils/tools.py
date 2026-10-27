import html
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from libs.handler.telegram_handler import TelegramHandler
from libs.utils.file_path import LOG_PATH
from libs.utils.logger import get_log_filename, log

load_dotenv()

TELEGRAM_ADMIN_ID = os.environ.get("telegram_admin_id")

TELEGRAM_MESSAGE_LIMIT = 4096


def send_daily_log():
    """Send Daily Log to Telegram Admin"""

    filenames = sorted(os.listdir(LOG_PATH))
    current_filename = get_log_filename()

    for filename in filenames:
        # Other jobs may still be writing to today's log
        if filename == current_filename:
            continue

        log_path = Path(LOG_PATH, filename)
        sent, _ = TelegramHandler().send_document(
            TELEGRAM_ADMIN_ID, log_path, "[Daily Log] " + filename
        )

        # Keep the file so it will be retried on the next run
        if sent:
            log_path.unlink()


def send_exception_log(e):
    """Send Exception Log to Telegram Admin

    Args:
        `e`: Exception
    """
    log("=" * 80)
    log("=" * 80)

    log("[main]", e)

    log("=" * 80)
    log("=" * 80)

    # Upload failure must not abort the caller's notification job
    try:
        TelegramHandler().send_message(
            TELEGRAM_ADMIN_ID, format_exception_message(e)
        )
    except requests.RequestException as err:
        log("[main]", f"Send exception log failed: {err!r}")


def format_exception_message(e):
    """Format an exception as a Telegram HTML message within size limit.

    Args:
        `e`: Exception

    Returns:
        A Telegram HTML message
    """
    header = "<b>[Exception]</b>\n"
    text = str(e)

    # Keep the tail, where a traceback shows the actual error
    while True:
        body = html.escape(text, quote=False)
        if len(header) + len(body) + len("<pre></pre>") <= (
            TELEGRAM_MESSAGE_LIMIT
        ):
            return f"{header}<pre>{body}</pre>"
        text = "...\n" + text[-(len(text) * 9 // 10):]


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
