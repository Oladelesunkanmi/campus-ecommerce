import logging

from fastapi import FastAPI

from app.config import settings
from app.modules.products.router import router as products_router

logging.basicConfig(level=settings.LOG_LEVEL.upper())

app = FastAPI(title="Product Service")
app.include_router(products_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
