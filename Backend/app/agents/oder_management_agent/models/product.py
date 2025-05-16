from sqlalchemy import Column, Integer, String, Text, Float, DECIMAL, JSON, Boolean
from .base import Base

class Product(Base):
    """Model cho bảng products"""
    __tablename__ = "products"

    _id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    brand = Column(String(255))
    category = Column(String(100))
    gender = Column(String(20))
    weight = Column(String(20))
    quantity = Column(Integer)
    images = Column(JSON)
    rating = Column(Float)
    newPrice = Column(DECIMAL(15, 2))
    trending = Column(Boolean)
    frameMaterial = Column(String(100))
    lensMaterial = Column(String(100))
    lensFeatures = Column(String(100))
    frameShape = Column(String(50))
    lensWidth = Column(String(10))
    bridgeWidth = Column(String(10))
    templeLength = Column(String(10))
    color = Column(String(50))
    availability = Column(String(20))
    price = Column(DECIMAL(15, 2), nullable=False)
    image = Column(String(255))
    stock = Column(Integer, default=0) 