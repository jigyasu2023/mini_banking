"""Dependency providers used with `Depends(...)` (Spring: @Autowired / @Bean wiring).

Objects are created once at startup in main.py and stored on `app.state`.
These small functions hand them to endpoints. Tests override them via
`app.dependency_overrides`, which is the FastAPI version of @MockBean.
"""

from fastapi import Depends, Request

from app.clients.frankfurter import ExchangeRateClient
from app.repositories.account_repository import AccountRepository
from app.services.account_service import AccountService


def get_repository(request: Request) -> AccountRepository:
    return request.app.state.repo


def get_rate_client(request: Request) -> ExchangeRateClient:
    return request.app.state.rate_client


def get_account_service(
    repo: AccountRepository = Depends(get_repository),
    rates: ExchangeRateClient = Depends(get_rate_client),
) -> AccountService:
    return AccountService(repo, rates)
