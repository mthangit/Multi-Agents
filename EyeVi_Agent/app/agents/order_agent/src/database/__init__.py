from src.database.connection import DatabaseConnection
import logging

logger = logging.getLogger("database")

def initialize_database_connections():
    """
    Initialize all database connections at application startup.
    This function should be called when the application starts to ensure
    database connections are established and ready for use.
    """
    logger.info("Initializing all database connections...")
    
    # Initialize MySQL connection
    try:
        mysql_conn = DatabaseConnection.get_instance()
        # Test the connection
        connection = mysql_conn.connect()
        if connection.is_connected():
            logger.info("MySQL database connection initialized successfully")
        else:
            logger.warning("MySQL connection initialized but not connected")
    except Exception as e:
        logger.error(f"Failed to initialize MySQL connection: {str(e)}")
        
    # Initialize MongoDB connection
    # try:
    #     mongo_conn = MongoDBConnection.get_instance()
    #     # Test the connection
    #     mongo_db = mongo_conn.connect()
    #     logger.info(f"MongoDB connection initialized successfully to database: {mongo_db.name}")
    # except Exception as e:
    #     logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
    
    logger.info("Database initialization completed")
    
# Export the database connection classes and initialization function
__all__ = ["DatabaseConnection", "MongoDBConnection", "initialize_database_connections"] 