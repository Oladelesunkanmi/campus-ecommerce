import logging
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import cart_client, payment_client, product_client
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


class EmptyCart(Exception):
    pass


class InsufficientStock(Exception):
    pass


async def checkout(db: AsyncSession, user_id: int):
    # Step 1: Read cart items (empty cart -> 400)
    cart_items = await cart_client.get_cart_items(db, user_id)
    if not cart_items:
        raise EmptyCart()

    items_payload = [{"product_id": ci.product_id, "quantity": ci.quantity} for ci in cart_items]

    # Step 2: Reserve stock (ONE call; product service reserves all items atomically; returns 409 if any lacks stock)
    ok, reserved_items = await product_client.reserve_all(items_payload)
    if not ok:
        raise InsufficientStock()

    unit_price_map = {item["product_id"]: Decimal(str(item["unit_price"])) for item in reserved_items}
    total = sum(unit_price_map[ci.product_id] * ci.quantity for ci in cart_items)

    # Step 3: Create the order (PENDING) and order_items in order_db, commit
    try:
        order = Order(buyer_id=user_id, total_amount=total, status="PENDING")
        db.add(order)
        await db.flush()

        for ci in cart_items:
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=ci.product_id,
                    quantity=ci.quantity,
                    unit_price=unit_price_map[ci.product_id],
                )
            )
        await db.commit()
        await db.refresh(order)
    except Exception as exc:
        logger.error(f"Failed to create order in DB: {exc}")
        await product_client.restore_all(items_payload)
        raise

    # Step 4: Payment charge
    try:
        payment = await payment_client.create_payment(db, order.id, total)
    except Exception as exc:
        logger.error(f"Payment failed for order {order.id}: {exc}")
        await product_client.restore_all(items_payload)
        order.status = "FAILED"
        await db.commit()
        raise

    # Step 5: Mark the order PAID (commit), then cart_client.clear for user
    order.status = "PAID"
    await db.commit()
    await db.refresh(order)

    try:
        await cart_client.clear_cart(db, user_id)
    except Exception as exc:
        logger.warning(f"Failed to clear cart for user {user_id} after payment: {exc}")

    result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    items = result.scalars().all()
    return order, items, payment


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
