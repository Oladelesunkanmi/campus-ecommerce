import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.http_client import close, init
from app.modules.cart.router import router as cart_router

logging.basicConfig(level=settings.LOG_LEVEL.upper())


@asynccontextmanager
async def lifespan(app):
    await init()
    yield
    await close()


app = FastAPI(title="Cart Service", lifespan=lifespan)
app.include_router(cart_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
