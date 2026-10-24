import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.payments.models import Payment
from app.modules.payments.schemas import PaymentCreate


async def create_payment(db: AsyncSession, order_id: int, amount: float) -> Payment:
    await asyncio.sleep(settings.PAYMENT_DELAY_MS / 1000.0)
    payment = Payment(
        order_id=order_id,
        amount=amount,
        status="SUCCESS",
        reference=str(uuid.uuid4()),
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return payment


async def get_payment(db: AsyncSession, payment_id: int) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()


async def get_payment_by_order(db: AsyncSession, order_id: int) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    return result.scalar_one_or_none()
