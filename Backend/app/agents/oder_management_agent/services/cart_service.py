from sqlalchemy.orm import Session
from ..models.cart import Cart, CartDetail
from ..models.product import Product

class CartService:
    @staticmethod
    def get_cart(db: Session, user_id: int):
        """Lấy thông tin giỏ hàng của người dùng"""
        try:
            cart = db.query(Cart).filter(Cart.user_id == user_id).first()
            
            if not cart:
                return {"status": "error", "message": "Cart not found"}
            
            items = []
            total = 0
            
            for item in cart.items:
                product = db.query(Product).filter(Product._id == item.product_id).first()
                if product:
                    item_total = float(product.price) * item.quantity
                    total += item_total
                    items.append({
                        "id": item.id,
                        "product_id": item.product_id,
                        "name": product.name,
                        "price": float(product.price),
                        "quantity": item.quantity,
                        "image": product.image,
                        "total": item_total
                    })
            
            return {
                "status": "success",
                "cart": {
                    "id": cart.id,
                    "items": items,
                    "total": total
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def add_to_cart(db: Session, user_id: int, product_id: str, quantity: int = 1):
        """Thêm sản phẩm vào giỏ hàng"""
        try:
            # Kiểm tra sản phẩm tồn tại
            product = db.query(Product).filter(Product._id == product_id).first()
            if not product:
                return {"status": "error", "message": "Product not found"}
            
            # Kiểm tra số lượng tồn kho
            if product.stock < quantity:
                return {"status": "error", "message": "Insufficient stock"}
            
            # Lấy hoặc tạo giỏ hàng
            cart = db.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                cart = Cart(user_id=user_id)
                db.add(cart)
                db.flush()
            
            # Kiểm tra sản phẩm đã có trong giỏ hàng
            cart_item = db.query(CartDetail).filter(
                CartDetail.cart_id == cart.id,
                CartDetail.product_id == product_id
            ).first()
            
            if cart_item:
                # Cập nhật số lượng
                cart_item.quantity += quantity
            else:
                # Thêm mới vào giỏ hàng
                cart_item = CartDetail(
                    cart_id=cart.id,
                    product_id=product_id,
                    quantity=quantity
                )
                db.add(cart_item)
            
            db.commit()
            return {"status": "success", "message": "Product added to cart"}
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)}

    @staticmethod
    def update_cart_item(db: Session, cart_item_id: int, quantity: int):
        """Cập nhật số lượng sản phẩm trong giỏ hàng"""
        try:
            cart_item = db.query(CartDetail).filter(CartDetail.id == cart_item_id).first()
            if not cart_item:
                return {"status": "error", "message": "Cart item not found"}
            
            # Kiểm tra số lượng tồn kho
            product = db.query(Product).filter(Product._id == cart_item.product_id).first()
            if product.stock < quantity:
                return {"status": "error", "message": "Insufficient stock"}
            
            cart_item.quantity = quantity
            db.commit()
            return {"status": "success", "message": "Cart updated"}
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)}

    @staticmethod
    def remove_from_cart(db: Session, cart_item_id: int):
        """Xóa sản phẩm khỏi giỏ hàng"""
        try:
            cart_item = db.query(CartDetail).filter(CartDetail.id == cart_item_id).first()
            if not cart_item:
                return {"status": "error", "message": "Cart item not found"}
            
            db.delete(cart_item)
            db.commit()
            return {"status": "success", "message": "Item removed from cart"}
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)} 