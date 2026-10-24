from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    category: str
    price: float
    stock: int = Field(0, ge=0)


class StockUpdate(BaseModel):
    stock: int = Field(ge=0)


class ProductResponse(BaseModel):
    id: int
    seller_id: int
    name: str
    description: str
    category: str
    price: float
    stock: int

    model_config = {"from_attributes": True}


class ReserveItem(BaseModel):
    product_id: int
    quantity: int


class ReserveRequest(BaseModel):
    items: list[ReserveItem]
