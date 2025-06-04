from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text, cast
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    is_admin = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    addresses = relationship("Address", back_populates="user")
    carts = relationship("Cart", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")
    wishlists = relationship("Wishlist", back_populates="user")


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100), nullable=True)
    country = Column(String(100))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="addresses")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text)
    price = Column(Float)
    image = Column(String(255))
    brand = Column(String(255), nullable=True)
    category = Column(String(100), index=True)
    gender = Column(String(20), nullable=True)
    weight = Column(String(20), nullable=True)
    quantity = Column(Integer, nullable=True)
    images = Column(String(255), nullable=True)
    rating = Column(Float, nullable=True)
    newPrice = Column(Float, nullable=True)
    trending = Column(Boolean, nullable=True)
    frameMaterial = Column(String(100), nullable=True)
    lensMaterial = Column(String(100), nullable=True)
    lensFeatures = Column(String(100), nullable=True)
    frameShape = Column(String(50), nullable=True)
    lensWidth = Column(String(10), nullable=True)
    bridgeWidth = Column(String(10), nullable=True)
    templeLength = Column(String(10), nullable=True)
    color = Column(String(50), nullable=True)
    availability = Column(String(20), nullable=True)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Loại bỏ các mối quan hệ ngược từ Product để tránh lỗi


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="carts")
    cart_details = relationship("CartDetail", back_populates="cart")


class CartDetail(Base):
    __tablename__ = "cart_details"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"))
    product_id = Column(String(36))
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cart = relationship("Cart", back_populates="cart_details")
    product = relationship("Product", primaryjoin="and_(foreign(CartDetail.product_id) == cast(Product.id, String))")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    address_id = Column(Integer, ForeignKey("addresses.id"))
    total_items = Column(Integer)
    actual_price = Column(Float)
    total_price = Column(Float)
    payment_method = Column(String(50))
    payment_status = Column(String(50), default="pending")
    order_status = Column(String(50), default="processing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="invoices")
    address = relationship("Address")
    invoice_details = relationship("InvoiceDetail", back_populates="invoice")


class InvoiceDetail(Base):
    __tablename__ = "invoice_details"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    product_id = Column(String(36))
    quantity = Column(Integer)
    price = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_details")
    product = relationship("Product", primaryjoin="and_(foreign(InvoiceDetail.product_id) == cast(Product.id, String))")


class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="wishlists")
    wishlist_details = relationship("WishlistDetail", back_populates="wishlist")


class WishlistDetail(Base):
    __tablename__ = "wishlist_details"

    id = Column(Integer, primary_key=True, index=True)
    wishlist_id = Column(Integer, ForeignKey("wishlist.id"))
    product_id = Column(String(36))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    wishlist = relationship("Wishlist", back_populates="wishlist_details")
    product = relationship("Product", primaryjoin="and_(foreign(WishlistDetail.product_id) == cast(Product.id, String))") 