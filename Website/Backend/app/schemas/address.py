from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AddressBase(BaseModel):
    name: str
    phone: str
    address: str
    city: str
    state: Optional[str] = None
    country: str
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    is_default: Optional[bool] = None


class Address(AddressBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 