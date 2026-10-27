import pytest

from conftest import FakeResponse
from libs.handler import plurk_handler, telegram_handler
from libs.handler.plurk_handler import PlurkHandler
from libs.handler.telegram_handler import TelegramHandler


def test_missing_plurk_credentials_raise(monkeypatch):
    monkeypatch.delenv("plurk_access_token")

    with pytest.raises(ValueError, match="plurk_access_token"):
        PlurkHandler()


def test_call_api_signs_and_uses_timeout(monkeypatch):
    calls = []

    def fake_post(url, headers, data, timeout):
        calls.append((url, headers, data, timeout))
        return FakeResponse(200, {"success_text": "ok"})

    monkeypatch.setattr(plurk_handler.requests, "post", fake_post)

    assert PlurkHandler().like_plurk(1) is True

    url, headers, data, timeout = calls[0]
    assert url == "https://www.plurk.com/APP/Timeline/favoritePlurks"
    assert headers["Authorization"].startswith("OAuth ")
    assert data == {"ids": "[1]"}
    assert timeout == plurk_handler.REQUEST_TIMEOUT


def test_call_api_returns_none_on_error(monkeypatch):
    monkeypatch.setattr(
        plurk_handler.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(400, text="bad"),
    )

    handler = PlurkHandler()

    assert handler.find_plurk(minutes=5) is None
    assert handler.like_plurk(1) is False
    assert handler.replurk_plurk(1) is False


def posted(second):
    return f"Tue, 27 Oct 2026 10:00:{second:02d} GMT"


def test_find_plurk_pages_past_limit(monkeypatch):
    monkeypatch.setattr(plurk_handler, "POLL_LIMIT", 2)
    monkeypatch.setattr(
        PlurkHandler,
        "get_offset",
        lambda self, *args: "2026-10-27T09:55:00",
    )
    pages = [
        {"plurks": [{"plurk_id": 1, "posted": posted(1)},
                    {"plurk_id": 2, "posted": posted(2)}]},
        {"plurks": [{"plurk_id": 3, "posted": posted(3)}]},
    ]
    offsets = []

    def fake_call_api(self, path, options):
        offsets.append(options["offset"])
        assert options["limit"] == 2
        return pages.pop(0)

    monkeypatch.setattr(PlurkHandler, "call_api", fake_call_api)

    plurks = PlurkHandler().find_plurk(minutes=5)

    assert [plurk["plurk_id"] for plurk in plurks] == [1, 2, 3]
    assert offsets[1] == "2026-10-27T10:00:02"


def test_find_plurk_stops_when_offset_does_not_advance(monkeypatch):
    monkeypatch.setattr(plurk_handler, "POLL_LIMIT", 1)
    monkeypatch.setattr(
        PlurkHandler,
        "get_offset",
        lambda self, *args: "2026-10-27T10:00:05",
    )
    calls = []

    def fake_call_api(self, path, options):
        calls.append(options["offset"])
        return {"plurks": [{"plurk_id": 1, "posted": posted(1)}]}

    monkeypatch.setattr(PlurkHandler, "call_api", fake_call_api)

    assert len(PlurkHandler().find_plurk(minutes=5)) == 1
    assert len(calls) == 1


def test_telegram_posts_message_as_form_data(monkeypatch):
    calls = []

    def fake_post(url, data, timeout):
        calls.append((url, data, timeout))
        return FakeResponse(
            429, {"parameters": {"retry_after": 3}}, text="too many"
        )

    monkeypatch.setattr(telegram_handler.requests, "post", fake_post)
    handler = TelegramHandler()

    assert handler.send_message("42", "a & b #c") is False
    assert calls[0][1]["text"] == "a & b #c"
    assert "a & b" not in calls[0][0]
    assert handler.last_status_code == 429
    assert handler.last_retry_after == 3
