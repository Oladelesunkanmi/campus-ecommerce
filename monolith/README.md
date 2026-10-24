# Campus E-Commerce Monolith

Single FastAPI application for the campus e-commerce micro-transaction system.

## Run

```powershell
docker compose up --build -d
docker compose exec app alembic upgrade head
```

## Seed / Reset (PowerShell)

Seed (empty database):

```powershell
docker compose exec db psql -U campus -d campus -c "TRUNCATE users, products, cart_items, order_items, orders, payments RESTART IDENTITY CASCADE;"
docker run --rm --network monolith_default -v "${PWD}\..:/workspace" -w /workspace -e DB_HOST=db -e DATA_DIR=/workspace/jmeter/data monolith-app python /workspace/scripts/seed.py
```

Reset (restore seeded state):

```powershell
docker run --rm --network monolith_default -v "${PWD}\..:/workspace" -w /workspace -e DB_HOST=db monolith-app python /workspace/scripts/reset.py
```

## Test

```powershell
curl http://localhost:8000/health
```
