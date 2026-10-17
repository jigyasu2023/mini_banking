"""Entry point (Spring: the @SpringBootApplication class).

Run with:  uvicorn app.main:app --reload
Docs UI:   http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import accounts, rates, transfers
from app.clients.frankfurter import FrankfurterClient
from app.config import settings
from app.core.errors import BankError
from app.repositories.account_repository import AccountRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hook. Build long-lived objects here (Spring: @Bean + @PreDestroy)."""
    app.state.repo = AccountRepository()
    # One shared HTTP client = connection pooling across requests.
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as http:
        app.state.rate_client = FrankfurterClient(http, settings.exchange_api_url)
        yield
    # leaving the `async with` closes the HTTP client


async def bank_error_handler(request: Request, exc: BankError) -> JSONResponse:
    """Spring: @ControllerAdvice + @ExceptionHandler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": type(exc).__name__, "message": exc.message},
    )


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.include_router(accounts.router)
    app.include_router(transfers.router)
    app.include_router(rates.router)
    app.add_exception_handler(BankError, bank_error_handler)

    @app.get("/health", tags=["meta"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
