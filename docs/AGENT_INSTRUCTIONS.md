# PROJECT INSTRUCTIONS (follow strictly)

## Context
This is an academic research project: a controlled performance comparison of
a MONOLITHIC and a MICROSERVICES backend for a campus e-commerce
micro-transaction system. Both systems must be functionally identical so that
any performance difference is caused ONLY by the architecture. Fairness and
reproducibility matter more than features or cleverness.

## Tech stack (do not substitute or add anything else)
- Python 3.11, FastAPI, Uvicorn
- SQLAlchemy 2.0 (async) with asyncpg, Alembic migrations
- PostgreSQL 16
- JWT auth (python-jose or PyJWT), bcrypt via passlib
- httpx (AsyncClient) for service-to-service calls (microservices only)
- Docker, Docker Compose, Nginx (API gateway, microservices only)
- Pin exact versions in requirements.txt
- NOT allowed: frontend, Kubernetes, message brokers (Kafka/RabbitMQ/Redis),
  caching layers, cloud services, real payment gateways, extra libraries.

## Repository layout
campus-ecommerce/
  docs/                 design.md, this file
  monolith/             single FastAPI app + Dockerfile + docker-compose.yml
  microservices/        auth/ product/ cart/ order/ payment/ nginx/ + docker-compose.yml
  jmeter/               test plans and seed scripts
  results/              experiment outputs

## Module structure (identical business logic in both systems)
Each domain (auth, products, cart, orders, payments) has the same files:
  models.py    SQLAlchemy models
  schemas.py   Pydantic schemas
  service.py   business logic (NO HTTP code, NO FastAPI imports)
  router.py    FastAPI endpoints (thin: validate, call service, return)
The service.py logic must be copy-compatible between the monolith and the
corresponding microservice. Never write different logic for the two systems,
except where a monolith calls another module directly and a microservice
calls it over HTTP (isolate this in one small client function).

## Database design (see docs/design.md for the final version)
Tables: users, products, cart_items, orders, order_items, payments.
- Monolith: one database, foreign keys allowed.
- Microservices: one database per service (auth_db, product_db, cart_db,
  order_db, payment_db) on ONE PostgreSQL container. NO cross-service foreign
  keys; store plain IDs only.
- Use Alembic migrations. Never create tables with create_all in app code.

## API (identical URLs in both systems)
POST /auth/register, POST /auth/login, GET /auth/me
GET /products, GET /products/{id}, POST /products, PATCH /products/{id}/stock
POST /cart/items, GET /cart, DELETE /cart/items/{product_id}
POST /orders/checkout, GET /orders, GET /orders/{id}
POST /payments, GET /payments/{id}
Also GET /health on every app/service.
In the microservices version, Nginx routes by path prefix so clients use the
same URLs through a single port.

## Fairness rules (never violate)
1. Every setting below must be configurable via environment variables and
   have the SAME value in both systems:
   BCRYPT_ROUNDS=10, DB pool size, max overflow, JWT secret, JWT expiry,
   payment simulation delay (50 ms, using asyncio.sleep), Uvicorn WORKERS.
2. JWT is verified locally in every service using the shared secret. Services
   must NOT call the Auth service to validate tokens.
3. Stock reservation must be one atomic statement:
   UPDATE products SET stock = stock - :qty WHERE id = :id AND stock >= :qty
   (check rows affected). No read-then-write.
4. No logging of request bodies and keep logging at WARNING level during
   performance runs (LOG_LEVEL env var).
5. No in-memory caching, no extra indexes beyond those in docs/design.md.
6. Docker resource limits are set in docker-compose via deploy/cpus/mem_limit.
   Application tier total: 2 CPUs and 1.5 GB. PostgreSQL: 1 CPU and 1 GB.
   The microservices share the app-tier budget between them.

## Checkout flow (the key transaction)
1. Read the user's cart items
2. Reserve stock atomically for each item (rollback everything if any fails)
3. Create the order and order items (status = PENDING)
4. Create the payment (simulated 50 ms delay, status = SUCCESS)
5. Mark the order PAID and clear the cart
Monolith: all of this in one DB transaction via function calls.
Microservices: Order service orchestrates via HTTP calls to Cart, Product and
Payment. On failure, compensate (restore stock, mark order FAILED).

## Working rules
- Work in SMALL steps. Do ONLY the task I give you. Do not build ahead.
- Before writing code for a task, list the files you will create or change.
- After each task, tell me exactly how to run it and how to test it
  (commands and example requests), then STOP and wait for my review.
- Keep code simple, readable, and commented. I must be able to explain every
  file to an examiner. No clever abstractions, no unused code.
- Ask me if anything is ambiguous. Do not invent requirements.
- Never change docs/design.md or the fairness rules without my approval.
- Use type hints and clear names. Handle errors with proper HTTP status codes.
- Commit-ready: at the end of each task, suggest a git commit message.