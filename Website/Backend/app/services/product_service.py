from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from typing import List, Optional
from app.models.models import Product
from app.schemas import product as product_schema

logger = logging.getLogger(__name__)


def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None
):
    """Lấy danh sách sản phẩm với các bộ lọc"""
    query = db.query(Product)
    
    # Áp dụng bộ lọc
    if category:
        query = query.filter(Product.category == category)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    # Phân trang
    products = query.offset(skip).limit(limit).all()
    return products


def get_product(db: Session, product_id: int):
    """Lấy thông tin chi tiết sản phẩm theo ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


def create_product(db: Session, product: product_schema.ProductCreate):
    """Tạo sản phẩm mới (chỉ dành cho admin)"""
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        image_url=product.image_url,
        category=product.category,
        stock=product.stock
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product: product_schema.ProductUpdate):
    """Cập nhật thông tin sản phẩm (chỉ dành cho admin)"""
    db_product = get_product(db, product_id)
    
    # Cập nhật thông tin
    if product.name is not None:
        db_product.name = product.name
    if product.description is not None:
        db_product.description = product.description
    if product.price is not None:
        db_product.price = product.price
    if product.image_url is not None:
        db_product.image_url = product.image_url
    if product.category is not None:
        db_product.category = product.category
    if product.stock is not None:
        db_product.stock = product.stock
    
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int):
    """Xóa sản phẩm (chỉ dành cho admin)"""
    db_product = get_product(db, product_id)
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}


def get_categories(db: Session):
    """Lấy danh sách các danh mục sản phẩm"""
    categories = db.query(Product.category).distinct().all()
    return [category[0] for category in categories if category[0]] 