from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import Product
from app.modules.products.schemas import ProductCreate


async def list_products(db: AsyncSession, limit: int, offset: int, q: str | None, category: str | None):
    stmt = select(Product)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(Product.category == category)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_product(db: AsyncSession, product_id: int):
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, seller_id: int, data: ProductCreate) -> Product:
    product = Product(
        seller_id=seller_id,
        name=data.name,
        description=data.description,
        category=data.category,
        price=data.price,
        stock=data.stock,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_stock(db: AsyncSession, product_id: int, stock: int) -> Product | None:
    product = await get_product(db, product_id)
    if product is None:
        return None
    product.stock = stock
    await db.commit()
    await db.refresh(product)
    return product


async def reserve_stock(db: AsyncSession, product_id: int, qty: int) -> bool:
    stmt = (
        update(Product)
        .where(Product.id == product_id, Product.stock >= qty)
        .values(stock=Product.stock - qty)
    )
    result = await db.execute(stmt)
    return result.rowcount > 0


async def restore_stock(db: AsyncSession, product_id: int, qty: int) -> None:
    product = await get_product(db, product_id)
    if product is not None:
        product.stock += qty


async def get_products_by_ids(db: AsyncSession, ids: list[int]):
    if not ids:
        return []
    result = await db.execute(select(Product).where(Product.id.in_(ids)))
    return result.scalars().all()


async def reserve_all(db, items):
    try:
        for it in items:
            ok = await reserve_stock(db, it.product_id, it.quantity)
            if not ok:
                raise ValueError("insufficient stock")
        await db.commit()
        return True
    except Exception:
        await db.rollback()
        raise


async def restore_all(db, items):
    for it in items:
        await restore_stock(db, it.product_id, it.quantity)
    await db.commit()
