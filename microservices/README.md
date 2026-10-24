# Campus E-Commerce Microservices

## Run

```powershell
cd microservices
docker compose up --build -d
docker compose exec auth alembic upgrade head
docker compose exec product alembic upgrade head
```

Gateway: http://localhost:8000
```