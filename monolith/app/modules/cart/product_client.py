from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.service import get_products_by_ids as _get_products_by_ids


@dataclass
class ProductData:
    id: int
    name: str
    price: float
    stock: int


async def get_products_by_ids(db: AsyncSession, ids: list[int]) -> list[ProductData]:
    # In the monolith this calls the products service directly.
    # In the microservices version this becomes an HTTP call.
    products = await _get_products_by_ids(db, ids)
    return [ProductData(id=p.id, name=p.name, price=float(p.price), stock=p.stock) for p in products]
