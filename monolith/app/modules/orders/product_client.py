from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.service import (
    get_products_by_ids as _get,
    reserve_stock as _reserve,
    restore_stock as _restore,
)


@dataclass
class ProductData:
    id: int
    name: str
    price: float
    stock: int


async def get_products_by_ids(db: AsyncSession, ids: list[int]) -> list[ProductData]:
    products = await _get(db, ids)
    return [ProductData(id=p.id, name=p.name, price=float(p.price), stock=p.stock) for p in products]


async def reserve_stock(db: AsyncSession, product_id: int, qty: int) -> bool:
    return await _reserve(db, product_id, qty)


async def restore_stock(db: AsyncSession, product_id: int, qty: int) -> None:
    await _restore(db, product_id, qty)
