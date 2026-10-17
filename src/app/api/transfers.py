"""Transfer endpoint. Converts currency automatically when the accounts differ."""

from fastapi import APIRouter, Depends

from app.api.deps import get_account_service
from app.schemas.bank import TransferOut, TransferRequest
from app.services.account_service import AccountService

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferOut, status_code=201)
async def transfer(body: TransferRequest, service: AccountService = Depends(get_account_service)):
    return await service.transfer(body.from_account_id, body.to_account_id, body.amount)
