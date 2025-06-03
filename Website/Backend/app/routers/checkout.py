from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any
from app.database.database import get_db
from app.schemas import order as order_schema
from app.services import order_service
from app.utils.security import get_current_active_user
from app.models.models import User

router = APIRouter(prefix="/user/checkout", tags=["Checkout"])

logger = logging.getLogger(__name__)


@router.post("/place-order", response_model=Dict[str, Any])
def place_order(
    order_data: order_schema.OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Đặt hàng từ giỏ hàng hiện tại
    """
    return order_service.create_order_from_cart(db, current_user.id, order_data)


@router.post("/process-payment", response_model=Dict[str, Any])
def process_payment(
    payment_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Xử lý thanh toán
    """
    # Trong thực tế, bạn sẽ tích hợp với cổng thanh toán ở đây
    # Hiện tại, chúng ta chỉ giả lập thanh toán thành công
    payment_method = payment_data.get("paymentMethod", "card")
    
    return {
        "success": True,
        "message": f"Payment processed successfully with {payment_method}",
        "transaction_id": "mock_transaction_id"
    }


@router.post("/cash-on-delivery", response_model=Dict[str, Any])
def cash_on_delivery(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Thanh toán khi nhận hàng
    """
    return {
        "success": True,
        "message": "Cash on delivery option selected",
        "payment_method": "cash_on_delivery"
    } 