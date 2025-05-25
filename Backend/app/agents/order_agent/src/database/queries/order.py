from src.database.connection import DatabaseConnection
from src.database.queries.cart import CartQuery
from typing import Optional, Dict, List

class OrderQuery:
    def __init__(self):
        self.db = DatabaseConnection().connect()
        self.cart_query = CartQuery()
    
    def create_order_from_cart(self, user_id: int, shipping_address: str, phone: str, payment_method: str) -> Optional[int]:
        """Tạo đơn hàng từ giỏ hàng, bao gồm kiểm tra hàng tồn kho"""
        cursor = self.db.cursor()
        try:
            # 1. Lấy giỏ hàng hiện tại
            cart_items = self.cart_query.get_cart_items(user_id)
            if not cart_items:
                return None  # Giỏ hàng trống
            
            # 2. Kiểm tra tồn kho cho từng sản phẩm
            for item in cart_items:
                if item['quantity'] > item['stock']:
                    raise Exception(f"Sản phẩm '{item['name']}' không đủ hàng (chỉ còn {item['stock']})")
            
            # 3. Tính tổng giá trị đơn hàng
            total_amount = sum(item['total_price'] for item in cart_items)
            
            # 4. Tạo đơn hàng mới
            cursor.execute(
                """
                INSERT INTO orders (user_id, total_amount, shipping_address, phone, payment_method, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, total_amount, shipping_address, phone, payment_method, 'pending')
            )
            order_id = cursor.lastrowid
            
            # 5. Thêm chi tiết đơn hàng
            for item in cart_items:
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, item['product_id'], item['quantity'], item['price'])
                )
                
                # 6. Cập nhật số lượng tồn kho
                cursor.execute(
                    "UPDATE products SET stock = stock - %s WHERE id = %s",
                    (item['quantity'], item['product_id'])
                )
            
            # 7. Xóa giỏ hàng sau khi đặt hàng thành công
            self.cart_query.clear_cart(user_id)
            
            self.db.commit()
            return order_id
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            cursor.close()
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """Lấy thông tin đơn hàng và chi tiết đơn hàng theo ID"""
        cursor = self.db.cursor(dictionary=True)
        
        # Lấy thông tin đơn hàng
        cursor.execute(
            """
            SELECT o.*, u.name as user_name, u.email as user_email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
            """,
            (order_id,)
        )
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            return None
        
        # Lấy chi tiết đơn hàng
        cursor.execute(
            """
            SELECT oi.*, p.name as product_name, p.description as product_description
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
            """,
            (order_id,)
        )
        order_items = cursor.fetchall()
        order['items'] = order_items
        
        cursor.close()
        return order
    
    def check_stock(self, product_id: int) -> Optional[Dict]:
        """Kiểm tra tồn kho của sản phẩm"""
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, stock, price FROM products WHERE id = %s",
            (product_id,)
        )
        product = cursor.fetchone()
        cursor.close()
        return product 