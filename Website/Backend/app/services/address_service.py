from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from app.models.models import Address
from app.schemas import address as address_schema

logger = logging.getLogger(__name__)


def get_user_addresses(db: Session, user_id: int):
    """Lấy danh sách địa chỉ của người dùng"""
    db_addresses = db.query(Address).filter(Address.user_id == user_id).all()
    
    # Chuyển đổi từ đối tượng SQLAlchemy sang dict
    addresses = []
    for address in db_addresses:
        address_dict = {
            "id": address.id,
            "user_id": address.user_id,
            "name": address.name,
            "phone": address.phone,
            "address": address.address,
            "city": address.city,
            "state": address.state,
            "country": address.country,
            "is_default": address.is_default,
            "created_at": address.created_at,
            "updated_at": address.updated_at
        }
        addresses.append(address_dict)
    
    return addresses


def create_address(db: Session, user_id: int, address: address_schema.AddressCreate):
    """Tạo địa chỉ mới cho người dùng"""
    # Nếu địa chỉ mới là mặc định, cập nhật tất cả địa chỉ khác thành không mặc định
    if address.is_default:
        db.query(Address).filter(Address.user_id == user_id).update({"is_default": False})
    
    # Tạo địa chỉ mới
    db_address = Address(
        user_id=user_id,
        name=address.name,
        phone=address.phone,
        address=address.address,
        city=address.city,
        state=address.state,
        country=address.country,
        is_default=address.is_default
    )
    
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    
    # Chuyển đổi từ đối tượng SQLAlchemy sang dict
    address_dict = {
        "id": db_address.id,
        "user_id": db_address.user_id,
        "name": db_address.name,
        "phone": db_address.phone,
        "address": db_address.address,
        "city": db_address.city,
        "state": db_address.state,
        "country": db_address.country,
        "is_default": db_address.is_default,
        "created_at": db_address.created_at,
        "updated_at": db_address.updated_at
    }
    
    return address_dict


def update_address(db: Session, user_id: int, address_id: int, address: address_schema.AddressUpdate):
    """Cập nhật địa chỉ của người dùng"""
    # Kiểm tra địa chỉ có tồn tại không
    db_address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user_id
    ).first()
    
    if not db_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    # Nếu cập nhật thành địa chỉ mặc định, cập nhật tất cả địa chỉ khác thành không mặc định
    if address.is_default:
        db.query(Address).filter(Address.user_id == user_id).update({"is_default": False})
    
    # Cập nhật thông tin địa chỉ
    if address.name is not None:
        db_address.name = address.name
    if address.phone is not None:
        db_address.phone = address.phone
    if address.address is not None:
        db_address.address = address.address
    if address.city is not None:
        db_address.city = address.city
    if address.state is not None:
        db_address.state = address.state
    if address.country is not None:
        db_address.country = address.country
    if address.is_default is not None:
        db_address.is_default = address.is_default
    
    db.commit()
    db.refresh(db_address)
    
    # Chuyển đổi từ đối tượng SQLAlchemy sang dict
    address_dict = {
        "id": db_address.id,
        "user_id": db_address.user_id,
        "name": db_address.name,
        "phone": db_address.phone,
        "address": db_address.address,
        "city": db_address.city,
        "state": db_address.state,
        "country": db_address.country,
        "is_default": db_address.is_default,
        "created_at": db_address.created_at,
        "updated_at": db_address.updated_at
    }
    
    return address_dict


def delete_address(db: Session, user_id: int, address_id: int):
    """Xóa địa chỉ của người dùng"""
    # Kiểm tra địa chỉ có tồn tại không
    db_address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user_id
    ).first()
    
    if not db_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    # Xóa địa chỉ
    db.delete(db_address)
    db.commit()
    
    # Nếu địa chỉ bị xóa là địa chỉ mặc định, cập nhật địa chỉ đầu tiên thành mặc định (nếu có)
    if db_address.is_default:
        first_address = db.query(Address).filter(Address.user_id == user_id).first()
        if first_address:
            first_address.is_default = True
            db.commit()
    
    return {"message": "Address deleted successfully"} 