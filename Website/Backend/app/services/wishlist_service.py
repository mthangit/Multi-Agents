from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from app.models.models import Wishlist, WishlistDetail, Product
from app.schemas import product as product_schema

logger = logging.getLogger(__name__)


def get_user_wishlist(db: Session, user_id: int):
    """Lấy danh sách yêu thích của người dùng"""
    # Kiểm tra xem người dùng đã có wishlist chưa
    wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
    
    # Nếu chưa có, tạo wishlist mới
    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
    
    # Lấy chi tiết wishlist với thông tin sản phẩm
    wishlist_items = []
    for wishlist_detail in db.query(WishlistDetail).filter(WishlistDetail.wishlist_id == wishlist.id).all():
        product = db.query(Product).filter(Product.id == wishlist_detail.product_id).first()
        if product:
            wishlist_items.append(
                product_schema.Product(
                    id=product.id,
                    name=product.name,
                    description=product.description,
                    price=product.price,
                    image_url=product.image_url,
                    category=product.category,
                    stock=product.stock,
                    created_at=product.created_at,
                    updated_at=product.updated_at
                )
            )
    
    return {
        "id": wishlist.id,
        "user_id": wishlist.user_id,
        "created_at": wishlist.created_at,
        "wishlist": wishlist_items
    }


def add_to_wishlist(db: Session, user_id: int, product_data: dict):
    """Thêm sản phẩm vào danh sách yêu thích"""
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
    
    # Lấy hoặc tạo wishlist
    wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
    
    # Kiểm tra sản phẩm đã có trong wishlist chưa
    wishlist_detail = db.query(WishlistDetail).filter(
        WishlistDetail.wishlist_id == wishlist.id,
        WishlistDetail.product_id == product_id
    ).first()
    
    if not wishlist_detail:
        # Nếu chưa có, thêm mới
        wishlist_detail = WishlistDetail(
            wishlist_id=wishlist.id,
            product_id=product_id
        )
        db.add(wishlist_detail)
        db.commit()
    
    # Trả về wishlist mới nhất
    return get_user_wishlist(db, user_id)


def remove_from_wishlist(db: Session, user_id: int, product_id: int):
    """Xóa sản phẩm khỏi danh sách yêu thích"""
    # Lấy wishlist
    wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    
    # Lấy chi tiết sản phẩm trong wishlist
    wishlist_detail = db.query(WishlistDetail).filter(
        WishlistDetail.wishlist_id == wishlist.id,
        WishlistDetail.product_id == product_id
    ).first()
    
    if not wishlist_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in wishlist"
        )
    
    # Xóa sản phẩm khỏi wishlist
    db.delete(wishlist_detail)
    db.commit()
    
    # Trả về wishlist mới nhất
    return get_user_wishlist(db, user_id) 