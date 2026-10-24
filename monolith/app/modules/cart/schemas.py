from pydantic import BaseModel, Field


class CartItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    line_total: float


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total: float
