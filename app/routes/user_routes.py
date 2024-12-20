# app/routes/user_routes.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from app.config import Settings
from app.services.database_service import DatabaseService
from app.services.storage_service import StorageService
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.config import settings
from pydantic import BaseModel
from typing import Optional
from appwrite.query import Query
from pydantic import BaseModel, conint


router = APIRouter(tags=["users"])

@router.get("/profile", response_model=User)
async def get_profile(
    current_user: User = Depends(get_current_user),
    database_service: DatabaseService = Depends()
):
    try:
        user = database_service.database.get_document(  # Remove await
            database_id=settings.DATABASE_ID,
            collection_id='6758085b003d85763089',  # users collection
            document_id=current_user.id
        )
        
        # Map Appwrite response to our User model
        return {
            'id': user['$id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user.get('full_name'),
            'profile_image': user.get('profile_image'),
            'current_streak': user.get('current_streak', 0),
            'highest_streak': user.get('highest_streak', 0),
            'total_points': user.get('total_points', 0),
            'achievements': user.get('achievements', []),
            'fcm_token': user.get('fcm_token'),
            'last_log_date': user.get('last_log_date'),
            'created_at': user['$createdAt'],
            'updated_at': user['$updatedAt']
        }
    except Exception as e:
        print(f"Get profile error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching profile: {str(e)}"
        )
    
class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None

@router.put("/profile", response_model=User)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    database_service: DatabaseService = Depends()
):
    try:
        print("Received update data:", update_data.dict())

        # Check if username already exists
        if update_data.username:
            existing_users = database_service.database.list_documents(
                database_id=settings.DATABASE_ID,
                collection_id='6758085b003d85763089',
                queries=[
                    Query.equal('username', update_data.username)
                ]
            )
            print("Existing users check:", existing_users)

        # Filter out None values
        update_fields = {
            k: v for k, v in update_data.dict().items() 
            if v is not None
        }
        print("Fields to update:", update_fields)

        # Update user document
        updated_user = database_service.database.update_document(
            database_id=settings.DATABASE_ID,
            collection_id='6758085b003d85763089',
            document_id=current_user.id,
            data=update_fields
        )
        print("Raw updated user from DB:", updated_user)

        response_data = {
            'id': updated_user['$id'],
            'username': updated_user['username'],  # Direct access, not using .get()
            'email': updated_user['email'],
            'full_name': updated_user.get('full_name'),
            'profile_image': updated_user.get('profile_image'),
            'current_streak': updated_user.get('current_streak', 0),
            'highest_streak': updated_user.get('highest_streak', 0),
            'total_points': updated_user.get('total_points', 0),
            'achievements': updated_user.get('achievements', []),
            'fcm_token': updated_user.get('fcm_token'),
            'last_log_date': updated_user.get('last_log_date'),
            'created_at': updated_user['$createdAt'],
            'updated_at': updated_user['$updatedAt']
        }
        print("Response being sent:", response_data)

        return response_data

    except Exception as e:
        print(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating profile: {str(e)}"
        )

@router.post("/profile/image")
async def update_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    storage_service: StorageService = Depends(),
    database_service: DatabaseService = Depends()
):
    try:
        file_data = await storage_service.upload_image(file)
        await database_service.update_user(
            current_user.id,
            {"profile_image": file_data['file_url']}
        )
        return {"message": "Profile image updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    database_service: DatabaseService = Depends()
):
    return await database_service.get_user_stats(current_user.id)


@router.post("/user/update-fcm")
async def update_fcm_token(
    fcm_token: str,
    current_user: User = Depends(get_current_user),
    database_service: DatabaseService = Depends()
):
    try:
        # Update user document with FCM token
        database_service.database.update_document(
            database_id=Settings.DATABASE_ID,
            collection_id='users',
            document_id=current_user.id,
            data={
                'fcm_token': fcm_token
            }
        )
        return {"message": "FCM token updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class CalorieGoalUpdate(BaseModel):
    daily_goal: conint(gt=0)  # Ensures positive integer
    
@router.post("/calorie-goal")
async def set_calorie_goal(
    goal_data: CalorieGoalUpdate,
    current_user: User = Depends(get_current_user),
    database_service: DatabaseService = Depends()
):
    try:
        # Ensure 'calories_consumed_today' is initialized properly
        updated_user = database_service.database.update_document(
            database_id=settings.DATABASE_ID,
            collection_id='6758085b003d85763089',  # users collection
            document_id=current_user.id,
            data={
                'daily_calorie_goal': goal_data.daily_goal,
                'calories_consumed_today': getattr(current_user, 'calories_consumed_today', 0)
            }
        )
        
        return {
            "success": True,
            "daily_calorie_goal": goal_data.daily_goal,
            "message": f"Daily calorie goal set to {goal_data.daily_goal} calories"
        }
        
    except Exception as e:
        print(f"Set calorie goal error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error setting calorie goal: {str(e)}"
        )


@router.get("/calorie-status")
async def get_calorie_status(
    current_user: User = Depends(get_current_user),
    database_service: DatabaseService = Depends()
):
    try:
        # Retrieve the user document
        user = database_service.database.get_document(
            database_id=settings.DATABASE_ID,
            collection_id='6758085b003d85763089',
            document_id=current_user.id
        )
        
        # Safely extract values with default fallbacks
        daily_goal = user.get('daily_calorie_goal', 0)  # Default to 0 if None or missing
        consumed = user.get('calories_consumed_today', 0)  # Default to 0 if None or missing
        
        # Calculate remaining calories
        remaining = max(daily_goal - consumed, 0)  # Ensure remaining is non-negative
        
        return {
            "goal": daily_goal,
            "consumed": consumed,
            "remaining": remaining
        }
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=str(e))
