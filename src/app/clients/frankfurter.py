"""Client for the free Frankfurter exchange-rate API (https://frankfurter.dev, no key needed).

Spring equivalent: a WebClient / Feign client wrapped in a small class.

`ExchangeRateClient` is a Protocol, i.e. an interface by shape ("structural typing").
Anything with an async `get_rate(base, target)` qualifies, which is how the tests
plug in a fake without any mocking framework.
"""

from decimal import Decimal
from typing import Protocol

import httpx

from app.core.errors import ExchangeRateUnavailable


class ExchangeRateClient(Protocol):
    async def get_rate(self, base: str, target: str) -> Decimal: ...


class FrankfurterClient:
    def __init__(self, http: httpx.AsyncClient, base_url: str):
        self._http = http
        self._base_url = base_url.rstrip("/")

    async def get_rate(self, base: str, target: str) -> Decimal:
        if base == target:
            return Decimal("1")
        try:
            response = await self._http.get(
                f"{self._base_url}/latest", params={"base": base, "symbols": target}
            )
            response.raise_for_status()
            # Response looks like: {"amount":1.0,"base":"USD","date":"...","rates":{"EUR":0.86}}
            return Decimal(str(response.json()["rates"][target]))
        except (httpx.HTTPError, KeyError, ValueError, ArithmeticError) as exc:
            raise ExchangeRateUnavailable(f"Could not get {base}->{target} rate") from exc
