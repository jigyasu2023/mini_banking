"""Domain exceptions. Each carries the HTTP status it should map to.

Spring equivalent: custom RuntimeExceptions + @ControllerAdvice. The handler that
turns these into JSON responses is registered in main.py.
"""


class BankError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AccountNotFound(BankError):
    status_code = 404


class InsufficientFunds(BankError):
    status_code = 409


class InvalidTransaction(BankError):
    status_code = 400


class ExchangeRateUnavailable(BankError):
    status_code = 502  # the upstream (open API) failed, not our client
