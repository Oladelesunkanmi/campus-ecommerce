from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.products import schemas, service
from app.security import get_current_user

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[schemas.ProductResponse])
async def list_products(
    limit: int = Query(20, le=100, ge=1),
    offset: int = Query(0, ge=0),
    q: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await service.list_products(db, limit, offset, q, category)


@router.get("/{product_id}", response_model=schemas.ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: schemas.ProductCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_product(db, current_user.user_id, data)


@router.patch("/{product_id}/stock", response_model=schemas.ProductResponse)
async def update_stock(
    product_id: int,
    data: schemas.StockUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await service.update_stock(db, product_id, data.stock)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("/internal/reserve", status_code=200)
async def internal_reserve(data: schemas.ReserveRequest, db=Depends(get_db)):
    try:
        result = await service.reserve_all(db, data.items)
    except ValueError:
        raise HTTPException(status_code=409, detail="Insufficient stock")
    return result


@router.post("/internal/batch", status_code=200)
async def internal_batch(data: schemas.BatchRequest, db=Depends(get_db)):
    products = await service.get_products_by_ids(db, data.ids)
    return [{"id": p.id, "name": p.name, "price": float(p.price), "stock": p.stock} for p in products]


@router.post("/internal/restore", status_code=200)
async def internal_restore(data: schemas.ReserveRequest, db=Depends(get_db)):
    await service.restore_all(db, data.items)
    return {"status": "restored"}
