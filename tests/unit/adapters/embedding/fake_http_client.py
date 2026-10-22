import json
from typing import Any

import requests

Outcome = requests.Response | Exception


def response(status_code: int = 200, payload: Any = None) -> requests.Response:
    built = requests.Response()
    built.status_code = status_code
    built._content = json.dumps(payload).encode()
    built.encoding = "utf-8"

    return built


class FakeHTTPClient:
    """Answers from scripted outcomes, in order; the last one repeats."""

    get_calls: list[dict[str, Any]]
    post_calls: list[dict[str, Any]]

    def __init__(
        self,
        gets: Outcome | list[Outcome] | None = None,
        posts: Outcome | list[Outcome] | None = None,
    ):
        self._gets = _as_list(gets)
        self._posts = _as_list(posts)
        self.get_calls = []
        self.post_calls = []

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        self.get_calls.append({"url": url, **kwargs})

        return _answer(self._gets, len(self.get_calls))

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        self.post_calls.append({"url": url, **kwargs})

        return _answer(self._posts, len(self.post_calls))


def _as_list(outcomes: Outcome | list[Outcome] | None) -> list[Outcome]:
    if outcomes is None:
        return []

    return outcomes if isinstance(outcomes, list) else [outcomes]


def _answer(outcomes: list[Outcome], call: int) -> requests.Response:
    outcome = outcomes[min(call, len(outcomes)) - 1]

    if isinstance(outcome, Exception):
        raise outcome

    return outcome
