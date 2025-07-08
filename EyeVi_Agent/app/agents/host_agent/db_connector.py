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
                cursor.execute("SELECT id, name, images, newPrice FROM products WHERE id = %s", (product_id,))
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
                query = f"SELECT id, name, images, newPrice FROM products WHERE id IN ({placeholders})"
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
    
    def get_all_products(self) -> List[Dict]:
        """
        Lấy toàn bộ sản phẩm từ database với tất cả các trường
        """
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                query = """
                SELECT id, name, description, brand, category, gender, weight, 
                       quantity, images, rating, newPrice, trending, frameMaterial, 
                       lensMaterial, lensFeatures, frameShape, lensWidth, bridgeWidth, 
                       templeLength, color, availability, price, image, stock
                FROM products
                """
                cursor.execute(query)
                products = cursor.fetchall()
                
                # Xử lý trường images cho mỗi sản phẩm và chuyển id thành _id
                for product in products:
                    # Chuyển id thành _id để tương thích với frontend
                    product['_id'] = product.pop('id')
                    
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
            logger.error(f"Error getting all products: {str(e)}")
            self.connect()
            return []
    
    def get_products_paginated(self, page: int = 1, limit: int = 20, search: str = None, category: str = None, brand: str = None) -> Dict:
        """
        Lấy sản phẩm có phân trang với các filter tùy chọn
        
        Args:
            page: Trang hiện tại (bắt đầu từ 1)
            limit: Số sản phẩm mỗi trang (tối đa 100)
            search: Tìm kiếm theo tên sản phẩm
            category: Lọc theo danh mục
            brand: Lọc theo thương hiệu
            
        Returns:
            Dict chứa products, pagination info
        """
        try:
            # Giới hạn limit tối đa
            limit = min(limit, 100)
            offset = (page - 1) * limit
            
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Xây dựng WHERE clause
                where_conditions = []
                params = []
                
                if search:
                    where_conditions.append("name LIKE %s")
                    params.append(f"%{search}%")
                
                if category:
                    where_conditions.append("category = %s")
                    params.append(category)
                    
                if brand:
                    where_conditions.append("brand = %s")
                    params.append(brand)
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # Query để đếm tổng số sản phẩm
                count_query = f"SELECT COUNT(*) as total FROM products {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()['total']
                
                # Query để lấy sản phẩm với phân trang
                products_query = f"""
                SELECT id, name, description, brand, category, gender, weight, 
                       quantity, images, rating, newPrice, trending, frameMaterial, 
                       lensMaterial, lensFeatures, frameShape, lensWidth, bridgeWidth, 
                       templeLength, color, availability, price, image, stock
                FROM products 
                {where_clause}
                ORDER BY id DESC
                LIMIT %s OFFSET %s
                """
                
                cursor.execute(products_query, params + [limit, offset])
                products = cursor.fetchall()
                
                # Xử lý trường images cho mỗi sản phẩm và chuyển id thành _id
                for product in products:
                    # Chuyển id thành _id để tương thích với frontend
                    product['_id'] = product.pop('id')
                    
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
                
                # Tính toán thông tin phân trang
                total_pages = (total_count + limit - 1) // limit  # Ceiling division
                has_next = page < total_pages
                has_prev = page > 1
                
                return {
                    "products": products,
                    "pagination": {
                        "current_page": page,
                        "per_page": limit,
                        "total_items": total_count,
                        "total_pages": total_pages,
                        "has_next": has_next,
                        "has_prev": has_prev,
                        "next_page": page + 1 if has_next else None,
                        "prev_page": page - 1 if has_prev else None
                    },
                    "filters": {
                        "search": search,
                        "category": category,
                        "brand": brand
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting paginated products: {str(e)}")
            self.connect()
            return {
                "products": [],
                "pagination": {
                    "current_page": 1,
                    "per_page": limit,
                    "total_items": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False,
                    "next_page": None,
                    "prev_page": None
                },
                "filters": {
                    "search": search,
                    "category": category,
                    "brand": brand
                }
            }

    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()
            logger.info("Database connection closed")

# Singleton instance
db_connector = DatabaseConnector() 