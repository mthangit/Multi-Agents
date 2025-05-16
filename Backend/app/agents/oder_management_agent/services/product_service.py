from sqlalchemy.orm import Session
from ..models.product import Product

class ProductService:
    @staticmethod
    def search_products(db: Session, query: str = None, category: str = None, brand: str = None, min_price: float = None, max_price: float = None):
        """Tìm kiếm sản phẩm theo các tiêu chí"""
        try:
            # Bắt đầu với query cơ bản
            products_query = db.query(Product)

            # Thêm các điều kiện tìm kiếm
            if query:
                products_query = products_query.filter(
                    Product.name.ilike(f"%{query}%") | 
                    Product.description.ilike(f"%{query}%")
                )
            if category:
                products_query = products_query.filter(Product.category == category)
            if brand:
                products_query = products_query.filter(Product.brand == brand)
            if min_price is not None:
                products_query = products_query.filter(Product.price >= min_price)
            if max_price is not None:
                products_query = products_query.filter(Product.price <= max_price)

            # Thực hiện query và lấy kết quả
            products = products_query.all()
            
            return {
                "status": "success",
                "products": [
                    {
                        "id": product._id,
                        "name": product.name,
                        "description": product.description,
                        "price": float(product.price),
                        "image": product.image,
                        "stock": product.stock
                    }
                    for product in products
                ]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_product_details(db: Session, product_id: int):
        """Lấy thông tin chi tiết sản phẩm"""
        try:
            product = db.query(Product).filter(Product._id == product_id).first()
            
            if not product:
                return {"status": "error", "message": "Product not found"}
            
            return {
                "status": "success",
                "product": {
                    "id": product._id,
                    "name": product.name,
                    "description": product.description,
                    "brand": product.brand,
                    "category": product.category,
                    "price": float(product.price),
                    "stock": product.stock,
                    "image": product.image,
                    "rating": product.rating,
                    "specifications": {
                        "frameMaterial": product.frameMaterial,
                        "lensMaterial": product.lensMaterial,
                        "lensFeatures": product.lensFeatures,
                        "frameShape": product.frameShape,
                        "lensWidth": product.lensWidth,
                        "bridgeWidth": product.bridgeWidth,
                        "templeLength": product.templeLength,
                        "color": product.color
                    }
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def check_stock(db: Session, product_id: int) -> dict:
        """Kiểm tra số lượng sản phẩm trong kho
        
        Args:
            db (Session): Database session
            product_id (int): ID của sản phẩm
            
        Returns:
            dict: Thông tin về số lượng sản phẩm trong kho
        """
        try:
            product = db.query(Product).filter(Product._id == product_id).first()
            
            if not product:
                return {"status": "error", "message": "Product not found"}
                
            return {
                "status": "success",
                "data": {
                    "product_id": product_id,
                    "stock": product.stock
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)} 