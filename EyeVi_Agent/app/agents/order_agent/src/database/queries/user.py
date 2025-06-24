from src.database.connection import DatabaseConnection
from typing import Optional, Dict, List
import logging

logger = logging.getLogger("database.queries")

class UserQuery:
    """
    Class for executing user-related database queries.
    Uses the singleton database connection.
    """
    
    def __init__(self):
        # Get the singleton database connection
        self.db_connection = DatabaseConnection.get_instance()
        # Use the established connection
        self.db = self.db_connection.connect()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Lấy thông tin người dùng theo ID.
        Args:
            user_id (int): ID người dùng
        Returns:
            Optional[Dict]: Thông tin người dùng hoặc None nếu không tìm thấy
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            self.db = self.db_connection.connect()
            raise

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Lấy thông tin người dùng theo email.
        Args:
            email (str): Email người dùng
        Returns:
            Optional[Dict]: Thông tin người dùng hoặc None nếu không tìm thấy
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting user by email '{email}': {str(e)}")
            self.db = self.db_connection.connect()
            raise

    def create_user(self, name: str, email: str, phone: str = "", address: str = "") -> Optional[int]:
        """
        Tạo người dùng mới.
        Args:
            name (str): Tên người dùng
            email (str): Email người dùng (unique)
            phone (str): Số điện thoại
            address (str): Địa chỉ
        Returns:
            Optional[int]: ID người dùng mới tạo hoặc None nếu thất bại
        """
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (name, email, phone, address)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, phone, address)
            )
            user_id = cursor.lastrowid
            self.db.commit()
            return user_id
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user with email '{email}': {str(e)}")
            raise
        finally:
            cursor.close()

    def update_user(self, user_id: int, name: str = None, email: str = None, phone: str = None, address: str = None) -> bool:
        """
        Cập nhật thông tin người dùng.
        Args:
            user_id (int): ID người dùng
            name (str): Tên mới (optional)
            email (str): Email mới (optional)
            phone (str): Số điện thoại mới (optional)
            address (str): Địa chỉ mới (optional)
        Returns:
            bool: True nếu cập nhật thành công, False nếu thất bại
        """
        cursor = self.db.cursor()
        try:
            # Tạo câu query động dựa trên các tham số được cung cấp
            update_fields = []
            values = []
            
            if name is not None:
                update_fields.append("name = %s")
                values.append(name)
            if email is not None:
                update_fields.append("email = %s")
                values.append(email)
            if phone is not None:
                update_fields.append("phone = %s")
                values.append(phone)
            if address is not None:
                update_fields.append("address = %s")
                values.append(address)
            
            if not update_fields:
                return False  # Không có gì để cập nhật
            
            values.append(user_id)  # Thêm user_id vào cuối cho WHERE clause
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, values)
            
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return False
        finally:
            cursor.close() 