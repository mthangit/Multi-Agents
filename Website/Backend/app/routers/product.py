from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging
from typing import List, Dict, Any, Optional
from app.database.database import get_db
from app.schemas import product as product_schema
from app.services import product_service
from app.utils.security import get_current_user_optional

router = APIRouter(prefix="/products", tags=["Products"])

logger = logging.getLogger(__name__)


@router.get("", response_model=Dict[str, Any])
def get_products(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Lấy danh sách sản phẩm với các tùy chọn lọc và sắp xếp
    """
    products = product_service.get_products(
        db, 
        skip=skip, 
        limit=limit, 
        category=category,
        search=search,
        min_price=min_price,
        max_price=max_price,
    )
    return {"products": products, "total": len(products)}


@router.get("/{product_id}", response_model=Dict[str, Any])
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Lấy thông tin chi tiết của một sản phẩm
    """
    product = product_service.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return {"product": product}


@router.get("/category/{category}", response_model=Dict[str, Any])
def get_products_by_category(
    category: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Lấy danh sách sản phẩm theo danh mục
    """
    products = product_service.get_products_by_category(db, category, skip, limit)
    return {"products": products, "total": len(products)}


@router.get("/search/", response_model=Dict[str, Any])
def search_products(
    q: str = Query(..., min_length=1),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Tìm kiếm sản phẩm theo từ khóa
    """
    products = product_service.search_products(db, q, skip, limit)
    return {"products": products, "total": len(products)}


@router.get("/featured/", response_model=Dict[str, Any])
def get_featured_products(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Lấy danh sách sản phẩm nổi bật
    """
    products = product_service.get_featured_products(db, limit)
    return {"products": products}


@router.get("/new-arrivals/", response_model=Dict[str, Any])
def get_new_arrivals(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Lấy danh sách sản phẩm mới nhất
    """
    products = product_service.get_new_arrivals(db, limit)
    return {"products": products} 