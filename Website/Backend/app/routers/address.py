from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import List, Dict, Any
from app.database.database import get_db
from app.schemas import address as address_schema
from app.services import address_service
from app.utils.security import get_current_active_user
from app.models.models import User

router = APIRouter(prefix="/user/address", tags=["Address"])

logger = logging.getLogger(__name__)


@router.get("/get", response_model=Dict[str, List[Dict[str, Any]]])
def get_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy danh sách địa chỉ của người dùng hiện tại
    """
    addresses = address_service.get_user_addresses(db, current_user.id)
    return {"addresses": addresses}


@router.post("", response_model=Dict[str, Any])
def create_address(
    address: address_schema.AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Tạo địa chỉ mới cho người dùng hiện tại
    """
    return address_service.create_address(db, current_user.id, address)


@router.put("/{address_id}", response_model=Dict[str, Any])
def update_address(
    address_id: int,
    address: address_schema.AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cập nhật địa chỉ của người dùng hiện tại
    """
    return address_service.update_address(db, current_user.id, address_id, address)


@router.delete("/{address_id}", response_model=Dict[str, Any])
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Xóa địa chỉ của người dùng hiện tại
    """
    return address_service.delete_address(db, current_user.id, address_id) 