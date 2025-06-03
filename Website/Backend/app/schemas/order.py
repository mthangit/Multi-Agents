from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int
    invoice_id: int

    class Config:
        orm_mode = True


class OrderItemDetail(OrderItemBase):
    id: int
    product_name: str
    product_description: Optional[str] = None

    class Config:
        orm_mode = True


class OrderBase(BaseModel):
    user_id: int
    total_amount: float
    shipping_address: str
    phone: str
    payment_method: str
    status: str = "pending"


class OrderCreate(BaseModel):
    shipping_address: str
    phone: str
    payment_method: str


class Order(OrderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class OrderDetail(Order):
    items: List[OrderItemDetail] = []

    class Config:
        orm_mode = True 