from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from appwrite.services.databases import Databases
from appwrite.query import Query
from app.utils.appwrite_client import get_client
from app.config import settings
from app.models.user import User

# Achievement definitions
ACHIEVEMENTS = {
    'WEEK_WARRIOR': {
        'title': 'Week Warrior',
        'description': 'Maintained a 7-day streak',
        'points': 100,
        'icon': '🔥'
    },
    'MONTH_MASTER': {
        'title': 'Month Master',
        'description': 'Maintained a 30-day streak',
        'points': 500,
        'icon': '👑'
    },
    'CENTURY_LOGGER': {
        'title': 'Century Logger',
        'description': 'Logged 100 meals',
        'points': 1000,
        'icon': '📱'
    },
    'PROTEIN_CHAMPION': {
        'title': 'Protein Champion',
        'description': 'Maintained high protein intake for a week',
        'points': 200,
        'icon': '💪'
    },
    'SOCIAL_BUTTERFLY': {
        'title': 'Social Butterfly',
        'description': 'Connected with 10 friends',
        'points': 300,
        'icon': '🦋'
    }
}

class GamificationService:
    def __init__(self):
        self.client = get_client()
        self.database = Databases(self.client)
        self.db_id = settings.DATABASE_ID
        self.users_collection = "6758085b003d85763089"
        self.food_logs_collection = "675928700015cab990d9"
        self.friends_collection = "67592b05001baf89ebb5"

    async def check_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Check and award new achievements"""
        try:
            user = self.database.get_document(
                database_id=self.db_id,
                collection_id=self.users_collection,
                document_id=user_id
            )
            
            new_achievements = []
            
            # Streak based achievements
            if user['highest_streak'] >= 7:
                new_achievements.append('WEEK_WARRIOR')
            if user['highest_streak'] >= 30:
                new_achievements.append('MONTH_MASTER')
                
            # Log count achievements
            logs = self.database.list_documents(
                database_id=self.db_id,
                collection_id=self.food_logs_collection,
                queries=[Query.equal('user_id', user_id)]
            )
            
            if logs['total'] >= 100:
                new_achievements.append('CENTURY_LOGGER')
            
            # Protein tracking achievement
            if self._check_protein_streak(user_id):
                new_achievements.append('PROTEIN_CHAMPION')
            
            # Social achievement
            if self._check_social_achievement(user_id):
                new_achievements.append('SOCIAL_BUTTERFLY')
            
            # Award new achievements
            current_achievements = set(user.get('achievements', []))
            new_achievements = set(new_achievements) - current_achievements
            
            if new_achievements:
                total_points = sum(ACHIEVEMENTS[ach]['points'] for ach in new_achievements)
                self.database.update_document(
                    database_id=self.db_id,
                    collection_id=self.users_collection,
                    document_id=user_id,
                    data={
                        'achievements': list(current_achievements | new_achievements),
                        'total_points': user.get('total_points', 0) + total_points
                    }
                )
            
            return [ACHIEVEMENTS[ach] for ach in new_achievements]
            
        except Exception as e:
            print(f"Achievement error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _check_protein_streak(self, user_id: str) -> bool:
        """Check if user maintained high protein intake"""
        try:
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            logs = self.database.list_documents(
                database_id=self.db_id,
                collection_id=self.food_logs_collection,
                queries=[
                    Query.equal('user_id', user_id),
                    Query.greater_than('timestamp', week_ago)  # Changed from greaterThan to greater
                ]
            )
            
            if len(logs['documents']) < 7:
                return False
            
            # Check protein in macronutrients
            return all(
                log.get('macronutrients', {}).get('protein', 0) >= 50 
                for log in logs['documents']
            )
            
        except Exception as e:
            print(f"Protein check error: {str(e)}")
            return False

    def _check_social_achievement(self, user_id: str) -> bool:
        """Check if user has enough friends"""
        try:
            friends = self.database.list_documents(
                database_id=self.db_id,
                collection_id=self.friends_collection,
                queries=[Query.equal('user_id', user_id)]
            )
            
            return friends['total'] >= 10
            
        except Exception as e:
            print(f"Social check error: {str(e)}")
            return False

    async def calculate_points(self, user_id: str, action: str) -> int:
        """Calculate and award points for user actions"""
        points_map = {
            'food_log': 10,
            'streak_day': 20,
            'friend_interaction': 5,
            'perfect_week': 100
        }
        
        try:
            user = self.database.get_document(
                database_id=self.db_id,
                collection_id=self.users_collection,
                document_id=user_id
            )
            
            points = points_map.get(action, 0)
            
            if points > 0:
                self.database.update_document(
                    database_id=self.db_id,
                    collection_id=self.users_collection,
                    document_id=user_id,
                    data={
                        'total_points': user.get('total_points', 0) + points
                    }
                )
            
            return points
            
        except Exception as e:
            print(f"Points calculation error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            users = self.database.list_documents(
                database_id=self.db_id,
                collection_id=self.users_collection,
                queries=[
                    Query.limit(100)  # Get all users within reasonable limit
                ]
            )

            # Process users and remove duplicates by username
            unique_users = {}
            for user in users['documents']:
                username = user['username']
                # Keep the user with highest streak/points if duplicate username
                if username not in unique_users or (
                    user.get('highest_streak', 0) > unique_users[username].get('highest_streak', 0) or
                    user.get('total_points', 0) > unique_users[username].get('total_points', 0)
                ):
                    unique_users[username] = {
                        'username': username,
                        'total_points': user.get('total_points', 0),
                        'achievements': len(user.get('achievements', [])),
                        'highest_streak': user.get('highest_streak', 0)
                    }

            # Convert to list and sort
            leaderboard = list(unique_users.values())
            leaderboard.sort(key=lambda x: (
                -x['total_points'],  # Sort by points descending
                -x['highest_streak'],  # Then by streak descending
                -x['achievements'],  # Then by achievements descending
                x['username']  # Then by username alphabetically
            ))

            return leaderboard[:limit]  # Return only requested number of entries

        except Exception as e:
            print(f"Leaderboard error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))