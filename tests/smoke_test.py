import asyncio
import os
import sys
import uuid

import httpx

BASE_URL = os.environ.get("BASE_URL") or (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000")


def main():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    password = "secret123"

    # register
    r = client.post("/auth/register", json={"email": email, "password": password, "full_name": "Smoke User"})
    assert r.status_code == 201, r.text
    print("register OK")

    # login
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    print("login OK")

    # create product
    r = client.post("/products", json={"name": "Widget", "description": "d", "category": "gadgets", "price": 9.99, "stock": 5}, headers=auth)
    assert r.status_code == 201, r.text
    product_id = r.json()["id"]
    print("create product OK", product_id)

    # list + search + filter
    r = client.get("/products")
    assert r.status_code == 200 and len(r.json()) >= 1
    r = client.get("/products", params={"q": "widg"})
    assert r.status_code == 200 and any(p["id"] == product_id for p in r.json())
    r = client.get("/products", params={"category": "gadgets"})
    assert r.status_code == 200 and any(p["id"] == product_id for p in r.json())
    print("list/search/filter OK")

    # get by id
    r = client.get(f"/products/{product_id}")
    assert r.status_code == 200 and r.json()["id"] == product_id
    print("get product OK")

    # add to cart
    r = client.post("/cart/items", json={"product_id": product_id, "quantity": 2}, headers=auth)
    assert r.status_code == 201, r.text
    print("add to cart OK")

    # view cart
    r = client.get("/cart", headers=auth)
    assert r.status_code == 200
    cart = r.json()
    assert cart["total"] > 0 and len(cart["items"]) == 1
    print("view cart OK", cart["total"])

    # remove from cart
    r = client.delete(f"/cart/items/{product_id}", headers=auth)
    assert r.status_code == 204, r.text
    print("remove from cart OK")

    # error cases
    r = client.get("/products/999999")
    assert r.status_code == 404, r.text
    r = client.post("/cart/items", json={"product_id": 999999, "quantity": 1}, headers=auth)
    assert r.status_code == 404, r.text
    r = client.delete("/cart/items/999999", headers=auth)
    assert r.status_code == 404, r.text
    r = client.post("/products", json={"name": "X", "category": "c", "price": 1.0, "stock": -1}, headers=auth)
    assert r.status_code == 422, r.text
    r = client.post("/products", json={"name": "X", "category": "c", "price": 1.0, "stock": 1})
    assert r.status_code in (401, 403), r.text
    print("error cases OK")

    # --- checkout tests ---
    # successful checkout
    r = client.post("/cart/items", json={"product_id": product_id, "quantity": 2}, headers=auth)
    assert r.status_code == 201, r.text
    r = client.post("/orders/checkout", headers=auth)
    assert r.status_code == 200, r.text
    order = r.json()
    assert order["status"] == "PAID"
    assert order["payment_reference"] is not None
    print("checkout OK", order["id"])

    # cart emptied
    r = client.get("/cart", headers=auth)
    assert r.status_code == 200 and len(r.json()["items"]) == 0
    print("cart emptied OK")

    # empty cart checkout -> 400
    r = client.post("/orders/checkout", headers=auth)
    assert r.status_code == 400, r.text
    print("empty cart checkout 400 OK")

    # stock reduced: product now stock 3 (5-2)
    r = client.get(f"/products/{product_id}")
    assert r.json()["stock"] == 3
    print("stock reduced OK")

    # insufficient stock: request more than available
    r = client.post("/cart/items", json={"product_id": product_id, "quantity": 10}, headers=auth)
    assert r.status_code == 201, r.text
    r = client.post("/orders/checkout", headers=auth)
    assert r.status_code == 409, r.text
    # stock unchanged
    r = client.get(f"/products/{product_id}")
    assert r.json()["stock"] == 3
    print("insufficient stock 409 OK")
    # clear cart for cleanliness
    client.delete(f"/cart/items/{product_id}", headers=auth)

    # another user's order -> 404
    email2 = f"smoke2-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": email2, "password": password, "full_name": "U2"})
    r = client.post("/auth/login", json={"email": email2, "password": password})
    token2 = r.json()["access_token"]
    auth2 = {"Authorization": f"Bearer {token2}"}
    r = client.get(f"/orders/{order['id']}", headers=auth2)
    assert r.status_code == 404, r.text
    print("other user order 404 OK")

    print("SYNC SMOKE TESTS PASSED")


async def async_tests():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # setup product with stock 5 by a fresh user
        email = f"conc-{uuid.uuid4().hex[:8]}@example.com"
        password = "secret123"
        await client.post("/auth/register", json={"email": email, "password": password, "full_name": "Conc"})
        r = await client.post("/auth/login", json={"email": email, "password": password})
        token = r.json()["access_token"]
        auth = {"Authorization": f"Bearer {token}"}
        r = await client.post("/products", json={"name": "ConcProd", "description": "d", "category": "c", "price": 1.0, "stock": 5}, headers=auth)
        product_id = r.json()["id"]

        async def one_user(i):
            e = f"u{i}-{uuid.uuid4().hex[:6]}@example.com"
            await client.post("/auth/register", json={"email": e, "password": password, "full_name": f"U{i}"})
            r = await client.post("/auth/login", json={"email": e, "password": password})
            t = r.json()["access_token"]
            a = {"Authorization": f"Bearer {t}"}
            await client.post("/cart/items", json={"product_id": product_id, "quantity": 1}, headers=a)
            r = await client.post("/orders/checkout", headers=a)
            return r.status_code

        results = await asyncio.gather(*[one_user(i) for i in range(20)], return_exceptions=True)
        successes = sum(1 for r in results if r == 200)
        conflicts = sum(1 for r in results if r == 409)
        print(f"concurrency: {successes} success, {conflicts} conflict")
        assert successes == 5, results
        assert conflicts == 15, results

        r = await client.get(f"/products/{product_id}")
        assert r.json()["stock"] == 0
        print("concurrency stock 0 OK")
        print("CONCURRENCY TEST PASSED")


if __name__ == "__main__":
    main()
    asyncio.run(async_tests())
    print("ALL SMOKE TESTS PASSED")
