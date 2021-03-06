import json
import requests
from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlparse, urlencode
from urllib.parse import urljoin
from http.client import RemoteDisconnected
from requests.exceptions import ConnectionError, HTTPError
from urllib3.exceptions import ProtocolError
import backoff

ENDPOINTS = {
    "profile": "/account/me",
    "stream": "/bot/game/stream/{}",
    "stream_event": "/api/stream/event",
    "game": "/bot/game/{}",
    "move": "/bot/game/{}/move/{}",
    "chat": "/bot/game/{}/chat",
    "abort": "/bot/game/{}/abort",
    "accept": "/challenge/{}/accept",
    "decline": "/challenge/{}/decline",
    "upgrade": "/bot/account/upgrade"
}

# docs: https://lichess.org/api
class Lichess():

    def __init__(self, token, url):
        self.header = self._get_header(token)
        self.baseUrl = url
        self.session = requests.Session()
        self.session.headers.update(self.header)

    def is_final(exception):
        return isinstance(exception, HTTPError) and exception.response.status_code < 500

    @backoff.on_exception(backoff.expo,
        (RemoteDisconnected, ConnectionError, ProtocolError, HTTPError),
        max_time=120,
        giveup=is_final)
    def api_get(self, path):
        url = urljoin(self.baseUrl, path)
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    @backoff.on_exception(backoff.expo,
        (RemoteDisconnected, ConnectionError, ProtocolError, HTTPError),
        max_time=20,
        giveup=is_final)
    def api_post(self, path, data=None):
        url = urljoin(self.baseUrl, path)
        response = self.session.post(url, data=data)
        response.raise_for_status()
        return response.json()

    def get_game(self, game_id):
        return self.api_get(ENDPOINTS["game"].format(game_id))

    def upgrade_to_bot_account(self):
        return self.api_post(ENDPOINTS["upgrade"])

    def make_move(self, game_id, move):
        return self.api_post(ENDPOINTS["move"].format(game_id, move))

    def chat(self, game_id, room, text):
        payload = {'room': room, 'text': text}
        return self.api_post(ENDPOINTS["chat"].format(game_id), data=payload)

    def abort(self, game_id):
        return self.api_post(ENDPOINTS["abort"].format(game_id))

    def get_event_stream(self):
        url = urljoin(self.baseUrl, ENDPOINTS["stream_event"])
        return requests.get(url, headers=self.header, stream=True)

    def get_game_stream(self, game_id):
        url = urljoin(self.baseUrl, ENDPOINTS["stream"].format(game_id))
        return requests.get(url, headers=self.header, stream=True)

    def accept_challenge(self, challenge_id):
        return self.api_post(ENDPOINTS["accept"].format(challenge_id))

    def decline_challenge(self, challenge_id):
        return self.api_post(ENDPOINTS["decline"].format(challenge_id))

    def get_profile(self):
        return self.api_get(ENDPOINTS["profile"])

    def _get_header(self, token):
        return {
            "Authorization": "Bearer {}".format(token)
        }
