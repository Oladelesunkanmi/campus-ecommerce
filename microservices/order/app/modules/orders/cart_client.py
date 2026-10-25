from dataclasses import dataclass
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app import http_client

CART_BASE_URL = os.environ.get("CART_BASE_URL", "http://cart:8000")


@dataclass
class CartItemData:
    product_id: int
    quantity: int


async def get_cart_items(db: AsyncSession | None, user_id: int) -> list[CartItemData]:
    response = await http_client.client.get(f"{CART_BASE_URL}/cart/internal/{user_id}")
    if response.status_code != 200:
        return []
    items = response.json()
    return [CartItemData(product_id=item["product_id"], quantity=item["quantity"]) for item in items]


async def clear_cart(db: AsyncSession | None, user_id: int) -> None:
    response = await http_client.client.delete(f"{CART_BASE_URL}/cart/internal/{user_id}")
    if response.status_code not in (200, 204):
        response.raise_for_status()
