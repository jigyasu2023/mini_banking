"""In-memory account storage (Spring: a JpaRepository, minus the database).

Swap this class for a SQLAlchemy-backed one later; the service only depends on
these three methods, so nothing else has to change.
"""

from app.core.errors import AccountNotFound
from app.models.account import Account


class AccountRepository:
    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}

    def add(self, account: Account) -> Account:
        self._accounts[account.id] = account
        return account

    def get(self, account_id: str) -> Account:
        try:
            return self._accounts[account_id]
        except KeyError:
            raise AccountNotFound(f"Account {account_id} not found") from None

    def list_all(self) -> list[Account]:
        return list(self._accounts.values())
