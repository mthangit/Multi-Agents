from pymongo import MongoClient
from pymongo.database import Database
from src.config import settings
import logging

logger = logging.getLogger("database")

class MongoDBConnection:
    """
    MongoDB connection singleton class.
    Ensures only one connection is created and reused throughout the application.
    """
    _instance = None
    _client = None
    _db = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not MongoDBConnection._initialized:
            self._initialize_connection()
            MongoDBConnection._initialized = True
    
    def _initialize_connection(self):
        """Initialize the MongoDB connection"""
        try:
            logger.info("Initializing MongoDB connection...")
            MongoDBConnection._client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 seconds timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=10
            )
            # Force a command to check the connection
            MongoDBConnection._client.admin.command('ping')
            MongoDBConnection._db = MongoDBConnection._client[settings.MONGO_DB_NAME]
            logger.info("MongoDB connection established successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
            raise

    def connect(self) -> Database:
        """
        Connect to MongoDB and return the database instance.
        Uses connection parameters from settings.
        
        Returns:
            pymongo.database.Database: MongoDB database instance
        """
        if MongoDBConnection._client is None:
            # Create a new client connection if one doesn't exist
            try:
                logger.warning("MongoDB connection lost, attempting to reconnect...")
                self._initialize_connection()
            except Exception as e:
                logger.error(f"Failed to reconnect to MongoDB: {str(e)}")
                raise
                
        return MongoDBConnection._db

    def get_collection(self, collection_name: str):
        """
        Get a MongoDB collection by name.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            pymongo.collection.Collection: MongoDB collection
        """
        db = self.connect()
        return db[collection_name]

    def close(self):
        """
        Close the MongoDB connection.
        """
        if MongoDBConnection._client:
            logger.info("Closing MongoDB connection")
            MongoDBConnection._client.close()
            MongoDBConnection._client = None
            MongoDBConnection._db = None
    
    @classmethod
    def get_instance(cls):
        """
        Get or create the singleton instance.
        
        Returns:
            MongoDBConnection: Singleton instance
        """
        if cls._instance is None:
            return cls()
        return cls._instance 