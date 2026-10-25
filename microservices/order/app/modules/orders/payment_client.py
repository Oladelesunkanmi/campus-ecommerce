from dataclasses import dataclass
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app import http_client

PAYMENT_BASE_URL = os.environ.get("PAYMENT_BASE_URL", "http://payment:8000")


@dataclass
class PaymentData:
    id: int
    reference: str
    status: str


async def create_payment(db: AsyncSession | None, order_id: int, amount: float) -> PaymentData:
    response = await http_client.client.post(
        f"{PAYMENT_BASE_URL}/payments/internal/charge",
        json={"order_id": order_id, "amount": float(amount)},
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(f"Payment failed with status {response.status_code}: {response.text}")
    data = response.json()
    return PaymentData(id=data["id"], reference=data["reference"], status=data["status"])


async def get_payment_by_order(db: AsyncSession | None, order_id: int) -> PaymentData | None:
    response = await http_client.client.get(f"{PAYMENT_BASE_URL}/payments/internal/by-order/{order_id}")
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        return None
    data = response.json()
    return PaymentData(id=data["id"], reference=data["reference"], status=data["status"])


charge = create_payment
