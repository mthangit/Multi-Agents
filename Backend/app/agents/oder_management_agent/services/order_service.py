from sqlalchemy.orm import Session
from ..models.order import Invoice, InvoiceDetail
from ..models.cart import Cart, CartDetail
from ..models.product import Product

class OrderService:
    @staticmethod
    def create_order(db: Session, user_id: int, address_id: int, payment_method: str):
        """Tạo đơn hàng mới từ giỏ hàng"""
        try:
            # Lấy giỏ hàng
            cart = db.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart or not cart.items:
                return {"status": "error", "message": "Cart is empty"}

            # Tính toán tổng tiền và kiểm tra tồn kho
            total_items = 0
            actual_price = 0
            total_price = 0
            order_items = []

            for item in cart.items:
                product = db.query(Product).filter(Product._id == item.product_id).first()
                if not product:
                    return {"status": "error", "message": f"Product {item.product_id} not found"}
                
                if product.stock < item.quantity:
                    return {"status": "error", "message": f"Insufficient stock for product {product.name}"}
                
                item_total = float(product.price) * item.quantity
                actual_price += item_total
                total_items += item.quantity
                
                order_items.append({
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": float(product.price)
                })

            # Tạo đơn hàng mới
            order = Invoice(
                user_id=user_id,
                address_id=address_id,
                total_items=total_items,
                actual_price=actual_price,
                total_price=actual_price,  # Có thể thêm phí vận chuyển, giảm giá, etc.
                payment_method=payment_method
            )
            db.add(order)
            db.flush()

            # Tạo chi tiết đơn hàng
            for item in order_items:
                order_detail = InvoiceDetail(
                    invoice_id=order.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
                db.add(order_detail)

                # Cập nhật số lượng tồn kho
                product = db.query(Product).filter(Product._id == item["product_id"]).first()
                product.stock -= item["quantity"]

            # Xóa giỏ hàng
            for item in cart.items:
                db.delete(item)
            db.delete(cart)

            db.commit()
            return {
                "status": "success",
                "order": {
                    "id": order.id,
                    "total_items": order.total_items,
                    "total_price": float(order.total_price),
                    "payment_method": order.payment_method,
                    "order_status": order.order_status
                }
            }
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_status(db: Session, order_id: int):
        """Lấy trạng thái đơn hàng"""
        try:
            order = db.query(Invoice).filter(Invoice.id == order_id).first()
            if not order:
                return {"status": "error", "message": "Order not found"}

            items = []
            for item in order.items:
                product = db.query(Product).filter(Product._id == item.product_id).first()
                if product:
                    items.append({
                        "product_id": item.product_id,
                        "name": product.name,
                        "quantity": item.quantity,
                        "price": float(item.price),
                        "image": product.image
                    })

            return {
                "status": "success",
                "order": {
                    "id": order.id,
                    "total_items": order.total_items,
                    "total_price": float(order.total_price),
                    "payment_method": order.payment_method,
                    "payment_status": order.payment_status,
                    "order_status": order.order_status,
                    "items": items,
                    "created_at": order.created_at
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_user_orders(db: Session, user_id: int):
        """Lấy danh sách đơn hàng của người dùng"""
        try:
            orders = db.query(Invoice).filter(Invoice.user_id == user_id).all()
            
            order_list = []
            for order in orders:
                order_list.append({
                    "id": order.id,
                    "total_items": order.total_items,
                    "total_price": float(order.total_price),
                    "payment_method": order.payment_method,
                    "payment_status": order.payment_status,
                    "order_status": order.order_status,
                    "created_at": order.created_at
                })

            return {
                "status": "success",
                "orders": order_list
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def cancel_order(db: Session, order_id: int):
        """Hủy đơn hàng"""
        try:
            order = db.query(Invoice).filter(Invoice.id == order_id).first()
            if not order:
                return {"status": "error", "message": "Order not found"}

            if order.order_status == "cancelled":
                return {"status": "error", "message": "Order is already cancelled"}

            # Cập nhật trạng thái đơn hàng
            order.order_status = "cancelled"
            order.payment_status = "refunded"

            # Hoàn trả số lượng tồn kho
            for item in order.items:
                product = db.query(Product).filter(Product._id == item.product_id).first()
                if product:
                    product.stock += item.quantity

            db.commit()
            return {"status": "success", "message": "Order cancelled successfully"}
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)} 