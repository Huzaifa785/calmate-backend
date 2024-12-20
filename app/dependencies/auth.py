# app/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from appwrite.client import Client
from appwrite.services.databases import Databases
from app.models.user import User
from app.config import settings
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    try:
        # Initialize client
        client = Client()
        client.set_endpoint(settings.APPWRITE_ENDPOINT)
        client.set_project(settings.APPWRITE_PROJECT_ID)
        client.set_key(settings.APPWRITE_API_KEY)
        
        # Get user document
        database = Databases(client)
        user_data = database.get_document(
            database_id=settings.DATABASE_ID,
            collection_id='6758085b003d85763089',
            document_id=token
        )
        
        # Map Appwrite document to User model
        return User(
            id=user_data['$id'],  # Appwrite uses $id for document ID
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data.get('full_name'),
            profile_image=user_data.get('profile_image'),
            current_streak=user_data.get('current_streak', 0),
            highest_streak=user_data.get('highest_streak', 0),
            total_points=user_data.get('total_points', 0),
            achievements=user_data.get('achievements', []),
            fcm_token=user_data.get('fcm_token'),
            last_log_date=user_data.get('last_log_date'),
            created_at=datetime.fromisoformat(user_data['$createdAt']),
            updated_at=datetime.fromisoformat(user_data['$updatedAt'])
        )
        
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )