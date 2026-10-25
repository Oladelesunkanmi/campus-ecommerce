from pydantic import BaseModel


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class OrderResponse(BaseModel):
    id: int
    buyer_id: int
    total_amount: float
    status: str
    items: list[OrderItemResponse]
    payment_reference: str | None = None

    model_config = {"from_attributes": True}
