from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from . import schemas, service
from app.security import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=schemas.OrderResponse)
async def checkout(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        order, items, payment = await service.checkout(db, current_user.user_id)
    except service.EmptyCart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
    except service.InsufficientStock:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient stock")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment failed")
    return schemas.OrderResponse(
        id=order.id,
        buyer_id=order.buyer_id,
        total_amount=float(order.total_amount),
        status=order.status,
        items=[schemas.OrderItemResponse(product_id=i.product_id, quantity=i.quantity, unit_price=float(i.unit_price)) for i in items],
        payment_reference=payment.reference,
    )


@router.get("", response_model=list[schemas.OrderResponse])
async def list_orders(
    limit: int = Query(20, le=100, ge=1),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orders = await service.list_orders(db, current_user.user_id, limit, offset)
    result = []
    for o in orders:
        detail = await service.get_order(db, current_user.user_id, o.id)
        order, items, payment = detail
        result.append(
            schemas.OrderResponse(
                id=order.id,
                buyer_id=order.buyer_id,
                total_amount=float(order.total_amount),
                status=order.status,
                items=[schemas.OrderItemResponse(product_id=i.product_id, quantity=i.quantity, unit_price=float(i.unit_price)) for i in items],
                payment_reference=payment.reference if payment else None,
            )
        )
    return result


@router.get("/{order_id}", response_model=schemas.OrderResponse)
async def get_order(order_id: int, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    detail = await service.get_order(db, current_user.user_id, order_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order, items, payment = detail
    return schemas.OrderResponse(
        id=order.id,
        buyer_id=order.buyer_id,
        total_amount=float(order.total_amount),
        status=order.status,
        items=[schemas.OrderItemResponse(product_id=i.product_id, quantity=i.quantity, unit_price=float(i.unit_price)) for i in items],
        payment_reference=payment.reference if payment else None,
    )
