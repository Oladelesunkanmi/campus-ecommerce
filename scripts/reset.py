import asyncio
import os

import asyncpg

TABLE_DB = {
    "users": "campus",
    "products": "campus",
    "cart_items": "campus",
    "orders": "campus",
    "order_items": "campus",
    "payments": "campus",
}

DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_USER = os.environ.get("DB_USER", "campus")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "campus")


async def main():
    conn = await asyncpg.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database="campus")
    try:
        await conn.execute("TRUNCATE cart_items, order_items, orders, payments RESTART IDENTITY CASCADE")
        await conn.execute("UPDATE products SET stock = 100000")
        await conn.execute("ANALYZE")
        print("cart_items:", await conn.fetchval("SELECT COUNT(*) FROM cart_items"))
        print("order_items:", await conn.fetchval("SELECT COUNT(*) FROM order_items"))
        print("orders:", await conn.fetchval("SELECT COUNT(*) FROM orders"))
        print("payments:", await conn.fetchval("SELECT COUNT(*) FROM payments"))
        print("products stock sample:", await conn.fetchval("SELECT stock FROM products LIMIT 1"))
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
