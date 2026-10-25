# Microservices Checkout Saga

## Overview
In the monolith backend (`monolith-v1`), the checkout flow executes inside a single relational database transaction across the `orders`, `order_items`, `products`, `cart_items`, and `payments` tables. Any failure (e.g., insufficient stock, payment rejection, database constraint error) triggers a standard database `ROLLBACK`, guaranteeing atomicity, consistency, isolation, and durability (ACID) at the database engine level.

In the microservices architecture, each domain manages its own dedicated database (`auth_db`, `product_db`, `cart_db`, `order_db`, `payment_db`) without cross-service foreign keys. Distributed ACID transactions across services and databases are not supported (avoiding two-phase commit overhead). Instead, an **orchestrated Saga pattern** implemented in the `order` service manages checkout as a sequence of local transactions with explicit compensating transactions upon failure.

---
## Known divergence from the monolith (smoke test)
After a payment failure the monolith's single transaction rolls back and leaves no order. The saga has already committed the order, so it ends as FAILED. tests/smoke_test.py (unmodified) therefore fails its final assertion "orders unchanged" (0 before, 1 after) on the microservices stack. Stock restoration and cart preservation, asserted earlier in the same test, pass. This is an expected architectural difference, not a defect.
## Saga Workflow Steps

The saga executes the same logical business steps in the same order as the monolith:

1. **Step 1: Read Cart Items (`cart_client.get_cart_items`)**
   - The Order service queries `GET http://cart:8000/cart/internal/{user_id}`.
   - If the cart is empty, raises `EmptyCart` which maps to HTTP `400 Bad Request`.
   - *Failure impact:* No state changes have occurred; no compensation needed.

2. **Step 2: Reserve Stock (`product_client.reserve_all`)**
   - The Order service makes **one atomic HTTP call** to `POST http://product:8000/products/internal/reserve`.
   - The Product service atomically updates product stocks (`UPDATE products SET stock = stock - :qty WHERE id = :id AND stock >= :qty`). If any item lacks stock, the Product service rolls back its local transaction and returns HTTP `409 Conflict`.
   - If HTTP 409 is received, raises `InsufficientStock` which maps to HTTP `409 Conflict`.
   - *Failure impact:* Stock was not reserved; no compensation needed.

3. **Step 3: Create Pending Order (`order_db`)**
   - Creates the `Order` record with status `PENDING` and associated `OrderItem` records in `order_db`, then commits.
   - *Failure impact:* If writing to `order_db` fails (e.g., DB connection error), the compensation step calls `product_client.restore_all` via `POST http://product:8000/products/internal/restore` to release reserved stock.

4. **Step 4: Payment Charge (`payment_client.charge`)**
   - The Order service calls `POST http://payment:8000/payments/internal/charge` with `order_id` and `amount`.
   - The Payment service executes simulated payment (with 50 ms delay). If `FAIL_PAYMENT=1` is set, it simulates a failure and returns HTTP 500.
   - *Failure impact / Compensation:*
     - Call `product_client.restore_all` to release reserved stock back to `product_db`.
     - Update the order in `order_db` with status `FAILED` and commit.
     - Re-raise error to return HTTP `500 Internal Server Error` ("Payment failed"), matching the monolith's HTTP status.

5. **Step 5: Finalize Order & Clear Cart**
   - Update order status to `PAID` in `order_db` and commit.
   - Call `cart_client.clear_cart` via `DELETE http://cart:8000/cart/internal/{user_id}`.
   - *Failure impact:* If clearing the cart fails after payment succeeded, a warning is logged (`Failed to clear cart for user...`). The order remains `PAID` because the transaction has already completed and payment was processed.

---

## Compensation Table

| Step | Operation | Failure Scenario | Compensation / Handling | Resulting System State |
| :--- | :--- | :--- | :--- | :--- |
| **1. Read Cart** | `GET /cart/internal/{user_id}` | Empty cart or cart unreachable | Abort checkout, return HTTP 400 | No changes; cart intact, stock intact |
| **2. Reserve Stock** | `POST /products/internal/reserve` | Any product has insufficient stock (HTTP 409) | Abort checkout, return HTTP 409 | Stock unchanged, no order created, cart intact |
| **3. Create Order** | Insert `Order(PENDING)` & `OrderItem` in `order_db` | Local DB write failure | Call `POST /products/internal/restore` | Stock restored, no order created, cart intact |
| **4. Payment Charge** | `POST /payments/internal/charge` | Payment fails (timeout, error, `FAIL_PAYMENT=1`) | 1. Call `POST /products/internal/restore`<br>2. Update order to `FAILED` in `order_db`<br>3. Commit and return HTTP 500 | Stock restored to original count, order marked `FAILED`, cart intact |
| **5. Finalize** | 1. Update order `PAID`<br>2. `DELETE /cart/internal/{user_id}` | Cart deletion fails after payment | Log warning; do not fail checkout | Order is `PAID`, payment recorded, stock reduced |

---

## Architectural Comparison: Monolith vs Microservices Saga

| Characteristic | Monolith (`monolith-v1`) | Microservices Saga |
| :--- | :--- | :--- |
| **Transaction Boundary** | Single relational database transaction across all tables. | Multiple independent local transactions coordinated via HTTP. |
| **Consistency Model** | Strict ACID (Immediate Consistency). | Eventual Consistency with Compensating Transactions. |
| **Failure Rollback Mechanism** | Database engine `ROLLBACK` reverts all inserts and updates. | Explicit forward compensation (`restore_stock`, status `FAILED`). |
| **Database State on Payment Failure** | Order and order items are never committed; 0 order records in DB. | Order is committed with status `FAILED` for auditability and tracking. |
| **Stock Reservation** | Item-by-item atomic SQL updates within the same DB session. | Atomic multi-item reservation via internal Product service HTTP endpoint. |
| **Service Coupling** | Direct module imports (`app.modules.*.service`). | Shared HTTP client (`httpx.AsyncClient`) calling internal endpoints. |
| **External Visibility** | Public HTTP API behavior is functionally identical (`/orders/checkout`, HTTP 200/400/409/500). | Public HTTP API behavior is identical; internal endpoints protected by Nginx. |
