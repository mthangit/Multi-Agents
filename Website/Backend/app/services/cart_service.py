from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from typing import List
from app.models.models import Cart, CartDetail, Product
from app.schemas import cart as cart_schema
from app.schemas import product as product_schema

logger = logging.getLogger(__name__)


def get_user_cart(db: Session, user_id: int):
    """Lấy giỏ hàng của người dùng"""
    # Kiểm tra xem người dùng đã có giỏ hàng chưa
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    
    # Nếu chưa có, tạo giỏ hàng mới
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    # Lấy chi tiết giỏ hàng với thông tin sản phẩm
    cart_items = []
    for cart_detail in db.query(CartDetail).filter(CartDetail.cart_id == cart.id).all():
        product = db.query(Product).filter(Product.id == cart_detail.product_id).first()
        if product:
            cart_items.append(
                product_schema.ProductInCart(
                    id=product.id,
                    name=product.name,
                    price=product.price,
                    image_url=product.image_url,
                    quantity=cart_detail.quantity
                )
            )
    
    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "created_at": cart.created_at,
        "updated_at": cart.updated_at,
        "cart": cart_items
    }


def add_to_cart(db: Session, user_id: int, product_data: dict):
    """Thêm sản phẩm vào giỏ hàng"""
    # Kiểm tra sản phẩm có tồn tại không
    product_id = product_data.get("_id")
    if not product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID is required"
        )
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Kiểm tra số lượng tồn kho
    if product.stock <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is out of stock"
        )
    
    # Lấy hoặc tạo giỏ hàng
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    # Kiểm tra sản phẩm đã có trong giỏ hàng chưa
    cart_detail = db.query(CartDetail).filter(
        CartDetail.cart_id == cart.id,
        CartDetail.product_id == product_id
    ).first()
    
    if cart_detail:
        # Nếu đã có, tăng số lượng
        cart_detail.quantity += 1
    else:
        # Nếu chưa có, thêm mới
        cart_detail = CartDetail(
            cart_id=cart.id,
            product_id=product_id,
            quantity=1
        )
        db.add(cart_detail)
    
    db.commit()
    
    # Trả về giỏ hàng mới nhất
    return get_user_cart(db, user_id)


def update_cart_item(db: Session, user_id: int, product_id: int, action_type: str):
    """Cập nhật số lượng sản phẩm trong giỏ hàng"""
    # Lấy giỏ hàng
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    # Lấy chi tiết sản phẩm trong giỏ hàng
    cart_detail = db.query(CartDetail).filter(
        CartDetail.cart_id == cart.id,
        CartDetail.product_id == product_id
    ).first()
    
    if not cart_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in cart"
        )
    
    # Cập nhật số lượng
    if action_type == "increment":
        # Kiểm tra tồn kho
        product = db.query(Product).filter(Product.id == product_id).first()
        if cart_detail.quantity >= product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot exceed available stock"
            )
        cart_detail.quantity += 1
    elif action_type == "decrement":
        if cart_detail.quantity > 1:
            cart_detail.quantity -= 1
        else:
            # Nếu số lượng = 1 và giảm nữa thì xóa khỏi giỏ hàng
            db.delete(cart_detail)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action type. Use 'increment' or 'decrement'"
        )
    
    db.commit()
    
    # Trả về giỏ hàng mới nhất
    return get_user_cart(db, user_id)


def remove_from_cart(db: Session, user_id: int, product_id: int):
    """Xóa sản phẩm khỏi giỏ hàng"""
    # Lấy giỏ hàng
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    # Lấy chi tiết sản phẩm trong giỏ hàng
    cart_detail = db.query(CartDetail).filter(
        CartDetail.cart_id == cart.id,
        CartDetail.product_id == product_id
    ).first()
    
    if not cart_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in cart"
        )
    
    # Xóa sản phẩm khỏi giỏ hàng
    db.delete(cart_detail)
    db.commit()
    
    # Trả về giỏ hàng mới nhất
    return get_user_cart(db, user_id)


def clear_cart(db: Session, user_id: int):
    """Xóa toàn bộ giỏ hàng"""
    # Lấy giỏ hàng
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        return {"message": "Cart is already empty"}
    
    # Xóa tất cả chi tiết giỏ hàng
    db.query(CartDetail).filter(CartDetail.cart_id == cart.id).delete()
    db.commit()
    
    return {"message": "Cart cleared successfully"} 