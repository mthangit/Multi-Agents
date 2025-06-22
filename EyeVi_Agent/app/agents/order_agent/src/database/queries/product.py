from src.database.connection import DatabaseConnection
from typing import Optional, Dict, List
import logging

logger = logging.getLogger("database.queries")

class ProductQuery:
    """
    Class for executing product-related database queries.
    Uses the singleton database connection.
    """
    
    def __init__(self):
        # Get the singleton database connection
        self.db_connection = DatabaseConnection.get_instance()
        # Use the established connection
        self.db = self.db_connection.connect()
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """
        Lấy thông tin sản phẩm theo ID.
        Args:
            product_id (int): ID sản phẩm
        Returns:
            Optional[Dict]: Thông tin sản phẩm hoặc None nếu không tìm thấy
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {str(e)}")
            self.db = self.db_connection.connect()
            raise

    def get_product_by_name(self, name: str) -> List[Dict]:
        """
        Lấy danh sách sản phẩm theo tên (tìm kiếm gần đúng).
        Args:
            name (str): Tên sản phẩm cần tìm
        Returns:
            List[Dict]: Danh sách sản phẩm phù hợp
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE name LIKE %s", (f"%{name}%",))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting products by name '{name}': {str(e)}")
            self.db = self.db_connection.connect()
            raise 