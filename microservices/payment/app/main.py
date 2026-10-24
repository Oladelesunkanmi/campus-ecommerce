from fastapi import FastAPI
app = FastAPI(title="Payment Service")

@app.get("/health")
async def health():
    return {"status": "ok"}
