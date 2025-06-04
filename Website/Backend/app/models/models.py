from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
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
    address_line = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    is_default = Column(Boolean, default=False)
    phone = Column(String(20))

    # Relationships
    user = relationship("User", back_populates="addresses")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text)
    price = Column(Float)
    image_url = Column(String(255))
    category = Column(String(100), index=True)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cart_details = relationship("CartDetail", back_populates="product")
    invoice_details = relationship("InvoiceDetail", back_populates="product")
    wishlist_details = relationship("WishlistDetail", back_populates="product")


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
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)

    # Relationships
    cart = relationship("Cart", back_populates="cart_details")
    product = relationship("Product", back_populates="cart_details")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    shipping_address = Column(String(255))
    phone = Column(String(20))
    payment_method = Column(String(50))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="invoices")
    invoice_details = relationship("InvoiceDetail", back_populates="invoice")


class InvoiceDetail(Base):
    __tablename__ = "invoice_details"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float)

    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_details")
    product = relationship("Product", back_populates="invoice_details")


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
    product_id = Column(Integer, ForeignKey("products.id"))

    # Relationships
    wishlist = relationship("Wishlist", back_populates="wishlist_details")
    product = relationship("Product", back_populates="wishlist_details") 