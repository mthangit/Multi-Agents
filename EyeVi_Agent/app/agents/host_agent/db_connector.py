import os
import logging
import pymysql
from pymysql.cursors import DictCursor
from typing import Dict, List, Optional, Any

# Setup logging
logger = logging.getLogger(__name__)

class DatabaseConnector:
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST", "eyevi.devsecopstech.click")
        self.port = int(os.getenv("MYSQL_PORT", "3306"))
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "123456")
        self.database = os.getenv("MYSQL_DATABASE", "eyevi_db")
        self.connection = None
        
        self.connect()
    
    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=DictCursor,
                charset='utf8mb4'
            )
            logger.info(f"✅ Kết nối thành công đến MySQL database: {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"❌ Lỗi kết nối database: {e}")
            self.connection = None
    
    def get_connection(self):
        if self.connection is None or not self.connection.open:
            self.connect()
        return self.connection
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                product = cursor.fetchone()
                
                # Xử lý trường images nếu có
                if product and product.get('images'):
                    try:
                        # Nếu images là chuỗi JSON, parse nó
                        import json
                        images_list = json.loads(product['images'])
                        # Lấy ảnh đầu tiên nếu có
                        if images_list and len(images_list) > 0:
                            product['image_url'] = images_list[0]
                    except Exception as e:
                        logger.warning(f"Không thể parse trường images: {e}")
                
                # Sử dụng trường image nếu không có images
                if product and not product.get('image_url') and product.get('image'):
                    product['image_url'] = product['image']
                
                return product
                
        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {str(e)}")
            # Thử kết nối lại nếu mất kết nối
            self.connect()
            return None
    
    def get_products_by_ids(self, product_ids: List[str]) -> List[Dict]:
        if not product_ids:
            return []
            
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                placeholders = ', '.join(['%s'] * len(product_ids))
                query = f"SELECT * FROM products WHERE id IN ({placeholders})"
                cursor.execute(query, product_ids)
                products = cursor.fetchall()
                
                # Xử lý trường images cho mỗi sản phẩm
                for product in products:
                    if product.get('images'):
                        try:
                            import json
                            images_list = json.loads(product['images'])
                            if images_list and len(images_list) > 0:
                                product['image_url'] = images_list[0]
                        except Exception as e:
                            logger.warning(f"Không thể parse trường images: {e}")
                    
                    # Sử dụng trường image nếu không có images
                    if not product.get('image_url') and product.get('image'):
                        product['image_url'] = product['image']
                
                return products
                
        except Exception as e:
            logger.error(f"Error getting products by IDs: {str(e)}")
            self.connect()
            return []
    
    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()
            logger.info("Database connection closed")

# Singleton instance
db_connector = DatabaseConnector() 