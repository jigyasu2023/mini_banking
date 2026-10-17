from decimal import Decimal

from tests.conftest import make_account


def dec(value: str) -> Decimal:
    return Decimal(value)


# ---------- accounts ----------
def test_open_account_with_initial_deposit(client):
    acc = make_account(client, "Alice", "usd", 100)
    assert acc["owner"] == "Alice"
    assert acc["currency"] == "USD"  # normalized to upper case
    assert dec(acc["balance"]) == dec("100")


def test_open_account_rejects_bad_input(client):
    resp = client.post("/accounts", json={"owner": "A", "currency": "DOLLARS"})
    assert resp.status_code == 422  # Pydantic validation, like @Valid -> 400 in Spring


def test_unknown_account_returns_404(client):
    resp = client.get("/accounts/nope")
    assert resp.status_code == 404
    assert resp.json()["error"] == "AccountNotFound"


# ---------- deposit / withdraw ----------
def test_deposit_and_withdraw(client):
    acc = make_account(client, initial=50)
    resp = client.post(f"/accounts/{acc['id']}/deposit", json={"amount": "25.50"})
    assert dec(resp.json()["balance"]) == dec("75.50")

    resp = client.post(f"/accounts/{acc['id']}/withdraw", json={"amount": "10"})
    assert dec(resp.json()["balance"]) == dec("65.50")


def test_withdraw_more_than_balance_is_rejected(client):
    acc = make_account(client, initial=20)
    resp = client.post(f"/accounts/{acc['id']}/withdraw", json={"amount": "20.01"})
    assert resp.status_code == 409
    assert resp.json()["error"] == "InsufficientFunds"
    # balance unchanged
    assert dec(client.get(f"/accounts/{acc['id']}").json()["balance"]) == dec("20")


def test_zero_or_negative_amount_is_rejected(client):
    acc = make_account(client, initial=20)
    for bad in ("0", "-5"):
        resp = client.post(f"/accounts/{acc['id']}/deposit", json={"amount": bad})
        assert resp.status_code == 422


def test_transaction_history_is_newest_first(client):
    acc = make_account(client, initial=100)
    client.post(f"/accounts/{acc['id']}/withdraw", json={"amount": "30"})
    history = client.get(f"/accounts/{acc['id']}/transactions").json()
    assert [t["type"] for t in history] == ["WITHDRAWAL", "DEPOSIT"]
    assert dec(history[0]["balance_after"]) == dec("70")


# ---------- transfers ----------
def test_transfer_same_currency(client):
    a = make_account(client, "Alice", "USD", 100)
    b = make_account(client, "Bob", "USD", 0)
    resp = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": "40"},
    )
    assert resp.status_code == 201
    assert dec(client.get(f"/accounts/{a['id']}").json()["balance"]) == dec("60")
    assert dec(client.get(f"/accounts/{b['id']}").json()["balance"]) == dec("40")


def test_transfer_converts_currency(client):
    usd = make_account(client, "Alice", "USD", 100)
    eur = make_account(client, "Bob", "EUR", 0)
    resp = client.post(
        "/transfers",
        json={"from_account_id": usd["id"], "to_account_id": eur["id"], "amount": "100"},
    )
    body = resp.json()
    assert resp.status_code == 201
    assert dec(body["credited"]) == dec("90.00")  # 100 USD * 0.90
    assert body["credited_currency"] == "EUR"
    assert dec(client.get(f"/accounts/{usd['id']}").json()["balance"]) == dec("0")


def test_transfer_with_insufficient_funds_changes_nothing(client):
    a = make_account(client, "Alice", "USD", 10)
    b = make_account(client, "Bob", "USD", 5)
    resp = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": "50"},
    )
    assert resp.status_code == 409
    assert dec(client.get(f"/accounts/{a['id']}").json()["balance"]) == dec("10")
    assert dec(client.get(f"/accounts/{b['id']}").json()["balance"]) == dec("5")


def test_transfer_to_same_account_is_rejected(client):
    a = make_account(client, initial=10)
    resp = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": a["id"], "amount": "1"},
    )
    assert resp.status_code == 400


# ---------- open-API powered ----------
def test_convert_balance(client):
    acc = make_account(client, "Alice", "USD", 200)
    resp = client.get(f"/accounts/{acc['id']}/balance/convert", params={"to": "eur"})
    body = resp.json()
    assert resp.status_code == 200
    assert dec(body["converted_amount"]) == dec("180.00")


def test_rate_endpoint(client):
    resp = client.get("/rates/usd/eur")
    assert resp.status_code == 200
    assert dec(resp.json()["rate"]) == dec("0.90")


def test_upstream_failure_maps_to_502(client):
    acc = make_account(client, "Alice", "USD", 10)
    resp = client.get(f"/accounts/{acc['id']}/balance/convert", params={"to": "XYZ"})
    assert resp.status_code == 502
    assert resp.json()["error"] == "ExchangeRateUnavailable"
