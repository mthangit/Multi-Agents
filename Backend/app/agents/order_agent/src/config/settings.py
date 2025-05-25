import os
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings using Pydantic for validation
    """
    # Database Configuration
    DB_HOST: str = Field(default=os.getenv("MYSQL_HOST", "localhost"))
    DB_PORT: int = Field(default=int(os.getenv("MYSQL_PORT", "3306")))
    DB_USER: str = Field(default=os.getenv("MYSQL_USER", "root"))
    DB_PASSWORD: str = Field(default=os.getenv("MYSQL_PASSWORD", ""))
    DB_NAME: str = Field(default=os.getenv("MYSQL_DATABASE", "order_management"))
    
    # MongoDB Configuration
    MONGO_URI: str = Field(default=os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    MONGO_DB_NAME: str = Field(default=os.getenv("MONGO_DB_NAME", "order_agents"))
    
    # API Keys
    GEMINI_API_KEY: str = Field(default=os.getenv("GEMINI_API_KEY", ""))
    
    # Application Settings
    DEBUG: bool = Field(default=os.getenv("DEBUG", "False").lower() == "true")
    API_HOST: str = Field(default=os.getenv("API_HOST", "0.0.0.0"))
    API_PORT: int = Field(default=int(os.getenv("API_PORT", "8000")))

# Create a singleton instance of settings
settings = Settings()

# Export settings instance
__all__ = ["settings"] 