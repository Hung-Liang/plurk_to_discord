from libs.handler.plurk_handler import PlurkHandler
from libs.handler.discord_handler import DiscordHandler
from libs.handler.telegram_handler import TelegramHandler
from libs.utils.logger import log
from libs.utils.tools import (
    find_plurk_id_by_user_id,
    find_raw_content_by_user_id,
    send_exception_log,
)


def send_notify_by_type(notifier_type, data, content):

    if notifier_type == "telegram":
        recipients_ids = data["recipient_id"]

        for cid in recipients_ids:
            sent = TelegramHandler().send_message(cid, content)
            if not sent:
                send_exception_log("[main] Telegram Message Sent Failed")

    elif notifier_type == "discord":
        webhook_urls = data["webhook_url"]

        for webhook_url in webhook_urls:
            sent = DiscordHandler(webhook_url).send_message(content)

            if not sent:
                send_exception_log("[main] Discord Message Sent Failed")


def send_plurk_updates(group, minutes=3):
    plurk = PlurkHandler()
    result = plurk.find_plurk(minutes=minutes)
    owner_id = group["owner_id"]
    contents = find_raw_content_by_user_id(owner_id, result['plurks'])

    log('[main]', 'Plurk Result: ', result)
    log('[main]', 'Plurk Contents: ', contents)

    notifier_types = group["notifier_types"]

    for content in contents:
        log('[main]', 'Plurk Content: ', content)
        for notifier_type, data in notifier_types.items():
            send_notify_by_type(notifier_type, data, content)

    plurk_ids = find_plurk_id_by_user_id(owner_id, result['plurks'])
    log('[main]', 'Plurk IDs: ', plurk_ids)

    for plurk_id in plurk_ids:
        plurk.like_plurk(plurk_id)
        plurk.replurk_plurk(plurk_id)
