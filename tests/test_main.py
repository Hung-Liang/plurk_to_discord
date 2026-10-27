import pytest

import main
from libs.utils import config_loader
from libs.utils.config_check import check_groups

VALID_GROUP = {
    "interval": 5,
    "owner_id": "123",
    "notifier_types": {
        "telegram": {"recipient_ids": []},
        "discord": {"webhook_urls": []},
    },
}


class FakeScheduler:
    def __init__(self):
        self.jobs = []

    def add_job(self, func, trigger, **kwargs):
        self.jobs.append((func, trigger, kwargs))


def test_group_jobs_use_whole_minute_cron():
    scheduler = FakeScheduler()

    main.schedule_group_jobs(scheduler, {"g": VALID_GROUP})

    func, trigger, kwargs = scheduler.jobs[0]
    assert func is main.send_plurk_updates
    assert trigger == "cron"
    assert kwargs == {"minute": "0-59/5", "args": ["g", VALID_GROUP]}


def test_check_groups_accepts_valid_group():
    assert check_groups({"g": VALID_GROUP}) == ([], [])


@pytest.mark.parametrize(
    "override, message",
    [
        ({"interval": 0}, "'interval'] must be a positive int"),
        ({"owner_id": ""}, "'owner_id'] must be a plurk user id"),
        ({"notifier_types": {"line": {}}}, "unknown type 'line'"),
        (
            {"notifier_types": {"telegram": {"recipient_id": []}}},
            "'recipient_ids'] must be a list",
        ),
    ],
)
def test_check_groups_reports_errors(override, message):
    errors, _ = check_groups({"g": {**VALID_GROUP, **override}})

    assert any(message in error for error in errors)


def test_check_groups_warns_on_uneven_interval():
    _, warnings = check_groups({"g": {**VALID_GROUP, "interval": 7}})

    assert "does not divide 60" in warnings[0]


def test_check_config_requires_plurk_credentials(monkeypatch):
    monkeypatch.delenv("plurk_consumer_key")

    with pytest.raises(ValueError, match="plurk_consumer_key"):
        main.check_config({"g": VALID_GROUP})


def test_job_error_sends_exception_text_only(monkeypatch):
    logged, sent = [], []
    monkeypatch.setattr(main, "log", lambda *m, **kw: logged.append(m))
    monkeypatch.setattr(main, "send_exception_log", sent.append)

    class Event:
        job_id = "abc"
        exception = ConnectionError("Connection reset")
        traceback = 'File "x.py", line 1, in f\n'

    main.on_job_error(Event())

    assert sent == [
        "[scheduler] Job abc failed\nConnectionError: Connection reset"
    ]
    assert 'File "x.py"' in logged[0][1]


def test_check_config_flag_exits_without_starting(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("must not start the service")

    monkeypatch.setattr(main, "load_config", lambda: {"g": VALID_GROUP})
    monkeypatch.setattr(main, "send_service_start_notification", fail)
    monkeypatch.setattr(main, "BlockingScheduler", fail)

    assert main.main(["--check-config"]) == 0


def test_check_config_flag_fails_on_missing_config(monkeypatch, tmp_path):
    monkeypatch.setattr(
        main,
        "load_config",
        lambda: config_loader.load_config(tmp_path / "missing.py"),
    )

    assert main.main(["--check-config"]) == 1


def test_load_config_uses_dev_config(monkeypatch, tmp_path):
    dev_config = tmp_path / "dev_config.py"
    dev_config.write_text("groups = {'dev': {}}\n", encoding="utf-8")
    monkeypatch.setattr(config_loader, "DEV_CONFIG_PATH", dev_config)
    monkeypatch.setenv("APP_ENV", "dev")

    assert config_loader.load_config() == {"dev": {}}
