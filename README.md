# plurk to discord

This is a simple script to re-post your plurk to discord or telegram.

## Usage

1. Create app on plurk and get the API key and secret.
2. Get discord webhook URL.
3. Create `config/config.py` (copy `config/config.example.py`) and fill in the following content:

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
  - Use a value that divides 60 (e.g. 1, 2, 3, 5, 10), otherwise polling gaps will be uneven.
- `owner_id`: Your plurk user id.
- `recipient_ids`: The telegram user ids to notify.
- `webhook_urls`: The discord webhook URLs to notify.
- For local testing, create `config/dev_config.py` with the same format and set `APP_ENV="dev"` in `.env`.
- Run `python main.py --check-config` to validate the config without starting the service.

4. Create a file named `.env` and fill in the following content:

```shell
telegram_admin_id=""

bot_token=""

plurk_consumer_secret=""
plurk_consumer_key=""
plurk_access_token=""
plurk_access_token_secret=""

APP_ENV=""
```

- `telegram_admin_id`: The telegram id that receives errors and daily logs.
- `bot_token`: The telegram bot token.
- `plurk_consumer_secret`: The plurk consumer secret.
- `plurk_consumer_key`: The plurk consumer key.
- `plurk_access_token`: The plurk access token.
- `plurk_access_token_secret`: The plurk access token secret.
- `APP_ENV`: Set to `dev` to load `config/dev_config.py`, any other value loads `config/config.py`.

5. Run the script.

```shell
uv sync --no-dev
uv run main.py
```

- You need to have [uv](https://docs.astral.sh/uv/) installed; dependencies are installed from `uv.lock`.

- Notified plurk ids are saved in `asset/ignore/`, so a plurk is only sent once.

## Run with Docker

- Put `.env` in the root folder and `config.py` in the `config` folder, then run `scripts/deploy.sh`.
  - It tags the current image as `plurk_to_discord:prev`, builds a new one, checks the config, and restarts the container.
- `config/`, `asset/` and `log/` are mounted from the host, so they survive rebuilds.
- After changing the config, run `docker compose restart notifier`.
- Rollback: `docker tag plurk_to_discord:prev plurk_to_discord:latest && docker compose up -d`.

## Running tests

- Tests run in a local [uv](https://docs.astral.sh/uv/) virtual environment, with the same Python version and locked dependencies as the Docker image.
- To upgrade dependencies, run `uv lock --upgrade` and commit the updated `uv.lock`.

```bash
uv sync
uv run pytest
```

## Support me

<a href="https://www.buymeacoffee.com/hungliang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
