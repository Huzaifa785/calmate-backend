# app/routes/food_routes.py
import json
import traceback
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from appwrite.query import Query as AppwriteQuery
from typing import List, Optional
from datetime import datetime, timezone
from app.config import Settings
from app.services.database_service import DatabaseService
from app.services.vision_service import VisionService
from app.services.storage_service import StorageService
from app.services.streak_service import StreakService
from app.services.gamification_service import GamificationService
from app.models.food_log import FoodLog
from app.models.user import User
from app.dependencies.auth import get_current_user
import uuid
from app.config import settings

router = APIRouter(tags=["food"])


@router.post("/analyze", response_model=FoodLog)
async def analyze_food(
    file: UploadFile = File(...),
    visibility: str = Query("friends", enum=["private", "friends", "public"]),
    current_user: User = Depends(get_current_user),
    vision_service: VisionService = Depends(),
    storage_service: StorageService = Depends(),
    streak_service: StreakService = Depends(),
    gamification_service: GamificationService = Depends(),
    database_service: DatabaseService = Depends()
):
    try:
        # Upload image
        file_data = await storage_service.upload_image(file)
        print(f"File uploaded: {file_data}")

        # Analyze food
        analysis = await vision_service.analyze_food(file_data['file_url'])
        print(f"Analysis completed: {analysis}")

        # Generate unique ID
        log_id = str(uuid.uuid4())

        # Create food log data for database
        food_log_data = {
            "id": log_id,
            "user_id": current_user.id,
            "food_name": analysis['food_name'],
            "portion_size": float(analysis['portion_size']),
            "calories": float(analysis['calories']),
            "macronutrients": json.dumps(analysis['macronutrients']),  # Convert dict to JSON string
            "image_url": file_data['file_url'],
            "visibility": visibility,
            "reactions": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Save to Appwrite
        database_service.database.create_document(
            database_id=settings.DATABASE_ID,
            collection_id='675928700015cab990d9',
            document_id=log_id,
            data=food_log_data
        )

        # Update streaks and achievements
        await streak_service.update_streak(current_user.id)
        new_achievements = await gamification_service.check_achievements(current_user.id)

        # Update user's daily calories
        user = database_service.database.get_document(
            database_id=settings.DATABASE_ID,
            collection_id='6758085b003d85763089',
            document_id=current_user.id
        )

        # Handle missing or None value for 'calories_consumed_today'
        current_calories = int(user.get('calories_consumed_today') or 0)
        new_calories = current_calories + int(analysis['calories'])

        database_service.database.update_document(
            database_id=settings.DATABASE_ID,
            collection_id='6758085b003d85763089',
            document_id=current_user.id,
            data={'calories_consumed_today': new_calories}
        )

        if analysis['calories'] is None:
            raise ValueError("Calories analysis returned None.")


        # Prepare response data
        response_data = {
            **food_log_data,
            "macronutrients": analysis['macronutrients'],  # Use original dict for response
            "timestamp": datetime.fromisoformat(food_log_data["timestamp"]),  # Convert back to datetime
            "new_achievements": new_achievements
        }

        return FoodLog(**response_data)

    except Exception as e:
        print(f"Error in food analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/logs", response_model=List[FoodLog])
async def get_food_logs(
    limit: int = Query(10, le=50),
    offset: int = 0,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    database_service: DatabaseService = Depends()  # Changed from vision_service
):
    try:
        # Create queries
        queries = [
            AppwriteQuery.equal('user_id', current_user.id),
            AppwriteQuery.limit(limit),
            AppwriteQuery.offset(offset),
            AppwriteQuery.order_desc('timestamp')  # Most recent first
        ]

        # Add date filters if provided
        if date_from:
            queries.append(Query.greater_than('timestamp', date_from.isoformat()))
        if date_to:
            queries.append(Query.less_than('timestamp', date_to.isoformat()))

        # Get logs from database
        logs = database_service.database.list_documents(
            database_id=settings.DATABASE_ID,
            collection_id='675928700015cab990d9',  # food_logs collection ID
            queries=queries
        )

        # Process the logs
        food_logs = []
        for log in logs['documents']:
            # Parse the JSON string back to dict for macronutrients
            log['macronutrients'] = json.loads(log['macronutrients'])
            # Convert timestamp string to datetime
            log['timestamp'] = datetime.fromisoformat(log['timestamp'])
            food_logs.append(FoodLog(**log))

        return food_logs

    except Exception as e:
        print(f"Error fetching food logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching food logs: {str(e)}"
        )