import datetime
import json
import os

import requests
from dotenv import load_dotenv
from oauth2 import Token
from plurk_oauth import PlurkAPI

from libs.utils.logger import log

load_dotenv()

REQUEST_TIMEOUT = 10

CREDENTIAL_KEYS = (
    "plurk_consumer_key",
    "plurk_consumer_secret",
    "plurk_access_token",
    "plurk_access_token_secret",
)


class PlurkHandler:
    def __init__(self):
        missing = [key for key in CREDENTIAL_KEYS if not os.environ.get(key)]
        # plurk_oauth falls back to input() prompts, which hang without a tty
        if missing:
            raise ValueError(
                "Missing plurk credentials in .env: " + ", ".join(missing)
            )

        consumer_key = os.environ.get("plurk_consumer_key")
        consumer_secret = os.environ.get("plurk_consumer_secret")
        access_token = os.environ.get("plurk_access_token")
        access_token_secret = os.environ.get("plurk_access_token_secret")

        self.plurk = PlurkAPI(consumer_key, consumer_secret)
        self.plurk.authorize(access_token, access_token_secret)

    def call_api(self, path, options):
        """Call plurk API.

        Args:
            `path`: API path.
            `options`: API parameters.

        Returns:
            Response json if success, None if fail.
        """

        # plurk_oauth posts without a timeout, so only use it for signing
        oauth = self.plurk._oauth
        oauth.token = Token(
            oauth.oauth_token["oauth_token"],
            oauth.oauth_token["oauth_token_secret"],
        )
        url = oauth.base_url + path
        req = oauth._make_request(url, options)

        res = requests.post(
            url,
            headers=req.to_header(),
            data=options,
            timeout=REQUEST_TIMEOUT,
        )

        if res.status_code != 200:
            log('[plurk_lib]', f'{path}: {res.status_code} {res.text}')
            return None

        return res.json()

    def get_offset(self, hours=None, minutes=None, seconds=None):
        """Get offset for plurk API

        Args:
            `hours`: Hours to find.
            `minutes`: Minutes to find.
            `seconds`: Seconds to find.

        Returns:
            Offset string.
        """

        offset = datetime.datetime.now(datetime.timezone.utc)

        if hours is not None:
            offset -= datetime.timedelta(hours=hours)
        elif minutes is not None:
            offset -= datetime.timedelta(minutes=minutes)
        elif seconds is not None:
            offset -= datetime.timedelta(seconds=seconds)

        offset = offset.strftime("%Y-%m-%dT%H:%M:%S")

        return offset

    def find_plurk(self, hours=None, minutes=None, seconds=None):
        """Find plurk by time

        Args:
            `hours`: Hours to find.
            `minutes`: Minutes to find.
            `seconds`: Seconds to find.

        Returns:
            Plurk content if success, None if fail.
        """

        offset = self.get_offset(hours, minutes, seconds)

        result = self.call_api(
            "/APP/Polling/getPlurks",
            options={"offset": offset, "qualifier": ':'},
        )

        return result

    def get_plurk(self, plurk_id):
        """Get plurk by id

        Args:
            `plurk_id`: Plurk id.

        Returns:
            Plurk content if success, None if fail.
        """

        result = self.call_api(
            "/APP/Timeline/getPlurk",
            options={"plurk_id": plurk_id},
        )

        return result

    def like_plurk(self, plurk_id):
        """Favorite plurk by id

        Args:
            `plurk_id`: Plurk id.

        Returns:
            True if success, False if fail.
        """

        ids = json.dumps([plurk_id])

        result = self.call_api(
            "/APP/Timeline/favoritePlurks",
            options={"ids": ids},
        )

        if result and result.get("success_text") == 'ok':
            return True
        else:
            return False

    def replurk_plurk(self, plurk_id):
        """Replurk plurk by id

        Args:
            `plurk_id`: Plurk id.

        Returns:
            True if success, False if fail.
        """

        ids = json.dumps([plurk_id])

        result = self.call_api(
            "/APP/Timeline/replurk",
            options={"ids": ids},
        )

        if result and result.get("success"):
            return True
        else:
            return False
