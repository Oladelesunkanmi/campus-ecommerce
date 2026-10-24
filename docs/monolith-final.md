# Monolith Final

## Architecture
Single FastAPI application (Python 3.11, Uvicorn) backed by one PostgreSQL 16
database. Modules: auth, products, cart, orders, payments. Business logic lives
in each module's service.py; routers are thin.

## Settings (frozen)
- WORKERS=2, LOG_LEVEL=warning
- BCRYPT_ROUNDS=10, JWT_EXPIRY_MINUTES=60
- DB pool: size 5, max overflow 5, timeout 30s
- PAYMENT_DELAY_MS=50
- Postgres: max_connections=100, shared_buffers=256MB, work_mem=4MB, fsync=on
- App limits: 2 CPUs / 1.5 GB; DB: 1 CPU / 1 GB

## Run
docker compose up --build -d
docker compose exec app alembic upgrade head

## Seed / Reset
docker run --rm --network monolith_default -v "<repo>:/workspace" -w /workspace -e DB_HOST=db -e DATA_DIR=/workspace/jmeter/data monolith-app python /workspace/scripts/seed.py
docker run --rm --network monolith_default -v "<repo>:/workspace" -w /workspace -e DB_HOST=db monolith-app python /workspace/scripts/reset.py

## Smoke test
docker run --rm -v "<repo>/tests:/tests" python:3.11-slim sh -c "pip install --quiet httpx && BASE_URL=http://host.docker.internal:8000 python /tests/smoke_test.py"
