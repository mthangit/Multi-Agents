from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import List, Optional
from app.database.database import get_db
from app.schemas import product as product_schema
from app.services import product_service

router = APIRouter(tags=["Products"])

logger = logging.getLogger(__name__)


@router.get("/products", response_model=dict)
def get_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách sản phẩm với các bộ lọc
    """
    products = product_service.get_products(
        db, skip, limit, category, min_price, max_price, search
    )
    return {"products": products}


@router.get("/products/{product_id}", response_model=product_schema.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Lấy thông tin chi tiết sản phẩm theo ID
    """
    return product_service.get_product(db, product_id)


@router.get("/categories", response_model=dict)
def get_categories(db: Session = Depends(get_db)):
    """
    Lấy danh sách các danh mục sản phẩm
    """
    categories = product_service.get_categories(db)
    return {"categories": categories} 