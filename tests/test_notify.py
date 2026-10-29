import json

import pytest
import requests

from libs.utils import notify

GROUP = {
    "interval": 5,
    "owner_id": "1",
    "notifier_types": {"discord": {"webhook_urls": ["a", "b"]}},
}


class FakePlurk:
    def __init__(self, plurks):
        self.plurks = plurks
        self.minutes = None
        self.liked = []
        self.replurked = []

    def find_plurk(self, minutes=None):
        self.minutes = minutes
        return self.plurks

    def like_plurk(self, plurk_id):
        self.liked.append(plurk_id)
        return True

    def replurk_plurk(self, plurk_id):
        self.replurked.append(plurk_id)
        return True


@pytest.fixture
def exceptions(monkeypatch):
    sent = []
    monkeypatch.setattr(notify, "send_exception_log", sent.append)
    return sent


def use_plurk(monkeypatch, plurks):
    fake = FakePlurk(plurks)
    monkeypatch.setattr(notify, "PlurkHandler", lambda: fake)
    return fake


def plurk(plurk_id, owner_id=1):
    return {
        "plurk_id": plurk_id,
        "owner_id": owner_id,
        "content_raw": f"content {plurk_id}",
    }


def test_delivered_plurk_is_marked_liked_and_replurked(
    monkeypatch, isolate, exceptions
):
    fake = use_plurk(monkeypatch, [plurk(1), plurk(2, owner_id=9)])
    sent = []
    monkeypatch.setattr(
        notify,
        "send_notify_by_type",
        lambda notifier_type, data, content: sent.append(content) or [True],
    )

    notify.send_plurk_updates("g", GROUP)
    notify.send_plurk_updates("g", GROUP)

    assert fake.minutes == 10
    assert sent == ["content 1"]
    assert fake.liked == [1]
    assert fake.replurked == [1]
    ignore = json.loads((isolate / "ignore" / "g.json").read_text("utf-8"))
    assert ignore == {"1": "content 1"}


def test_all_recipients_failed_retries_next_run(
    monkeypatch, isolate, exceptions
):
    fake = use_plurk(monkeypatch, [plurk(1)])
    monkeypatch.setattr(
        notify, "send_notify_by_type", lambda *args: [False, False]
    )

    notify.send_plurk_updates("g", GROUP)

    assert fake.liked == []
    assert not (isolate / "ignore" / "g.json").exists()


def test_polling_failure_is_reported(monkeypatch, exceptions):
    use_plurk(monkeypatch, None)

    notify.send_plurk_updates("g", GROUP)

    assert exceptions == ["[main] Plurk polling failed for g"]


class FakeHandler:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []
        self.last_status_code = None
        self.last_retry_after = None

    def send_message(self, user, message):
        self.calls.append(user)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        self.last_status_code, self.last_retry_after = result
        return self.last_status_code == 204


def test_rate_limited_message_is_retried(monkeypatch, exceptions):
    handler = FakeHandler([(429, 1), (204, None), (204, None)])
    monkeypatch.setattr(notify, "DiscordHandler", lambda: handler)
    slept = []
    monkeypatch.setattr(notify.time, "sleep", slept.append)

    delivered = notify.send_notify_by_type(
        "discord", {"webhook_urls": ["a", "b"]}, "hi"
    )

    assert delivered == [True, True]
    assert handler.calls == ["a", "a", "b"]
    assert slept == [1]
    assert exceptions == []


def test_one_recipient_error_does_not_block_others(monkeypatch, exceptions):
    handler = FakeHandler(
        [requests.ConnectionError("https://secret/url"), (204, None)]
    )
    monkeypatch.setattr(notify, "DiscordHandler", lambda: handler)

    delivered = notify.send_notify_by_type(
        "discord", {"webhook_urls": ["a", "b"]}, "hi"
    )

    assert delivered == [False, True]
    assert len(exceptions) == 1
    assert "ConnectionError" in exceptions[0]
    assert "secret" not in exceptions[0]


def test_read_timeout_counts_as_delivered(monkeypatch, exceptions):
    handler = FakeHandler([requests.ReadTimeout("https://secret/url")])
    monkeypatch.setattr(notify, "DiscordHandler", lambda: handler)

    delivered = notify.send_notify_by_type(
        "discord", {"webhook_urls": ["a"]}, "hi"
    )

    assert delivered == [True]
    assert handler.calls == ["a"]
    assert len(exceptions) == 1
    assert "ReadTimeout" in exceptions[0]
    assert "secret" not in exceptions[0]


def test_telegram_reads_recipient_ids(monkeypatch, exceptions):
    handler = FakeHandler([(204, None)])
    monkeypatch.setattr(notify, "TelegramHandler", lambda: handler)

    notify.send_notify_by_type("telegram", {"recipient_ids": ["42"]}, "a<b")

    assert handler.calls == ["42"]
