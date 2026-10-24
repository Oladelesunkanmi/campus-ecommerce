# Campus E-Commerce Monolith

Single FastAPI application for the campus e-commerce micro-transaction system.

## Run

```bash
docker compose up --build -d
docker compose exec app alembic upgrade head
```

## Test

```bash
curl http://localhost:8000/health
```
