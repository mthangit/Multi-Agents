from pydantic import BaseModel
from typing import Optional, List


class AddressBase(BaseModel):
    address_line: str
    city: str
    state: str
    postal_code: str
    country: str
    phone: str
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    is_default: Optional[bool] = None


class Address(AddressBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True 