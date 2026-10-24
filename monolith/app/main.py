import logging

from fastapi import FastAPI

from app.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.orders.router import router as orders_router
from app.modules.payments.router import router as payments_router
from app.modules.products.router import router as products_router

logging.basicConfig(level=settings.LOG_LEVEL.upper())

app = FastAPI(title="Campus E-Commerce Monolith")

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
