from src.database.connection import DatabaseConnection
from typing import Optional, Dict, List

class CartQuery:
    def __init__(self):
        self.db = DatabaseConnection().connect()
    
    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> bool:
        """Thêm sản phẩm vào giỏ hàng hoặc cập nhật số lượng nếu đã tồn tại"""
        cursor = self.db.cursor()
        try:
            # Kiểm tra sản phẩm đã có trong giỏ chưa
            cursor.execute(
                "SELECT id, quantity FROM cart WHERE user_id = %s AND product_id = %s",
                (user_id, product_id)
            )
            cart_item = cursor.fetchone()
            
            if cart_item:
                # Cập nhật số lượng nếu đã có trong giỏ
                cursor.execute(
                    "UPDATE cart SET quantity = quantity + %s WHERE id = %s",
                    (quantity, cart_item[0])
                )
            else:
                # Thêm mới nếu chưa có trong giỏ
                cursor.execute(
                    "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                    (user_id, product_id, quantity)
                )
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error adding to cart: {e}")
            return False
        finally:
            cursor.close()
    
    def get_cart_items(self, user_id: int) -> List[Dict]:
        """Lấy danh sách sản phẩm trong giỏ hàng của user"""
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.stock, 
                   (p.price * c.quantity) as total_price
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
            """,
            (user_id,)
        )
        cart_items = cursor.fetchall()
        cursor.close()
        return cart_items
    
    def clear_cart(self, user_id: int) -> bool:
        """Xóa toàn bộ giỏ hàng của user"""
        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            return False
        finally:
            cursor.close()
    
    def remove_cart_item(self, user_id: int, product_id: int) -> bool:
        """Xóa một sản phẩm khỏi giỏ hàng"""
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "DELETE FROM cart WHERE user_id = %s AND product_id = %s", 
                (user_id, product_id)
            )
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            return False
        finally:
            cursor.close() 