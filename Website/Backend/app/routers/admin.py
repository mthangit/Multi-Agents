from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import logging
from typing import List, Dict, Any
from app.database.database import get_db
from app.schemas import user as user_schema
from app.schemas import product as product_schema
from app.schemas import order as order_schema
from app.services import user_service, product_service, order_service
from app.utils.security import get_current_admin_user
from app.models.models import User

router = APIRouter(prefix="/admin", tags=["Admin"])

logger = logging.getLogger(__name__)


@router.get("/getUser", response_model=List[user_schema.User])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Lấy danh sách người dùng (chỉ dành cho admin)
    """
    return user_service.get_all_users(db, skip, limit)


@router.get("/getInvoices", response_model=List[order_schema.Order])
def get_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Lấy danh sách đơn hàng (chỉ dành cho admin)
    """
    return order_service.get_all_orders(db, skip, limit)


@router.get("/getInvoices/{invoice_id}", response_model=Dict[str, Any])
def get_invoice_details(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Lấy chi tiết đơn hàng (chỉ dành cho admin)
    """
    return order_service.get_order_by_id(db, invoice_id)


@router.post("/addproduct", response_model=product_schema.Product)
def add_product(
    product: product_schema.ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Thêm sản phẩm mới (chỉ dành cho admin)
    """
    return product_service.create_product(db, product)


@router.put("/products/{product_id}", response_model=product_schema.Product)
def update_product(
    product_id: int,
    product: product_schema.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Cập nhật thông tin sản phẩm (chỉ dành cho admin)
    """
    return product_service.update_product(db, product_id, product)


@router.delete("/products/{product_id}", response_model=Dict[str, str])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Xóa sản phẩm (chỉ dành cho admin)
    """
    return product_service.delete_product(db, product_id)


@router.put("/orders/{order_id}/status", response_model=order_schema.Order)
def update_order_status(
    order_id: int,
    status_data: Dict[str, str] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Cập nhật trạng thái đơn hàng (chỉ dành cho admin)
    """
    status = status_data.get("status")
    if not status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    return order_service.update_order_status(db, order_id, status) 