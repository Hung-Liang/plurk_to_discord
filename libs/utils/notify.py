import time
from pathlib import Path

import requests

from libs.handler.discord_handler import DiscordHandler
from libs.handler.plurk_handler import PlurkHandler
from libs.handler.telegram_handler import TelegramHandler
from libs.utils.file_path import IGNORE_PATH
from libs.utils.logger import log
from libs.utils.tools import (
    find_new_plurks,
    get_message,
    load_ignore_json,
    mark_notified,
    send_exception_log,
)

# Longest rate-limit wait we accept before giving up on a recipient
MAX_RETRY_AFTER = 30


def send_notify_by_type(notifier_type, data, content):
    """Send to every recipient of one notifier type.

    Returns:
        A list of bools, one per recipient, True if delivered.
    """

    def send_to_user(handler, message, user):
        if handler.send_message(user, message):
            return True

        status_code = handler.last_status_code

        if status_code == 429:
            retry_after = handler.last_retry_after
            if retry_after is not None and retry_after <= MAX_RETRY_AFTER:
                time.sleep(retry_after)
                if handler.send_message(user, message):
                    return True
            send_exception_log(
                f"[main] {notifier_type.capitalize()} Message Sent Failed"
                f" (429, retry_after={retry_after})"
            )
            return False

        send_exception_log(
            f"[main] {notifier_type.capitalize()} Message Sent Failed"
            f" ({status_code})"
        )
        return False

    message = get_message(notifier_type, content)

    if notifier_type == "telegram":
        users = data["recipient_ids"]
        handler = TelegramHandler()
    elif notifier_type == "discord":
        users = data["webhook_urls"]
        handler = DiscordHandler()
    else:
        raise ValueError(f"Unknown notifier_type: {notifier_type}")

    delivered = []
    for index, user in enumerate(users):
        # One unreachable recipient must not block the others
        try:
            delivered.append(send_to_user(handler, message, user))
        except requests.RequestException as err:
            # Only the error type: its message may contain the bot token
            # or webhook url
            send_exception_log(
                f"[main] {notifier_type.capitalize()} Message Sent Failed"
                f" (recipient #{index}, {type(err).__name__})"
            )
            delivered.append(False)
    return delivered


def send_plurk_updates(group, config):
    plurk = PlurkHandler()

    # Look back two intervals so a late run still covers the gap; plurks
    # already notified are skipped by the ignore json
    plurks = plurk.find_plurk(minutes=config["interval"] * 2)
    if plurks is None:
        send_exception_log(f"[main] Plurk polling failed for {group}")
        return

    ignore_json = Path(IGNORE_PATH, f"{group}.json")
    new_plurks = find_new_plurks(
        config["owner_id"], plurks, load_ignore_json(ignore_json)
    )

    log('[main]', f'{group}: {len(plurks)} plurks, {len(new_plurks)} new')

    for new_plurk in new_plurks:
        plurk_id = new_plurk["plurk_id"]
        content = new_plurk["content_raw"]
        log('[main]', f'Plurk {plurk_id}: {content}')

        delivered = []
        for notifier_type, data in config["notifier_types"].items():
            delivered += send_notify_by_type(notifier_type, data, content)

        # Retry next run only when every recipient failed
        if delivered and not any(delivered):
            log('[main]', f'All recipients failed, retry later: {plurk_id}')
            continue

        mark_notified(ignore_json, plurk_id, content)

        if not plurk.like_plurk(plurk_id):
            log('[main]', f'Like plurk failed: {plurk_id}')
        if not plurk.replurk_plurk(plurk_id):
            log('[main]', f'Replurk plurk failed: {plurk_id}')
