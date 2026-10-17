"""Use-cases of the bank (Spring: @Service).

Dependencies come in through the constructor, exactly like constructor injection.
Nothing here knows about HTTP; it could be reused from a CLI or a message consumer.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.clients.frankfurter import ExchangeRateClient
from app.core.errors import InvalidTransaction
from app.models.account import Account, Transaction, TransactionType
from app.repositories.account_repository import AccountRepository
from app.schemas.bank import AccountCreate, ConversionOut, TransferOut

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


class AccountService:
    def __init__(self, repo: AccountRepository, rates: ExchangeRateClient):
        self._repo = repo
        self._rates = rates

    # ----- accounts -----
    def open_account(self, data: AccountCreate) -> Account:
        account = Account(owner=data.owner, currency=data.currency)
        if data.initial_deposit > 0:
            account.deposit(money(data.initial_deposit), description="Initial deposit")
        return self._repo.add(account)

    def get_account(self, account_id: str) -> Account:
        return self._repo.get(account_id)

    def list_accounts(self) -> list[Account]:
        return self._repo.list_all()

    def history(self, account_id: str) -> list[Transaction]:
        return list(reversed(self._repo.get(account_id).transactions))  # newest first

    # ----- money movement -----
    def deposit(self, account_id: str, amount: Decimal) -> Account:
        account = self._repo.get(account_id)
        account.deposit(money(amount))
        return account

    def withdraw(self, account_id: str, amount: Decimal) -> Account:
        account = self._repo.get(account_id)
        account.withdraw(money(amount))
        return account

    async def transfer(self, from_id: str, to_id: str, amount: Decimal) -> TransferOut:
        if from_id == to_id:
            raise InvalidTransaction("Cannot transfer to the same account")
        source = self._repo.get(from_id)
        target = self._repo.get(to_id)
        amount = money(amount)

        # 1) Do the slow I/O first (external API call) ...
        rate = await self._rates.get_rate(source.currency, target.currency)
        credited = money(amount * rate)

        # 2) ... then change state with no `await` in between. On a single event loop
        # nothing else can run in this stretch, so the debit+credit pair is atomic.
        # (With a real database you would use a DB transaction here instead.)
        source.withdraw(amount, TransactionType.TRANSFER_OUT, f"Transfer to {target.id}")
        target.deposit(credited, TransactionType.TRANSFER_IN, f"Transfer from {source.id}")

        return TransferOut(
            from_account=source,  # type: ignore[arg-type]  # converted via from_attributes
            to_account=target,  # type: ignore[arg-type]
            debited=amount,
            debited_currency=source.currency,
            credited=credited,
            credited_currency=target.currency,
            rate=rate,
        )

    # ----- open-API powered features -----
    async def convert_balance(self, account_id: str, to_currency: str) -> ConversionOut:
        account = self._repo.get(account_id)
        to_currency = to_currency.upper()
        rate = await self._rates.get_rate(account.currency, to_currency)
        return ConversionOut(
            from_currency=account.currency,
            to_currency=to_currency,
            rate=rate,
            original_amount=account.balance,
            converted_amount=money(account.balance * rate),
        )

    async def get_rate(self, base: str, target: str) -> Decimal:
        return await self._rates.get_rate(base.upper(), target.upper())
