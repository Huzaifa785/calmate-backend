# app/routes/auth_routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.models.user import User
from app.services.database_service import DatabaseService
from appwrite.client import Client
from appwrite.services.account import Account
from pydantic import BaseModel, EmailStr
from app.dependencies.auth import get_current_user
from app.config import settings

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


def get_appwrite_client():
    client = Client()
    client.set_endpoint(settings.APPWRITE_ENDPOINT)
    client.set_project(settings.APPWRITE_PROJECT_ID)
    client.set_key(settings.APPWRITE_API_KEY)
    return client

@router.post("/signup", response_model=User)
async def signup(
    user_data: UserCreate,
    database_service: DatabaseService = Depends()
):
    try:
        client = get_appwrite_client()
        account = Account(client)
        
        # Create Appwrite account
        user = account.create(
            user_id='unique()',
            email=user_data.email,
            password=user_data.password,
            name=user_data.username
        )
        
        # Create user in our database with proper ID from Appwrite
        db_user = await database_service.create_user({
            "id": user['$id'],
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "current_streak": 0,
            "highest_streak": 0,
            "total_points": 0,
            "achievements": []
        })
        
        # Return complete user object
        return {
            "id": user['$id'], 
            **db_user
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/login")
async def login(credentials: UserLogin):
    try:
        client = get_appwrite_client()
        account = Account(client)

        # Create session
        session = account.create_email_password_session(
            email=credentials.email,
            password=credentials.password
        )

        # Return JWT in a format our client can use
        return {
            "access_token": session['userId'],  # Use userId instead of session ID
            "token_type": "bearer",
            "user_id": session['userId'],
            "expires": session['expire']
        }

    except Exception as e:
        print("Login Error:", str(e))
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    try:
        client = get_appwrite_client()
        account = Account(client)
        await account.delete_session('current')
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error logging out"
        )
