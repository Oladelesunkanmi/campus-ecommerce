from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cart.models import CartItem
from app.modules.cart.product_client import get_products_by_ids
from app.modules.cart.schemas import CartItemRequest


async def add_to_cart(db: AsyncSession, user_id: int, data: CartItemRequest) -> CartItem:
    products = await get_products_by_ids(db, [data.product_id])
    if not products:
        raise ValueError("Product not found")

    result = await db.execute(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == data.product_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        item = CartItem(user_id=user_id, product_id=data.product_id, quantity=data.quantity)
        db.add(item)
    else:
        item.quantity += data.quantity
    await db.commit()
    await db.refresh(item)
    return item


async def get_cart(db: AsyncSession, user_id: int):
    result = await db.execute(select(CartItem).where(CartItem.user_id == user_id))
    cart_items = result.scalars().all()

    product_ids = [ci.product_id for ci in cart_items]
    products = await get_products_by_ids(db, product_ids)
    product_map = {p.id: p for p in products}

    items = []
    total = 0.0
    for cart_item in cart_items:
        product = product_map.get(cart_item.product_id)
        if product is None:
            continue
        line_total = product.price * cart_item.quantity
        total += line_total
        items.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "unit_price": product.price,
                "quantity": cart_item.quantity,
                "line_total": line_total,
            }
        )
    return items, total


async def remove_from_cart(db: AsyncSession, user_id: int, product_id: int) -> bool:
    result = await db.execute(
        delete(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    )
    await db.commit()
    return result.rowcount > 0
