from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .product import ProductInCart


class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int


class CartItem(CartItemBase):
    id: int
    cart_id: int

    class Config:
        from_attributes = True


class CartBase(BaseModel):
    user_id: int


class CartCreate(CartBase):
    pass


class Cart(CartBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    cart_details: List[CartItem] = []

    class Config:
        from_attributes = True


class CartWithProducts(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    cart: List[ProductInCart] = []

    class Config:
        from_attributes = True 