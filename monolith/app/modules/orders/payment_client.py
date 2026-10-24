from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payments.service import create_payment as _create, get_payment_by_order as _get_by_order


@dataclass
class PaymentData:
    id: int
    reference: str
    status: str


async def create_payment(db: AsyncSession, order_id: int, amount: float) -> PaymentData:
    p = await _create(db, order_id, amount)
    return PaymentData(id=p.id, reference=p.reference, status=p.status)


async def get_payment_by_order(db: AsyncSession, order_id: int) -> PaymentData | None:
    p = await _get_by_order(db, order_id)
    if p is None:
        return None
    return PaymentData(id=p.id, reference=p.reference, status=p.status)
