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
        Get a product by its ID.
        
        Args:
            product_id (int): The ID of the product to retrieve
            
        Returns:
            Optional[Dict]: The product data as a dictionary, or None if not found
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE _id = %s", (product_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {str(e)}")
            # Re-establish connection if needed
            self.db = self.db_connection.connect()
            raise

    def get_product_by_name(self, name: str) -> List[Dict]:
        """
        Get products matching a name pattern.
        
        Args:
            name (str): The name pattern to search for
            
        Returns:
            List[Dict]: A list of matching products
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE name LIKE %s", (f"%{name}%",))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting products by name '{name}': {str(e)}")
            # Re-establish connection if needed
            self.db = self.db_connection.connect()
            raise 