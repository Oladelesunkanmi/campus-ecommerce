from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cart.models import CartItem


@dataclass
class CartItemData:
    product_id: int
    quantity: int


async def get_cart_items(db: AsyncSession, user_id: int) -> list[CartItemData]:
    result = await db.execute(select(CartItem).where(CartItem.user_id == user_id))
    return [CartItemData(product_id=ci.product_id, quantity=ci.quantity) for ci in result.scalars().all()]


async def clear_cart(db: AsyncSession, user_id: int) -> None:
    await db.execute(delete(CartItem).where(CartItem.user_id == user_id))
