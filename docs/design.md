# Design (final)
## Tables
users: id, email (unique), password_hash, full_name, created_at
products: id, seller_id, name, description, category, price, stock, created_at
cart_items: id, user_id, product_id, quantity (unique user_id+product_id)
orders: id, buyer_id, total_amount, status, created_at
order_items: id, order_id, product_id, quantity, unit_price
payments: id, order_id, amount, status, reference, created_at
Indexes (only these): users.email unique, products.category, products.name,
cart_items.user_id, orders.buyer_id, order_items.order_id, payments.order_id.
Money columns are NUMERIC(10,2). Stock has CHECK (stock >= 0).
## Endpoints
See CLAUDE.md API section. All identical in both systems.
