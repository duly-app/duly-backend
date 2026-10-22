from collections.abc import Mapping
from typing import Any, Protocol

import requests


class HTTPClient(Protocol):
    def get(self, url: str, *, timeout: float) -> requests.Response: ...

    def post(
        self,
        url: str,
        *,
        json: Any,
        headers: Mapping[str, str],
        timeout: float,
    ) -> requests.Response: ...
