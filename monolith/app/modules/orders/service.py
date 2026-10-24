from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import cart_client, payment_client, product_client
from .models import Order, OrderItem


class EmptyCart(Exception):
    pass


class InsufficientStock(Exception):
    pass


async def checkout(db: AsyncSession, user_id: int):
    cart_items = await cart_client.get_cart_items(db, user_id)
    if not cart_items:
        raise EmptyCart()

    ids = [ci.product_id for ci in cart_items]
    products = await product_client.get_products_by_ids(db, ids)
    product_map = {p.id: p for p in products}

    try:
        for ci in cart_items:
            ok = await product_client.reserve_stock(db, ci.product_id, ci.quantity)
            if not ok:
                raise InsufficientStock()
        total = sum(product_map[ci.product_id].price * ci.quantity for ci in cart_items)

        order = Order(buyer_id=user_id, total_amount=total, status="PENDING")
        db.add(order)
        await db.flush()

        for ci in cart_items:
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=ci.product_id,
                    quantity=ci.quantity,
                    unit_price=product_map[ci.product_id].price,
                )
            )
        await db.flush()

        payment = await payment_client.create_payment(db, order.id, total)
        order.status = "PAID"
        await cart_client.clear_cart(db, user_id)
        await db.commit()
        await db.refresh(order)

        result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        items = result.scalars().all()
        return order, items, payment
    except Exception:
        await db.rollback()
        raise


async def list_orders(db: AsyncSession, user_id: int, limit: int, offset: int):
    result = await db.execute(
        select(Order)
        .where(Order.buyer_id == user_id)
        .order_by(Order.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def get_order(db: AsyncSession, user_id: int, order_id: int):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None or order.buyer_id != user_id:
        return None
    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    items = items_result.scalars().all()
    payment = await payment_client.get_payment_by_order(db, order.id)
    return order, items, payment
