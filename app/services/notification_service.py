# app/services/notification_service.py
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta, timezone
import uuid
from fastapi import HTTPException
from appwrite.services.databases import Databases
from appwrite.query import Query
from firebase_admin import messaging, initialize_app, credentials, get_app
from app.utils.appwrite_client import get_client
from app.config import settings
from app.models.user import User

# Initialize Firebase once
try:
    firebase_app = get_app()
except ValueError:
    # Only initialize if not already initialized
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_app = initialize_app(cred)

class NotificationService:
    def __init__(self):
        self.client = get_client()
        self.database = Databases(self.client)
        self.db_id = settings.DATABASE_ID
        self.users_collection = '6758085b003d85763089'

    def _init_firebase(self):
        """Initialize Firebase for push notifications"""
        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            initialize_app(cred)
        except Exception as e:
            print(f"Firebase initialization error: {str(e)}")

    async def send_streak_reminder(self, user_id: str) -> None:
        """Send reminder to maintain streak"""
        try:
            user = await self.database.get_document(
                database_id=self.db_id,
                collection_id='6758085b003d85763089',
                document_id=user_id
            )
            
            last_log = datetime.fromisoformat(user['last_log_date'])
            now = datetime.now()
            
            # Send reminder if no log in 20 hours
            if (now - last_log).total_seconds() / 3600 >= 20:
                await self.send_push_notification(
                    user_id=user_id,
                    title="Keep Your Streak Going! 🔥",
                    body=f"Don't forget to log today's meals to maintain your {user['current_streak']} day streak!"
                )
        except Exception as e:
            print(f"Error sending streak reminder: {str(e)}")

    async def send_achievement_notification(self, user_id: str, achievement: str) -> None:
        """Send notification for new achievement"""
        try:
            await self.send_push_notification(
                user_id=user_id,
                title="New Achievement Unlocked! 🏆",
                body=f"Congratulations! You've earned the {achievement} badge!"
            )
        except Exception as e:
            print(f"Error sending achievement notification: {str(e)}")

    async def send_friend_activity(self, user_id: str, friend_id: str, activity: str) -> None:
        """Notify user about friend's activity"""
        try:
            # Get friend's info
            friend = self.database.get_document(
                database_id=self.db_id,
                collection_id=self.users_collection,
                document_id=friend_id
            )
            
            # Need to await the push notification since it's async
            await self.send_push_notification(
                user_id=user_id,
                title="Friend Activity 👋",
                body=f"{friend['username']} {activity}"
            )
        except Exception as e:
            print(f"Error sending friend activity notification: {str(e)}")

    async def send_push_notification(self, user_id: str, title: str, body: str) -> None:
        """Send push notification via Firebase"""
        try:
            # Get user's FCM token
            user = self.database.get_document(
                database_id=self.db_id,
                collection_id=self.users_collection,
                document_id=user_id
            )
            
            if not user.get('fcm_token'):
                return
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                token=user['fcm_token'],
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='notification_icon',
                        color='#20B2AA'
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            response = messaging.send(message)
            
            # Log notification
            self.database.create_document(
                database_id=self.db_id,
                collection_id='notifications',
                document_id=str(uuid.uuid4()),
                data={
                    'user_id': user_id,
                    'title': title,
                    'body': body,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'status': 'sent',
                    'firebase_response': str(response)
                }
            )
        except Exception as e:
            print(f"Error sending push notification: {str(e)}")