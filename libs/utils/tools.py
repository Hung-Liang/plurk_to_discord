import html
import json
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


def load_json(path):
    """Load Json from Select File

    Args:
        `path`: File path

    Returns:
        A Json Object of Select File
    """
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data


def save_json(path, data):
    """Save Json to Select File

    Args:
        `path`: File path
        `data`: Json data
    """
    # Write to a temp file then swap, so a crash never leaves a broken file
    tmp_path = Path(f"{path}.tmp")
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def load_ignore_json(json_path):
    """Load Ignore Json

    Returns:
        A dict of notified plurk ids
    """

    if not Path(json_path).exists():
        return {}

    ignore_list = load_json(json_path)

    if len(ignore_list) > 100:
        ignore_list = dict(list(ignore_list.items())[-50:])

    return ignore_list


def mark_notified(json_path, plurk_id, content):
    """Record a plurk in the ignore json so it is not sent again.

    Args:
        `json_path`: Ignore Json Path
        `plurk_id`: Plurk ID
        `content`: Plurk raw content
    """
    ignore_list = load_ignore_json(json_path)
    ignore_list[str(plurk_id)] = content
    save_json(json_path, ignore_list)


def find_new_plurks(owner_id, plurks, ignore_list):
    """Find the owner's plurks that were not notified yet.

    Args:
        `owner_id`: User id.
        `plurks`: Plurk results.
        `ignore_list`: Notified plurk ids.

    Returns:
        Plurk list, oldest first.
    """

    new_plurks = {}
    for plurk in plurks:
        plurk_id = str(plurk["plurk_id"])
        if plurk["owner_id"] != int(owner_id) or plurk_id in ignore_list:
            continue
        # Pages may overlap on the same second
        new_plurks[plurk_id] = plurk

    return sorted(new_plurks.values(), key=lambda plurk: plurk["plurk_id"])


def get_message(notifier_type, content):
    """Get Message for one notifier type

    Args:
        `notifier_type`: "telegram" or "discord"
        `content`: Plurk raw content

    Returns:
        A Message for the notifier type
    """
    if notifier_type == "telegram":
        return html.escape(content, quote=False)
    elif notifier_type == "discord":
        return content

    raise ValueError(f"Unknown notifier_type: {notifier_type}")
