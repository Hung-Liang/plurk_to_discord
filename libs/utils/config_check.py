import os

from libs.handler.plurk_handler import CREDENTIAL_KEYS

NOTIFIER_KEYS = {
    "telegram": ("recipient_ids",),
    "discord": ("webhook_urls",),
}


def check_env():
    """Check the .env values the service cannot start without.

    Returns:
        A list of error messages.
    """
    return [
        f"{key} is missing in .env"
        for key in CREDENTIAL_KEYS
        if not os.environ.get(key)
    ]


def check_groups(groups):
    """Check the groups in the config file.

    Args:
        `groups`: Groups dict from the config file

    Returns:
        (errors, warnings): Lists of messages. Errors must stop startup.
    """
    errors = []
    warnings = []

    if not isinstance(groups, dict):
        return ["groups must be a dict"], warnings

    for group, config in groups.items():
        where = f"groups[{group!r}]"

        if not isinstance(config, dict):
            errors.append(f"{where} must be a dict")
            continue

        interval = config.get("interval")
        if (
            not isinstance(interval, int)
            or isinstance(interval, bool)
            or interval <= 0
        ):
            errors.append(f"{where}['interval'] must be a positive int")
        elif 60 % interval != 0:
            # Cron restarts at minute 0, so the last gap of each hour is short
            warnings.append(
                f"{where}['interval'] = {interval} does not divide 60,"
                " polling gaps will be uneven"
            )

        if not str(config.get("owner_id", "")).isdigit():
            errors.append(f"{where}['owner_id'] must be a plurk user id")

        errors += check_notifier_types(where, config.get("notifier_types"))

    return errors, warnings


def check_notifier_types(where, notifier_types):
    if not isinstance(notifier_types, dict):
        return [f"{where}['notifier_types'] must be a dict"]

    errors = []
    for notifier_type, data in notifier_types.items():
        if notifier_type not in NOTIFIER_KEYS:
            errors.append(
                f"{where}['notifier_types'] has unknown type"
                f" {notifier_type!r}"
            )
            continue

        if not isinstance(data, dict):
            errors.append(
                f"{where}['notifier_types'][{notifier_type!r}] must be a dict"
            )
            continue

        for key in NOTIFIER_KEYS[notifier_type]:
            if not isinstance(data.get(key), list):
                errors.append(
                    f"{where}['notifier_types'][{notifier_type!r}][{key!r}]"
                    " must be a list"
                )

    return errors
