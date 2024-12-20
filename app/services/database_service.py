# app/services/database_service.py
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from datetime import datetime, timedelta
from appwrite.services.databases import Databases
from appwrite.query import Query
from app.utils.appwrite_client import get_client
from app.config import settings
from app.models.food_log import FoodLog
from app.models.user import User

class DatabaseService:
    def __init__(self):
        self.client = get_client()
        self.database = Databases(self.client)
        self.db_id = settings.DATABASE_ID

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new user in the database"""
        try:
            # Debug log
            print(f"Attempting to create user with data: {user_data}")

            result = self.database.create_document(
                database_id=self.db_id,
                # Make sure this matches your Appwrite collection ID
                collection_id='6758085b003d85763089',
                document_id=user_data['id'],
                data={
                    "username": user_data['username'],
                    "email": user_data['email'],
                    "full_name": user_data.get('full_name'),
                    "current_streak": 0,
                    "highest_streak": 0,
                    "total_points": 0,
                    "achievements": [],
                    "last_log_date": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            )
            print(f"User creation result: {result}")  # Debug log
            return result
        except Exception as e:
            print(f"Error creating user: {str(e)}")  # Debug log
            raise HTTPException(
                status_code=500,
                detail=f"Error creating user in database: {str(e)}"
            )

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Gets user by ID"""
        try:
            return self.database.get_document(
                database_id=self.db_id,
                collection_id='6758085b003d85763089',
                document_id=user_id
            )
        except Exception:
            return None

    async def create_food_log(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new food log entry.
        """
        try:
            log_data = {
                "user_id": user_id,
                "food_name": data["food_name"],
                "calories": data["calories"],
                "protein": data["macronutrients"]["protein"],
                "carbs": data["macronutrients"]["carbs"],
                "fats": data["macronutrients"]["fats"],
                "image_url": data["image_url"],
                "timestamp": datetime.now().isoformat(),
                "visibility": data.get("visibility", "friends")
            }

            result = await self.database.create_document(
                database_id=self.db_id,
                collection_id='675928700015cab990d9',
                data=log_data
            )

            return result

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating food log: {str(e)}"
            )

    async def get_user_logs(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Gets food logs for a specific user.
        """
        try:
            result = await self.database.list_documents(
                database_id=self.db_id,
                collection_id='675928700015cab990d9',
                queries=[
                    Query.equal('user_id', user_id),
                    Query.orderDesc('timestamp'),
                    Query.limit(limit),
                    Query.offset(offset)
                ]
            )

            return result['documents']

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching logs: {str(e)}"
            )

    async def update_user_stats(self, user_id: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates user statistics.
        """
        try:
            result = await self.database.update_document(
                database_id=self.db_id,
                collection_id='6758085b003d85763089',
                document_id=user_id,
                data=stats
            )

            return result

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating user stats: {str(e)}"
            )

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Gets user statistics and achievements.
        """
        try:
            # Get user document
            user = await self.database.get_document(
                database_id=self.db_id,
                collection_id='6758085b003d85763089',
                document_id=user_id
            )

            # Get total logs count
            logs = await self.database.list_documents(
                database_id=self.db_id,
                collection_id='675928700015cab990d9',
                queries=[
                    Query.equal('user_id', user_id)
                ]
            )

            return {
                "total_logs": logs['total'],
                "current_streak": user.get('current_streak', 0),
                "highest_streak": user.get('highest_streak', 0),
                "achievements": user.get('achievements', [])
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching user stats: {str(e)}"
            )

    async def search_food_logs(
        self,
        query: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Searches through user's food logs.
        """
        try:
            result = await self.database.list_documents(
                database_id=self.db_id,
                collection_id='675928700015cab990d9',
                queries=[
                    Query.equal('user_id', user_id),
                    Query.search('food_name', query)
                ]
            )

            return result['documents']

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error searching logs: {str(e)}"
            )

    async def get_nutrition_summary(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Gets nutrition summary for specified days.
        """
        try:
            from_date = (datetime.now() - timedelta(days=days)).isoformat()

            logs = await self.database.list_documents(
                database_id=self.db_id,
                collection_id='675928700015cab990d9',
                queries=[
                    Query.equal('user_id', user_id),
                    Query.greaterThan('timestamp', from_date)
                ]
            )

            # Calculate averages
            total_calories = sum(log['calories'] for log in logs['documents'])
            total_protein = sum(log['protein'] for log in logs['documents'])
            total_carbs = sum(log['carbs'] for log in logs['documents'])
            total_fats = sum(log['fats'] for log in logs['documents'])

            return {
                "avg_daily_calories": total_calories / days,
                "avg_daily_protein": total_protein / days,
                "avg_daily_carbs": total_carbs / days,
                "avg_daily_fats": total_fats / days,
                "total_logs": len(logs['documents'])
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting nutrition summary: {str(e)}"
            )
