"""Account endpoints (Spring: @RestController + @RequestMapping("/accounts"))."""

from fastapi import APIRouter, Depends

from app.api.deps import get_account_service
from app.schemas.bank import (
    AccountCreate,
    AccountOut,
    AmountRequest,
    ConversionOut,
    TransactionOut,
)
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])

# Every endpoint is `async def` on purpose: they then all run on the event loop thread,
# so no two requests can interleave in the middle of a balance update.


@router.post("", response_model=AccountOut, status_code=201)
async def open_account(body: AccountCreate, service: AccountService = Depends(get_account_service)):
    return service.open_account(body)


@router.get("", response_model=list[AccountOut])
async def list_accounts(service: AccountService = Depends(get_account_service)):
    return service.list_accounts()


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(account_id: str, service: AccountService = Depends(get_account_service)):
    return service.get_account(account_id)


@router.post("/{account_id}/deposit", response_model=AccountOut)
async def deposit(
    account_id: str, body: AmountRequest, service: AccountService = Depends(get_account_service)
):
    return service.deposit(account_id, body.amount)


@router.post("/{account_id}/withdraw", response_model=AccountOut)
async def withdraw(
    account_id: str, body: AmountRequest, service: AccountService = Depends(get_account_service)
):
    return service.withdraw(account_id, body.amount)


@router.get("/{account_id}/transactions", response_model=list[TransactionOut])
async def transactions(account_id: str, service: AccountService = Depends(get_account_service)):
    return service.history(account_id)


@router.get("/{account_id}/balance/convert", response_model=ConversionOut)
async def convert_balance(
    account_id: str, to: str, service: AccountService = Depends(get_account_service)
):
    """Show this account's balance in another currency, using a live rate from the open API."""
    return await service.convert_balance(account_id, to)
