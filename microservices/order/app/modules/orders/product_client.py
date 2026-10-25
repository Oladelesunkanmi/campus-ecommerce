from dataclasses import dataclass
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app import http_client

PRODUCT_BASE_URL = os.environ.get("PRODUCT_BASE_URL", "http://product:8000")


@dataclass
class ProductData:
    id: int
    name: str
    price: float
    stock: int


async def get_products_by_ids(db: AsyncSession | None, ids: list[int]) -> list[ProductData]:
    if not ids:
        return []
    response = await http_client.client.post(f"{PRODUCT_BASE_URL}/products/internal/batch", json={"ids": ids})
    if response.status_code != 200:
        return []
    return [ProductData(id=p["id"], name=p["name"], price=float(p["price"]), stock=p["stock"]) for p in response.json()]


async def reserve_stock(db: AsyncSession | None, product_id: int, qty: int) -> bool:
    response = await http_client.client.post(
        f"{PRODUCT_BASE_URL}/products/internal/reserve",
        json={"items": [{"product_id": product_id, "quantity": qty}]},
    )
    return response.status_code == 200


async def restore_stock(db: AsyncSession | None, product_id: int, qty: int) -> None:
    await http_client.client.post(
        f"{PRODUCT_BASE_URL}/products/internal/restore",
        json={"items": [{"product_id": product_id, "quantity": qty}]},
    )


async def reserve_all(items: list[dict]) -> tuple[bool, list[dict]]:
    """Reserves all items in one atomic call to product service."""
    response = await http_client.client.post(
        f"{PRODUCT_BASE_URL}/products/internal/reserve",
        json={"items": [{"product_id": it["product_id"], "quantity": it["quantity"]} for it in items]},
    )
    if response.status_code == 200:
        return True, response.json()
    return False, []


async def restore_all(items: list[dict]) -> None:
    """Restores stock for all items in one call."""
    await http_client.client.post(
        f"{PRODUCT_BASE_URL}/products/internal/restore",
        json={"items": [{"product_id": it["product_id"], "quantity": it["quantity"]} for it in items]},
    )
