import asyncio
import csv
import os
import random
from passlib.context import CryptContext

import asyncpg

# table -> database name (monolith: all one db; microservices reuse this mapping)
TABLE_DB = {
    "users": "campus",
    "products": "campus",
    "cart_items": "campus",
    "orders": "campus",
    "order_items": "campus",
    "payments": "campus",
}

BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "10"))
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_USER = os.environ.get("DB_USER", "campus")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "campus")
DATA_DIR = os.environ.get("DATA_DIR", "jmeter/data")

CATEGORIES = [
    "Electronics", "Books", "Clothing", "Food", "Sports",
    "Toys", "Home", "Beauty", "Automotive", "Garden",
]

ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=BCRYPT_ROUNDS)


async def main():
    conn = await asyncpg.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database="campus")
    try:
        # idempotency: skip if already seeded
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        product_count = await conn.fetchval("SELECT COUNT(*) FROM products")

        if user_count < 1000:
            password_hash = ctx.hash("Test1234!")
            users = [(f"user{i}@test.com", password_hash, f"User {i}") for i in range(1, 1001)]
            await conn.copy_records_to_table("users", records=users, columns=["email", "password_hash", "full_name"])
            print(f"inserted users (now {await conn.fetchval('SELECT COUNT(*) FROM users')})")

        if product_count < 5000:
            random.seed(42)
            products = []
            for i in range(1, 5001):
                category = CATEGORIES[(i - 1) % len(CATEGORIES)]
                name = f"{category} Item {i}"
                price = round(random.uniform(50, 5000), 2)
                seller_id = random.randint(1, 1000)
                products.append((seller_id, name, f"Description for {name}", category, price, 100000))
            await conn.copy_records_to_table(
                "products",
                records=products,
                columns=["seller_id", "name", "description", "category", "price", "stock"],
            )
            print(f"inserted products (now {await conn.fetchval('SELECT COUNT(*) FROM products')})")

        # write CSVs
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "users.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["email", "password"])
            for i in range(1, 1001):
                w.writerow([f"user{i}@test.com", "Test1234!"])
        with open(os.path.join(DATA_DIR, "products.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "category", "name"])
            rows = await conn.fetch("SELECT id, category, name FROM products ORDER BY id")
            for r in rows:
                w.writerow([r["id"], r["category"], r["name"]])

        print("users:", await conn.fetchval("SELECT COUNT(*) FROM users"))
        print("products:", await conn.fetchval("SELECT COUNT(*) FROM products"))
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
