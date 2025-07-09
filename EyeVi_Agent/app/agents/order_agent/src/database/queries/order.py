from src.database.connection import DatabaseConnection
from src.database.queries.user import UserQuery
from typing import Optional, Dict, List

class OrderQuery:
    def __init__(self):
        self.db = DatabaseConnection().connect()
        self.user_query = UserQuery()
    
    def create_order(self, user_id: int, items: List[Dict], shipping_address: str = "", phone: str = "", payment_method: str = "COD") -> Optional[int]:
        """
        Tạo đơn hàng trực tiếp từ danh sách sản phẩm, bao gồm kiểm tra hàng tồn kho
        Args:
            user_id: ID người dùng
            items: Danh sách sản phẩm [{'product_id': int, 'quantity': int}, ...]
            shipping_address: Địa chỉ giao hàng (nếu trống sẽ lấy từ user)
            phone: Số điện thoại (nếu trống sẽ lấy từ user)
            payment_method: Phương thức thanh toán
        Returns:
            Optional[int]: ID đơn hàng mới tạo hoặc None nếu thất bại
        """
        cursor = self.db.cursor()
        try:
            if not items:
                return None  # Không có sản phẩm
            
            # 1. Lấy thông tin user
            user = self.user_query.get_user_by_id(user_id)
            if not user:
                raise Exception(f"Người dùng ID {user_id} không tồn tại")
            
            # 2. Sử dụng thông tin user nếu không có shipping_address hoặc phone
            final_shipping_address = shipping_address.strip() if shipping_address.strip() else user.get('address', 'Thủ Đức, TP.HCM')
            final_phone = phone.strip() if phone.strip() else user.get('phone', '0901234567')
                        
            # 3. Kiểm tra tồn kho và tính tổng cho từng sản phẩm
            validated_items = []
            total_items = 0
            total_price = 0
            
            for item in items:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 1)
                
                # Lấy thông tin sản phẩm
                cursor.execute(
                    "SELECT id, name, price, stock FROM products WHERE id = %s",
                    (product_id,)
                )
                product = cursor.fetchone()
                
                if not product:
                    raise Exception(f"Sản phẩm ID {product_id} không tồn tại")
                
                product_id, name, price, stock = product
                
                if quantity > stock:
                    raise Exception(f"Sản phẩm '{name}' không đủ hàng (chỉ còn {stock})")
                
                validated_items.append({
                    'product_id': product_id,
                    'name': name,
                    'price': price,
                    'quantity': quantity
                })
                
                total_items += quantity
                total_price += price * quantity
            
            actual_price = total_price  # Có thể áp dụng giảm giá sau
            
            # 4. Tạo đơn hàng mới với thông tin user và payment
            cursor.execute(
                """
                INSERT INTO orders (user_id, total_items, total_price, actual_price, shipping_address, phone, payment, order_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, total_items, total_price, actual_price, final_shipping_address, final_phone, payment_method, 'pending')
            )
            order_id = cursor.lastrowid
            
            # 5. Thêm chi tiết đơn hàng và cập nhật tồn kho
            for item in validated_items:
                cursor.execute(
                    """
                    INSERT INTO order_details (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, item['product_id'], item['quantity'], item['price'])
                )
                
                # Cập nhật số lượng tồn kho
                cursor.execute(
                    "UPDATE products SET stock = stock - %s WHERE id = %s",
                    (item['quantity'], item['product_id'])
                )
            
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
        
        # Lấy thông tin đơn hàng bao gồm cột payment
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
            SELECT od.*, p.name as product_name, p.description as product_description
            FROM order_details od
            JOIN products p ON od.product_id = p.id
            WHERE od.order_id = %s
            """,
            (order_id,)
        )
        order_items = cursor.fetchall()
        order['items'] = order_items
        
        cursor.close()
        return order
    
    def get_orders_by_user_id(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Lấy danh sách đơn hàng của user
        Args:
            user_id: ID người dùng
            limit: Số lượng đơn hàng tối đa (mặc định 10)
        Returns:
            List[Dict]: Danh sách đơn hàng
        """
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT o.*, u.name as user_name, u.email as user_email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
            LIMIT %s
            """,
            (user_id, limit)
        )
        orders = cursor.fetchall()
        cursor.close()
        return orders
    
    def update_order(self, order_id: int, shipping_address: str = None, phone: str = None, payment_method: str = None) -> bool:
        """
        Cập nhật thông tin đơn hàng
        Args:
            order_id: ID đơn hàng cần cập nhật
            shipping_address: Địa chỉ giao hàng mới (tùy chọn)
            phone: Số điện thoại mới (tùy chọn) 
            payment_method: Phương thức thanh toán mới (tùy chọn)
        Returns:
            bool: True nếu cập nhật thành công, False nếu thất bại
        """
        cursor = self.db.cursor()
        try:
            # Xây dựng câu query UPDATE động
            update_fields = []
            update_values = []
            
            if shipping_address is not None:
                update_fields.append("shipping_address = %s")
                update_values.append(shipping_address)
            
            if phone is not None:
                update_fields.append("phone = %s")
                update_values.append(phone)
                
            if payment_method is not None:
                update_fields.append("payment = %s")
                update_values.append(payment_method)
            
            if not update_fields:
                return False  # Không có gì để cập nhật
            
            update_values.append(order_id)  # Thêm order_id vào cuối cho WHERE clause
            
            query = f"""
                UPDATE orders 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            
            cursor.execute(query, update_values)
            self.db.commit()
            
            return cursor.rowcount > 0  # Trả về True nếu có ít nhất 1 row được cập nhật
            
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            cursor.close()
    
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