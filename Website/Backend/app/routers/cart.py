from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any
from app.database.database import get_db
from app.schemas import cart as cart_schema
from app.services import cart_service
from app.utils.security import get_current_active_user
from app.models.models import User

router = APIRouter(prefix="/user/cart", tags=["Cart"])

logger = logging.getLogger(__name__)


@router.get("/get", response_model=Dict[str, Any])
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy giỏ hàng của người dùng hiện tại
    """
    return cart_service.get_user_cart(db, current_user.id)


@router.post("/add", response_model=Dict[str, Any])
def add_to_cart(
    product: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Thêm sản phẩm vào giỏ hàng
    """
    return cart_service.add_to_cart(db, current_user.id, product)


@router.post("/update/{product_id}", response_model=Dict[str, Any])
def update_cart_item(
    product_id: int,
    action: Dict[str, str] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cập nhật số lượng sản phẩm trong giỏ hàng
    """
    action_type = action.get("type")
    if not action_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action type is required"
        )
    
    return cart_service.update_cart_item(db, current_user.id, product_id, action_type)


@router.delete("/remove/{product_id}", response_model=Dict[str, Any])
def remove_from_cart(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Xóa sản phẩm khỏi giỏ hàng
    """
    return cart_service.remove_from_cart(db, current_user.id, product_id) 