from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from typing import List, Optional
from app.models.models import Invoice, InvoiceDetail, Product, Cart, CartDetail
from app.schemas import order as order_schema
from app.services import cart_service

logger = logging.getLogger(__name__)


def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Lấy danh sách đơn hàng của người dùng"""
    orders = db.query(Invoice).filter(Invoice.user_id == user_id).order_by(
        Invoice.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return orders


def get_order_by_id(db: Session, order_id: int, user_id: Optional[int] = None):
    """Lấy thông tin chi tiết đơn hàng theo ID"""
    query = db.query(Invoice).filter(Invoice.id == order_id)
    
    # Nếu có user_id, kiểm tra đơn hàng có thuộc về người dùng không
    if user_id:
        query = query.filter(Invoice.user_id == user_id)
    
    order = query.first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Lấy chi tiết đơn hàng
    order_items = []
    for item in db.query(InvoiceDetail).filter(InvoiceDetail.invoice_id == order.id).all():
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            order_items.append(
                order_schema.OrderItemDetail(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                    product_name=product.name,
                    product_description=product.description
                )
            )
    
    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "shipping_address": order.shipping_address,
        "phone": order.phone,
        "payment_method": order.payment_method,
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": order_items
    }


def create_order_from_cart(db: Session, user_id: int, order_data: order_schema.OrderCreate):
    """Tạo đơn hàng từ giỏ hàng"""
    # Lấy giỏ hàng của người dùng
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    # Lấy chi tiết giỏ hàng
    cart_details = db.query(CartDetail).filter(CartDetail.cart_id == cart.id).all()
    if not cart_details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )
    
    # Tính tổng tiền
    total_amount = 0
    for cart_detail in cart_details:
        product = db.query(Product).filter(Product.id == cart_detail.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {cart_detail.product_id} not found"
            )
        
        # Kiểm tra tồn kho
        if product.stock < cart_detail.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for product {product.name}. Available: {product.stock}"
            )
        
        total_amount += product.price * cart_detail.quantity
    
    # Tạo đơn hàng mới
    new_order = Invoice(
        user_id=user_id,
        total_amount=total_amount,
        shipping_address=order_data.shipping_address,
        phone=order_data.phone,
        payment_method=order_data.payment_method,
        status="pending"
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # Tạo chi tiết đơn hàng
    for cart_detail in cart_details:
        product = db.query(Product).filter(Product.id == cart_detail.product_id).first()
        
        # Tạo chi tiết đơn hàng
        order_detail = InvoiceDetail(
            invoice_id=new_order.id,
            product_id=product.id,
            quantity=cart_detail.quantity,
            price=product.price
        )
        
        db.add(order_detail)
        
        # Cập nhật tồn kho
        product.stock -= cart_detail.quantity
    
    db.commit()
    
    # Xóa giỏ hàng
    db.query(CartDetail).filter(CartDetail.cart_id == cart.id).delete()
    db.commit()
    
    # Trả về thông tin đơn hàng
    return get_order_by_id(db, new_order.id)


def update_order_status(db: Session, order_id: int, status: str):
    """Cập nhật trạng thái đơn hàng (chỉ dành cho admin)"""
    order = db.query(Invoice).filter(Invoice.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Cập nhật trạng thái
    order.status = status
    db.commit()
    db.refresh(order)
    
    return order


def get_all_orders(db: Session, skip: int = 0, limit: int = 100):
    """Lấy danh sách tất cả đơn hàng (chỉ dành cho admin)"""
    orders = db.query(Invoice).order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    return orders 