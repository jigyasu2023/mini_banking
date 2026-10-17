# Mini Bank (FastAPI learning project)

A small banking API for learning Python: accounts, deposits, withdrawals, transfers,
and **live currency conversion from an open API** ([Frankfurter](https://frankfurter.dev), no key needed).

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                 # optional, defaults work
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive Swagger UI (generated automatically).

Run the tests (fully offline, the exchange API is faked):

```bash
pytest
```

## Try it

```bash
# open two accounts
curl -X POST localhost:8000/accounts -H 'content-type: application/json' \
  -d '{"owner":"Alice","currency":"USD","initial_deposit":"100"}'
curl -X POST localhost:8000/accounts -H 'content-type: application/json' \
  -d '{"owner":"Bob","currency":"EUR"}'

# transfer 50 USD -> EUR (converted with the live rate)
curl -X POST localhost:8000/transfers -H 'content-type: application/json' \
  -d '{"from_account_id":"<alice id>","to_account_id":"<bob id>","amount":"50"}'

# live rate and balance conversion
curl localhost:8000/rates/USD/EUR
curl "localhost:8000/accounts/<alice id>/balance/convert?to=AED"
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/accounts` | open account (owner, currency, initial_deposit) |
| GET | `/accounts`, `/accounts/{id}` | list / fetch |
| POST | `/accounts/{id}/deposit` | deposit `{"amount": "25.50"}` |
| POST | `/accounts/{id}/withdraw` | withdraw (409 if insufficient funds) |
| GET | `/accounts/{id}/transactions` | history, newest first |
| GET | `/accounts/{id}/balance/convert?to=EUR` | balance in another currency (open API) |
| POST | `/transfers` | transfer, auto-converts across currencies (open API) |
| GET | `/rates/{base}/{target}` | raw exchange rate (open API) |

## Structure (and the Spring Boot equivalent)

```
src/app/
├── main.py            @SpringBootApplication + @ControllerAdvice (app factory, startup, error handler)
├── config.py          application.properties        (pydantic-settings reads .env)
├── api/               @RestController               (routers: HTTP only, no logic)
│   └── deps.py        @Autowired / @Bean wiring     (Depends(...) providers)
├── services/          @Service                      (use-cases, constructor-injected deps)
├── models/            @Entity / domain objects      (dataclasses; rules like "no overdraft")
├── repositories/      JpaRepository                 (in-memory dict, swap for a DB later)
├── clients/           WebClient / Feign             (httpx call to the open API)
├── schemas/           DTO + Bean Validation         (Pydantic request/response models)
└── core/errors.py     custom exceptions             (each maps to an HTTP status)
tests/                 JUnit + @MockBean             (pytest + dependency_overrides)
```

Request flow: `router -> service -> (repository | client -> open API)`, validated by Pydantic on the way in and out.

## Things worth noticing

- **Money uses `Decimal`, never `float`.** `0.1 + 0.2 != 0.3` with floats.
- **No component scanning.** Wiring is explicit: look at `main.py` and `api/deps.py`.
- **`async def` endpoints** run on one event loop. The transfer does its network call *first*, then
  debits and credits with no `await` in between, so that pair can't be interleaved by another request.
- **Tests swap the open API for a fake** by overriding the `get_rate_client` dependency.

## Exercises (in order)

1. Add `GET /accounts/{id}/statement?from=...&to=...` filtering transactions by date.
2. Add a daily withdrawal limit rule on `Account` and a test for it.
3. Replace `AccountRepository` with SQLAlchemy + SQLite (only the repository should change).
4. Cache exchange rates for 60 seconds inside `FrankfurterClient`.
5. Add retries with `tenacity` when the open API fails.
6. Add a second open API (e.g. a public holidays API) and block transfers on holidays.
7. Add a `Dockerfile` running `uvicorn app.main:app --host 0.0.0.0`.
8. Split rates into its own service and call it from the bank service over HTTP.
