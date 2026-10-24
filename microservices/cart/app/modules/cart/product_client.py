from dataclasses import dataclass

from app import http_client


@dataclass
class ProductData:
    id: int
    name: str
    price: float
    stock: int


PRODUCT_BASE_URL = "http://product:8000"


async def get_products_by_ids(ids: list[int]) -> list[ProductData]:
    if not ids:
        return []
    r = await http_client.client.post(f"{PRODUCT_BASE_URL}/products/internal/batch", json={"ids": ids})
    r.raise_for_status()
    data = r.json()
    return [ProductData(id=p["id"], name=p["name"], price=float(p["price"]), stock=p["stock"]) for p in data]
