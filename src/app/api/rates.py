"""Thin pass-through to the open exchange-rate API."""

from fastapi import APIRouter, Depends

from app.api.deps import get_account_service
from app.schemas.bank import RateOut
from app.services.account_service import AccountService

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("/{base}/{target}", response_model=RateOut)
async def get_rate(base: str, target: str, service: AccountService = Depends(get_account_service)):
    rate = await service.get_rate(base, target)
    return RateOut(base=base.upper(), target=target.upper(), rate=rate)
