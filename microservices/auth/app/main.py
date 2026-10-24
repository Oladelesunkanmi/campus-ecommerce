import logging

from fastapi import FastAPI

from app.config import settings
from app.modules.auth.router import router as auth_router

logging.basicConfig(level=settings.LOG_LEVEL.upper())

app = FastAPI(title="Auth Service")
app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
