"""Domain model: Account and Transaction.

These are plain Python dataclasses (Spring: @Entity / POJO, but Lombok-free).
Business rules live here, on the object, rather than in a service.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from app.core.errors import InsufficientFunds, InvalidTransaction


class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


@dataclass
class Transaction:
    type: TransactionType
    amount: Decimal
    balance_after: Decimal
    description: str = ""
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Account:
    owner: str
    currency: str
    id: str = field(default_factory=lambda: uuid4().hex[:10])
    balance: Decimal = Decimal("0.00")
    transactions: list[Transaction] = field(default_factory=list)

    def deposit(
        self,
        amount: Decimal,
        kind: TransactionType = TransactionType.DEPOSIT,
        description: str = "",
    ) -> Transaction:
        self._check_amount(amount)
        self.balance += amount
        return self._record(kind, amount, description)

    def withdraw(
        self,
        amount: Decimal,
        kind: TransactionType = TransactionType.WITHDRAWAL,
        description: str = "",
    ) -> Transaction:
        self._check_amount(amount)
        if amount > self.balance:
            raise InsufficientFunds(
                f"Account {self.id} has {self.balance} {self.currency}, cannot withdraw {amount}"
            )
        self.balance -= amount
        return self._record(kind, amount, description)

    @staticmethod
    def _check_amount(amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidTransaction("Amount must be greater than zero")

    def _record(self, kind: TransactionType, amount: Decimal, description: str) -> Transaction:
        tx = Transaction(
            type=kind, amount=amount, balance_after=self.balance, description=description
        )
        self.transactions.append(tx)
        return tx
