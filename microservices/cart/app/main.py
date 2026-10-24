from fastapi import FastAPI
app = FastAPI(title="Cart Service")

@app.get("/health")
async def health():
    return {"status": "ok"}
