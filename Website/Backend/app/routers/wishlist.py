from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any
from app.database.database import get_db
from app.schemas import wishlist as wishlist_schema
from app.services import wishlist_service
from app.utils.security import get_current_active_user
from app.models.models import User

router = APIRouter(prefix="/user/wishlist", tags=["Wishlist"])

logger = logging.getLogger(__name__)


@router.get("/get", response_model=Dict[str, Any])
def get_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy danh sách yêu thích của người dùng hiện tại
    """
    return wishlist_service.get_user_wishlist(db, current_user.id)


@router.post("/add", response_model=Dict[str, Any])
def add_to_wishlist(
    product: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Thêm sản phẩm vào danh sách yêu thích
    """
    return wishlist_service.add_to_wishlist(db, current_user.id, product)


@router.delete("/remove/{product_id}", response_model=Dict[str, Any])
def remove_from_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Xóa sản phẩm khỏi danh sách yêu thích
    """
    return wishlist_service.remove_from_wishlist(db, current_user.id, product_id) 