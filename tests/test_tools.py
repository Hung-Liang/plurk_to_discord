import json

from libs.utils import tools


def make_plurk(plurk_id, owner_id=1, content="hi"):
    return {"plurk_id": plurk_id, "owner_id": owner_id, "content_raw": content}


def test_find_new_plurks_filters_owner_and_notified():
    plurks = [
        make_plurk(3),
        make_plurk(1),
        make_plurk(2, owner_id=99),
        make_plurk(4),
        make_plurk(3),
    ]

    result = tools.find_new_plurks("1", plurks, {"4": "old"})

    assert [plurk["plurk_id"] for plurk in result] == [1, 3]


def test_mark_notified_appends_to_ignore_json(tmp_path):
    path = tmp_path / "group.json"

    tools.mark_notified(path, 1, "a")
    tools.mark_notified(path, 2, "b")

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "1": "a",
        "2": "b",
    }
    assert not (tmp_path / "group.json.tmp").exists()


def test_load_ignore_json_trims_old_entries(tmp_path):
    path = tmp_path / "group.json"
    tools.save_json(path, {str(i): "x" for i in range(101)})

    ignore_list = tools.load_ignore_json(path)

    assert len(ignore_list) == 50
    assert "100" in ignore_list
    assert "0" not in ignore_list


def test_load_ignore_json_missing_file(tmp_path):
    assert tools.load_ignore_json(tmp_path / "missing.json") == {}


def test_get_message_escapes_html_only_for_telegram():
    content = "a < b & c"

    assert tools.get_message("telegram", content) == "a &lt; b &amp; c"
    assert tools.get_message("discord", content) == content


def test_send_daily_log_skips_today_and_keeps_unsent(isolate, monkeypatch):
    log_path = isolate / "log"
    today = tools.get_log_filename()
    for name in (today, "2000-01-01.log", "2000-01-02.log"):
        (log_path / name).write_text("x", encoding="utf-8")

    sent_names = []

    class FakeTelegram:
        def send_document(self, cid, path, filename):
            sent_names.append(path.name)
            return path.name == "2000-01-01.log", {}

    monkeypatch.setattr(tools, "TelegramHandler", FakeTelegram)

    tools.send_daily_log()

    assert sent_names == ["2000-01-01.log", "2000-01-02.log"]
    assert sorted(p.name for p in log_path.iterdir()) == [
        "2000-01-02.log",
        today,
    ]


def test_format_exception_message_fits_telegram_limit():
    message = tools.format_exception_message("<x>" * 5000 + "END")

    assert len(message) <= tools.TELEGRAM_MESSAGE_LIMIT
    assert message.endswith("END</pre>")
    assert "&lt;x&gt;" in message
