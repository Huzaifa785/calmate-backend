# app/services/streak_service.py
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import HTTPException, Query
from appwrite.services.databases import Databases
from app.utils.appwrite_client import get_client
from app.config import settings
from datetime import datetime, timezone

class StreakService:
    def __init__(self):
        self.client = get_client()
        self.database = Databases(self.client)
        self.db_id = settings.DATABASE_ID
        self.users_collection = "6758085b003d85763089"  # Your users collection ID

    async def update_streak(self, user_id: str):
        try:
            user = self.database.get_document(
                database_id=self.db_id,
                collection_id=self.users_collection,
                document_id=user_id
            )
            
            today = datetime.now(timezone.utc)
            
            # If no last_log_date, this is first log
            if not user.get('last_log_date'):
                self.database.update_document(
                    database_id=self.db_id,
                    collection_id=self.users_collection,
                    document_id=user_id,
                    data={
                        'current_streak': 1,
                        'highest_streak': 1,
                        'last_log_date': today.isoformat()
                    }
                )
                return

            # Get last log date and convert to datetime
            last_log = datetime.fromisoformat(user['last_log_date'])
            
            # Calculate hours since last log
            hours_since_last_log = (today - last_log).total_seconds() / 3600
            
            # Same day - no streak update needed
            if last_log.date() == today.date():
                return
                
            # Next day - increment streak
            elif hours_since_last_log <= 48:  # 48-hour grace period
                new_streak = user['current_streak'] + 1
                highest_streak = max(new_streak, user.get('highest_streak', 0))
                
                self.database.update_document(
                    database_id=self.db_id,
                    collection_id=self.users_collection,
                    document_id=user_id,
                    data={
                        'current_streak': new_streak,
                        'highest_streak': highest_streak,
                        'last_log_date': today.isoformat()
                    }
                )
            else:
                # Beyond grace period - reset streak
                self.database.update_document(
                    database_id=self.db_id,
                    collection_id=self.users_collection,
                    document_id=user_id,
                    data={
                        'current_streak': 1,
                        'highest_streak': user.get('highest_streak', 0),
                        'last_log_date': today.isoformat()
                    }
                )

        except Exception as e:
            print(f"Streak update error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        
    async def get_user_streak(self, user_id: str) -> Dict[str, Any]:
        try:
            # Get user document
            user = self.database.get_document(
                database_id=self.db_id,
                collection_id=self.users_collection,
                document_id=user_id
            )
            
            return {
                'current_streak': user.get('current_streak', 0),
                'highest_streak': user.get('highest_streak', 0),
                'last_log_date': user.get('last_log_date'),
                'user_id': user_id
            }
            
        except Exception as e:
            print(f"Get streak error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))