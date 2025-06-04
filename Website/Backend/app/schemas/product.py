from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    image: str
    category: str
    stock: int
    brand: Optional[str] = None
    gender: Optional[str] = None
    weight: Optional[str] = None
    quantity: Optional[int] = None
    images: Optional[Any] = None
    rating: Optional[float] = None
    newPrice: Optional[float] = None
    trending: Optional[bool] = None
    frameMaterial: Optional[str] = None
    lensMaterial: Optional[str] = None
    lensFeatures: Optional[str] = None
    frameShape: Optional[str] = None
    lensWidth: Optional[str] = None
    bridgeWidth: Optional[str] = None
    templeLength: Optional[str] = None
    color: Optional[str] = None
    availability: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None
    category: Optional[str] = None
    stock: Optional[int] = None
    brand: Optional[str] = None
    gender: Optional[str] = None
    weight: Optional[str] = None
    quantity: Optional[int] = None
    images: Optional[Any] = None
    rating: Optional[float] = None
    newPrice: Optional[float] = None
    trending: Optional[bool] = None
    frameMaterial: Optional[str] = None
    lensMaterial: Optional[str] = None
    lensFeatures: Optional[str] = None
    frameShape: Optional[str] = None
    lensWidth: Optional[str] = None
    bridgeWidth: Optional[str] = None
    templeLength: Optional[str] = None
    color: Optional[str] = None
    availability: Optional[str] = None


class Product(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ProductInCart(BaseModel):
    id: int
    name: str
    price: float
    image: str
    quantity: int

    class Config:
        orm_mode = True 