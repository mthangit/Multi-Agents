from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .product import Product


class WishlistItemBase(BaseModel):
    product_id: int


class WishlistItemCreate(WishlistItemBase):
    pass


class WishlistItem(WishlistItemBase):
    id: int
    wishlist_id: int

    class Config:
        from_attributes = True


class WishlistBase(BaseModel):
    user_id: int


class WishlistCreate(WishlistBase):
    pass


class Wishlist(WishlistBase):
    id: int
    created_at: datetime
    wishlist_details: List[WishlistItem] = []

    class Config:
        from_attributes = True


class WishlistWithProducts(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    wishlist: List[Product] = []

    class Config:
        from_attributes = True 