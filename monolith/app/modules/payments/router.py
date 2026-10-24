from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.payments import schemas, service
from app.security import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=schemas.PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: schemas.PaymentCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payment = await service.create_payment(db, data.order_id, data.amount)
    await db.commit()
    return payment


@router.get("/{payment_id}", response_model=schemas.PaymentResponse)
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    payment = await service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment
