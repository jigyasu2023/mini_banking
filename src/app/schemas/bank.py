"""Pydantic schemas: validation + JSON shape in one place.

Spring equivalent: DTO classes with Bean Validation annotations (@NotNull, @Size...).
Invalid input never reaches your code; FastAPI answers 422 automatically.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.account import TransactionType


def _normalize_currency(value: str) -> str:
    value = value.strip().upper()
    if len(value) != 3 or not value.isalpha():
        raise ValueError("currency must be a 3-letter code such as USD")
    return value


# ---------- requests ----------
class AccountCreate(BaseModel):
    owner: str = Field(min_length=2, max_length=100)
    currency: str = "USD"
    initial_deposit: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)

    _currency = field_validator("currency")(_normalize_currency)


class AmountRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)


class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: Decimal = Field(gt=0, decimal_places=2)


# ---------- responses ----------
class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # build from the Account dataclass

    id: str
    owner: str
    currency: str
    balance: Decimal


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: TransactionType
    amount: Decimal
    balance_after: Decimal
    description: str
    created_at: datetime


class TransferOut(BaseModel):
    from_account: AccountOut
    to_account: AccountOut
    debited: Decimal
    debited_currency: str
    credited: Decimal
    credited_currency: str
    rate: Decimal


class ConversionOut(BaseModel):
    from_currency: str
    to_currency: str
    rate: Decimal
    original_amount: Decimal
    converted_amount: Decimal


class RateOut(BaseModel):
    base: str
    target: str
    rate: Decimal
