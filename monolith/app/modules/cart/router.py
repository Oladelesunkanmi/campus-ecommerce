from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.cart import schemas, service
from app.security import get_current_user

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_item(
    data: schemas.CartItemRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await service.add_to_cart(db, current_user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {"status": "added"}


@router.get("", response_model=schemas.CartResponse)
async def get_cart(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items, total = await service.get_cart(db, current_user.id)
    return schemas.CartResponse(items=items, total=total)


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    product_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    removed = await service.remove_from_cart(db, current_user.id, product_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not in cart")
