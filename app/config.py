from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App Config
    APP_NAME: str 
    DEBUG: bool
    SECRET_KEY: str
    ENVIRONMENT: str
    
    # Appwrite Config
    APPWRITE_ENDPOINT: str
    APPWRITE_PROJECT_ID: str
    APPWRITE_API_KEY: str
    APPWRITE_BUCKET_ID: str
    
    # OpenAI Config
    OPENAI_API_KEY: str
    
    # Database Config
    DATABASE_ID: str
    
    # Storage Config
    STORAGE_BUCKET: str

    # Firebase Config
    FIREBASE_CREDENTIALS_PATH: str
    FIREBASE_API_KEY: str
    
    # Server Config
    HOST: str
    PORT: int
    
    # CORS Settings
    ALLOWED_ORIGINS: str
    
    # Rate Limiting
    RATE_LIMIT_PER_SECOND: int
    
    # Cache Settings
    CACHE_TTL: int
    
    # Upload Settings
    MAX_UPLOAD_SIZE: int
    ALLOWED_IMAGE_TYPES: str

    # Notification Settings
    NOTIFICATION_EMAIL: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()