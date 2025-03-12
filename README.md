# plurk to discord

This is a simple script to re-post your plurk to discord or telegram.

## Usage

1. Create app on plurk and get the API key and secret.
2. Get discord webhook URL.
3. Create a file named `config.py` and fill in the following content:

```python
groups = {
    "group1": {
        "interval": 5,
        "owner_id": "",
        "notifier_types": {
            "telegram": {
                "recipient_ids": [],
            },
            "discord": {
                "webhook_urls": [],
            },
        },
    },
}
```

- `interval`: The interval of checking new plurks in minutes.
- `owner_id`: Your plurk user id.
- `recipient_ids`: The telegram user ids to notify.
- `webhook_urls`: The discord webhook URLs to notify.

4. Create a file named `.env` and fill in the following content:

```shell
bot_token=""

plurk_consumer_secret=""
plurk_consumer_key=""
plurk_access_token=""
plurk_access_token_secret=""
```

- `bot_token`: The telegram bot token.
- `plurk_consumer_secret`: The plurk consumer secret.
- `plurk_consumer_key`: The plurk consumer key.
- `plurk_access_token`: The plurk access token.
- `plurk_access_token_secret`: The plurk access token secret.

5. Run the script.

```shell
pip install -r requirements.txt
python main.py
```

## Support me

<a href="https://www.buymeacoffee.com/hungliang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
