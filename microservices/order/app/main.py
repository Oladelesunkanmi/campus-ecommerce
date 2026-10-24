from fastapi import FastAPI
app = FastAPI(title="Order Service")

@app.get("/health")
async def health():
    return {"status": "ok"}
