import logging

from fastapi import FastAPI

from app.config import settings
from app.modules.payments.router import router as payments_router

logging.basicConfig(level=settings.LOG_LEVEL.upper())

app = FastAPI(title="Payment Service")
app.include_router(payments_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
