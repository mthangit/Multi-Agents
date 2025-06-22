from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from typing import List, Optional, Dict, Any
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
    db_products = query.offset(skip).limit(limit).all()
    
    # Chuyển đổi từ đối tượng SQLAlchemy sang schema Pydantic
    products = []
    for product in db_products:
        product_dict = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "image": product.image,
            "category": product.category,
            "stock": product.stock,
            "brand": product.brand,
            "gender": product.gender,
            "weight": product.weight,
            "quantity": product.quantity,
            "images": product.images,
            "rating": product.rating,
            "newPrice": product.newPrice,
            "trending": product.trending,
            "frameMaterial": product.frameMaterial,
            "lensMaterial": product.lensMaterial,
            "lensFeatures": product.lensFeatures,
            "frameShape": product.frameShape,
            "lensWidth": product.lensWidth,
            "bridgeWidth": product.bridgeWidth,
            "templeLength": product.templeLength,
            "color": product.color,
            "availability": product.availability
        }
        products.append(product_dict)
    
    return products


def get_product(db: Session, product_id: int):
    """Lấy thông tin chi tiết sản phẩm theo ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Chuyển đổi từ đối tượng SQLAlchemy sang dict
    product_dict = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "image": product.image,
        "category": product.category,
        "stock": product.stock,
        "brand": product.brand,
        "gender": product.gender,
        "weight": product.weight,
        "quantity": product.quantity,
        "images": product.images,
        "rating": product.rating,
        "newPrice": product.newPrice,
        "trending": product.trending,
        "frameMaterial": product.frameMaterial,
        "lensMaterial": product.lensMaterial,
        "lensFeatures": product.lensFeatures,
        "frameShape": product.frameShape,
        "lensWidth": product.lensWidth,
        "bridgeWidth": product.bridgeWidth,
        "templeLength": product.templeLength,
        "color": product.color,
        "availability": product.availability
    }
    
    return product_dict


def create_product(db: Session, product: product_schema.ProductCreate):
    """Tạo sản phẩm mới (chỉ dành cho admin)"""
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        image=product.image,
        category=product.category,
        stock=product.stock,
        brand=product.brand,
        gender=product.gender,
        weight=product.weight,
        quantity=product.quantity,
        images=product.images,
        rating=product.rating,
        newPrice=product.newPrice,
        trending=product.trending,
        frameMaterial=product.frameMaterial,
        lensMaterial=product.lensMaterial,
        lensFeatures=product.lensFeatures,
        frameShape=product.frameShape,
        lensWidth=product.lensWidth,
        bridgeWidth=product.bridgeWidth,
        templeLength=product.templeLength,
        color=product.color,
        availability=product.availability
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Chuyển đổi từ đối tượng SQLAlchemy sang dict
    product_dict = {
        "id": db_product.id,
        "name": db_product.name,
        "description": db_product.description,
        "price": db_product.price,
        "image": db_product.image,
        "category": db_product.category,
        "stock": db_product.stock,
        "brand": db_product.brand,
        "gender": db_product.gender,
        "weight": db_product.weight,
        "quantity": db_product.quantity,
        "images": db_product.images,
        "rating": db_product.rating,
        "newPrice": db_product.newPrice,
        "trending": db_product.trending,
        "frameMaterial": db_product.frameMaterial,
        "lensMaterial": db_product.lensMaterial,
        "lensFeatures": db_product.lensFeatures,
        "frameShape": db_product.frameShape,
        "lensWidth": db_product.lensWidth,
        "bridgeWidth": db_product.bridgeWidth,
        "templeLength": db_product.templeLength,
        "color": db_product.color,
        "availability": db_product.availability
    }
    
    return product_dict


def update_product(db: Session, product_id: int, product: product_schema.ProductUpdate):
    """Cập nhật thông tin sản phẩm (chỉ dành cho admin)"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Cập nhật thông tin
    if product.name is not None:
        db_product.name = product.name
    if product.description is not None:
        db_product.description = product.description
    if product.price is not None:
        db_product.price = product.price
    if product.image is not None:
        db_product.image = product.image
    if product.category is not None:
        db_product.category = product.category
    if product.stock is not None:
        db_product.stock = product.stock
    if product.brand is not None:
        db_product.brand = product.brand
    if product.gender is not None:
        db_product.gender = product.gender
    if product.weight is not None:
        db_product.weight = product.weight
    if product.quantity is not None:
        db_product.quantity = product.quantity
    if product.images is not None:
        db_product.images = product.images
    if product.rating is not None:
        db_product.rating = product.rating
    if product.newPrice is not None:
        db_product.newPrice = product.newPrice
    if product.trending is not None:
        db_product.trending = product.trending
    if product.frameMaterial is not None:
        db_product.frameMaterial = product.frameMaterial
    if product.lensMaterial is not None:
        db_product.lensMaterial = product.lensMaterial
    if product.lensFeatures is not None:
        db_product.lensFeatures = product.lensFeatures
    if product.frameShape is not None:
        db_product.frameShape = product.frameShape
    if product.lensWidth is not None:
        db_product.lensWidth = product.lensWidth
    if product.bridgeWidth is not None:
        db_product.bridgeWidth = product.bridgeWidth
    if product.templeLength is not None:
        db_product.templeLength = product.templeLength
    if product.color is not None:
        db_product.color = product.color
    if product.availability is not None:
        db_product.availability = product.availability
    
    db.commit()
    db.refresh(db_product)
    
    # Chuyển đổi từ đối tượng SQLAlchemy sang dict
    product_dict = {
        "id": db_product.id,
        "name": db_product.name,
        "description": db_product.description,
        "price": db_product.price,
        "image": db_product.image,
        "category": db_product.category,
        "stock": db_product.stock,
        "brand": db_product.brand,
        "gender": db_product.gender,
        "weight": db_product.weight,
        "quantity": db_product.quantity,
        "images": db_product.images,
        "rating": db_product.rating,
        "newPrice": db_product.newPrice,
        "trending": db_product.trending,
        "frameMaterial": db_product.frameMaterial,
        "lensMaterial": db_product.lensMaterial,
        "lensFeatures": db_product.lensFeatures,
        "frameShape": db_product.frameShape,
        "lensWidth": db_product.lensWidth,
        "bridgeWidth": db_product.bridgeWidth,
        "templeLength": db_product.templeLength,
        "color": db_product.color,
        "availability": db_product.availability
    }
    
    return product_dict


def delete_product(db: Session, product_id: int):
    """Xóa sản phẩm (chỉ dành cho admin)"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    db.delete(db_product)
    db.commit()
    
    return {"message": "Product deleted successfully"}


def get_categories(db: Session):
    """Lấy danh sách các danh mục sản phẩm"""
    categories = db.query(Product.category).distinct().all()
    return [category[0] for category in categories if category[0]]


def get_product_by_id(db: Session, product_id: int) -> Dict[str, Any]:
    """Lấy thông tin chi tiết sản phẩm theo ID"""
    return get_product(db, product_id)


def get_products_by_category(db: Session, category: str, skip: int = 0, limit: int = 20):
    """Lấy danh sách sản phẩm theo danh mục"""
    return get_products(db, skip=skip, limit=limit, category=category)


def search_products(db: Session, query: str, skip: int = 0, limit: int = 20):
    """Tìm kiếm sản phẩm theo từ khóa"""
    return get_products(db, skip=skip, limit=limit, search=query)


def get_featured_products(db: Session, limit: int = 10):
    """Lấy danh sách sản phẩm nổi bật"""
    db_products = db.query(Product).filter(Product.trending == True).limit(limit).all()
    
    # Chuyển đổi từ đối tượng SQLAlchemy sang schema Pydantic
    products = []
    for product in db_products:
        product_dict = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "image": product.image,
            "category": product.category,
            "stock": product.stock,
            "brand": product.brand,
            "gender": product.gender,
            "weight": product.weight,
            "quantity": product.quantity,
            "images": product.images,
            "rating": product.rating,
            "newPrice": product.newPrice,
            "trending": product.trending,
            "frameMaterial": product.frameMaterial,
            "lensMaterial": product.lensMaterial,
            "lensFeatures": product.lensFeatures,
            "frameShape": product.frameShape,
            "lensWidth": product.lensWidth,
            "bridgeWidth": product.bridgeWidth,
            "templeLength": product.templeLength,
            "color": product.color,
            "availability": product.availability
        }
        products.append(product_dict)
    
    return products


def get_new_arrivals(db: Session, limit: int = 10):
    """Lấy danh sách sản phẩm mới nhất"""
    db_products = db.query(Product).order_by(Product.id.desc()).limit(limit).all()
    
    # Chuyển đổi từ đối tượng SQLAlchemy sang schema Pydantic
    products = []
    for product in db_products:
        product_dict = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "image": product.image,
            "category": product.category,
            "stock": product.stock,
            "brand": product.brand,
            "gender": product.gender,
            "weight": product.weight,
            "quantity": product.quantity,
            "images": product.images,
            "rating": product.rating,
            "newPrice": product.newPrice,
            "trending": product.trending,
            "frameMaterial": product.frameMaterial,
            "lensMaterial": product.lensMaterial,
            "lensFeatures": product.lensFeatures,
            "frameShape": product.frameShape,
            "lensWidth": product.lensWidth,
            "bridgeWidth": product.bridgeWidth,
            "templeLength": product.templeLength,
            "color": product.color,
            "availability": product.availability
        }
        products.append(product_dict)
    
    return products 