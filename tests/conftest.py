"""Shared pytest fixtures (JUnit: @BeforeEach + @MockBean setup).

The key idea: replace the real exchange-rate client with a fake, so tests are fast,
offline and deterministic. No mocking library needed, because `get_rate_client` is
a FastAPI dependency and can be overridden.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_rate_client
from app.core.errors import ExchangeRateUnavailable
from app.main import create_app


class FakeRates:
    TABLE = {
        ("USD", "EUR"): Decimal("0.90"),
        ("EUR", "USD"): Decimal("1.25"),
    }

    async def get_rate(self, base: str, target: str) -> Decimal:
        if base == target:
            return Decimal("1")
        try:
            return self.TABLE[(base, target)]
        except KeyError:
            raise ExchangeRateUnavailable(f"No rate for {base}->{target}") from None


@pytest.fixture
def client():
    app = create_app()  # fresh app => fresh empty repository for every test
    app.dependency_overrides[get_rate_client] = lambda: FakeRates()
    with TestClient(app) as c:
        yield c


def make_account(client, owner="Alice", currency="USD", initial=0):
    resp = client.post(
        "/accounts",
        json={"owner": owner, "currency": currency, "initial_deposit": str(initial)},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
