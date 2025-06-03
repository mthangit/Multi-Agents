import mysql.connector
from mysql.connector import MySQLConnection
from src.config import settings
import logging

logger = logging.getLogger("database")

class DatabaseConnection:
    """
    MySQL database connection singleton.
    Ensures only one connection is created and reused throughout the application.
    """
    _instance = None
    _connection = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not DatabaseConnection._initialized:
            self._initialize_connection()
            DatabaseConnection._initialized = True
    
    def _initialize_connection(self):
        """Internal method to initialize the database connection"""
        try:
            logger.info("Initializing MySQL database connection...")
            DatabaseConnection._connection = mysql.connector.connect(
                host=settings.DB_HOST,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                port=settings.DB_PORT,
                pool_size=5,  # Connection pool size
                pool_name="order_agents_pool",
                autocommit=True
            )
            logger.info("MySQL database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MySQL connection: {str(e)}")
            raise

    def connect(self) -> MySQLConnection:
        """
        Get the database connection. If the connection is closed, attempt to reconnect.
        
        Returns:
            MySQLConnection: MySQL database connection
        """
        if DatabaseConnection._connection is None or not DatabaseConnection._connection.is_connected():
            # Connection lost, try to reconnect
            try:
                logger.warning("Database connection lost, attempting to reconnect...")
                self._initialize_connection()
            except Exception as e:
                logger.error(f"Failed to reconnect to database: {str(e)}")
                raise
                
        return DatabaseConnection._connection

    def close(self):
        """Close the database connection"""
        if DatabaseConnection._connection and DatabaseConnection._connection.is_connected():
            logger.info("Closing MySQL database connection")
            DatabaseConnection._connection.close()
            DatabaseConnection._connection = None
            
    @classmethod
    def get_instance(cls):
        """
        Get or create the singleton instance.
        This is a convenience method for getting the instance.
        
        Returns:
            DatabaseConnection: Singleton instance
        """
        if cls._instance is None:
            return cls()
        return cls._instance 