# app/services/social_service.py
import traceback
from typing import List, Dict, Any
from fastapi import HTTPException
from appwrite.services.databases import Databases
from appwrite.query import Query
from app.utils.appwrite_client import get_client
from app.config import settings
import uuid
from datetime import datetime, timezone
import json


class SocialService:
    def __init__(self):
        self.client = get_client()
        self.database = Databases(self.client)
        self.db_id = settings.DATABASE_ID
        self.users_collection = '6758085b003d85763089'      # Users collection ID
        self.friends_collection = '67592b05001baf89ebb5'    # Friendships collection ID
        # Friend requests collection ID
        self.friend_requests_collection = '67592a09000aff381e48'

    async def send_friend_request(self, from_user: str, to_user: str) -> Dict[str, Any]:
        try:
            print(f"Attempting friend request from {from_user} to {to_user}")

            existing = self.database.list_documents(
                database_id=self.db_id,
                collection_id='67592a09000aff381e48',
                queries=[
                    Query.equal('from_user', from_user),
                    Query.equal('to_user', to_user)
                ]
            )

            print("Existing requests check:", existing)

            if existing['total'] > 0:
                print("Found existing friend request")
                # Return the existing request instead of raising an error
                existing_request = existing['documents'][0]
                return {
                    'id': existing_request['$id'],
                    'from_user': existing_request['from_user'],
                    'to_user': existing_request['to_user'],
                    'status': existing_request['status'],
                    'timestamp': existing_request['timestamp'],
                    'message': "Friend request already exists"
                }

            request_id = str(uuid.uuid4())
            print(f"Generated request ID: {request_id}")

            response = self.database.create_document(
                database_id=self.db_id,
                collection_id='67592a09000aff381e48',
                document_id=request_id,
                data={
                    'from_user': from_user,
                    'to_user': to_user,
                    'status': 'pending',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            print("Document created response:", response)

            return {
                'id': response['$id'],
                'from_user': response['from_user'],
                'to_user': response['to_user'],
                'status': response['status'],
                'timestamp': response['timestamp']
            }

        except Exception as e:
            print(f"Friend request error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing friend request: {str(e)}"
            )

    async def accept_friend_request(self, request_id: str) -> Dict[str, Any]:
        try:
            request = self.database.get_document(
                database_id=self.db_id,
                collection_id='67592a09000aff381e48',  # friend_requests collection
                document_id=request_id
            )

            # Check if friendship already exists
            existing_friendship = self.database.list_documents(
                database_id=self.db_id,
                collection_id='67592b05001baf89ebb5',  # friendships collection
                queries=[
                    Query.equal('user_id', request['to_user']),
                    Query.equal('friend_id', request['from_user'])
                ]
            )

            current_time = datetime.now(timezone.utc).isoformat()

            if existing_friendship['total'] == 0:
                # Create friendship
                self.database.create_document(
                    database_id=self.db_id,
                    collection_id='67592b05001baf89ebb5',
                    document_id=str(uuid.uuid4()),
                    data={
                        'user_id': request['to_user'],
                        'friend_id': request['from_user'],
                        'streak_count': 0,
                        'last_interaction': current_time,
                        'status': 'active'
                    }
                )

                # Create reverse friendship
                self.database.create_document(
                    database_id=self.db_id,
                    collection_id='67592b05001baf89ebb5',
                    document_id=str(uuid.uuid4()),
                    data={
                        'user_id': request['from_user'],
                        'friend_id': request['to_user'],
                        'streak_count': 0,
                        'last_interaction': current_time,
                        'status': 'active'
                    }
                )

            # Update request status
            updated_request = self.database.update_document(
                database_id=self.db_id,
                collection_id='67592a09000aff381e48',
                document_id=request_id,
                data={'status': 'accepted'}
            )

            return {
                'id': updated_request['$id'],
                'from_user': updated_request['from_user'],
                'to_user': updated_request['to_user'],
                'status': updated_request['status'],
                'timestamp': updated_request['timestamp']
            }

        except Exception as e:
            print(f"Accept friend request error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_friends(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            # Get all friendships where user is user_id
            friendships = self.database.list_documents(
                database_id=self.db_id,
                collection_id=self.friends_collection,
                queries=[
                    Query.equal('user_id', user_id),
                    Query.equal('status', 'active')
                ]
            )

            # Get user details for each friend
            friend_list = []
            for friendship in friendships['documents']:
                friend = self.database.get_document(
                    database_id=self.db_id,
                    collection_id=self.users_collection,
                    document_id=friendship['friend_id']
                )

                friend_list.append({
                    'id': friend['$id'],
                    'user_id': friendship['user_id'],
                    'friend_id': friendship['friend_id'],
                    'username': friend['username'],
                    'streak_count': friendship['streak_count'],
                    'last_interaction': friendship['last_interaction'],
                    'status': friendship['status']
                })

            return friend_list

        except Exception as e:
            print(f"Get friends error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_friend_feed(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            # First get all friends
            friendships = self.database.list_documents(
                database_id=self.db_id,
                collection_id=self.friends_collection,
                queries=[
                    Query.equal('user_id', user_id),
                    Query.equal('status', 'active')
                ]
            )
            
            # Get friend IDs
            friend_ids = [friendship['friend_id'] for friendship in friendships['documents']]
            
            if not friend_ids:
                return []

            # Get all logs from all friends
            all_logs = []
            for friend_id in friend_ids:
                logs = self.database.list_documents(
                    database_id=self.db_id,
                    collection_id='675928700015cab990d9',
                    queries=[
                        Query.equal('visibility', 'friends'),
                        Query.equal('user_id', friend_id),
                        Query.order_desc('timestamp')
                    ]
                )
                all_logs.extend(logs['documents'])

            # Sort all logs by timestamp
            all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Apply pagination
            paginated_logs = all_logs[offset:offset + limit]

            # Process logs and add user info
            feed_items = []
            for log in paginated_logs:
                user = self.database.get_document(
                    database_id=self.db_id,
                    collection_id=self.users_collection,
                    document_id=log['user_id']
                )
                
                # Parse JSON string back to dict for macronutrients
                macros = json.loads(log['macronutrients'])

                feed_items.append({
                    'id': log['$id'],
                    'user_id': log['user_id'],
                    'username': user['username'],
                    'food_name': log['food_name'],
                    'portion_size': log['portion_size'],
                    'calories': log['calories'],
                    'macronutrients': macros,
                    'image_url': log['image_url'],
                    'timestamp': log['timestamp']
                })

            return feed_items

        except Exception as e:
            print(f"Get friend feed error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def cleanup_duplicate_friendships(self):
        try:
            # Get all friendships
            friendships = self.database.list_documents(
                database_id=self.db_id,
                collection_id='67592b05001baf89ebb5'
            )

            seen_pairs = set()
            duplicates = []

            for friendship in friendships['documents']:
                pair = tuple(
                    sorted([friendship['user_id'], friendship['friend_id']]))
                if pair in seen_pairs:
                    duplicates.append(friendship['$id'])
                else:
                    seen_pairs.add(pair)

            # Delete duplicates
            for doc_id in duplicates:
                self.database.delete_document(
                    database_id=self.db_id,
                    collection_id='67592b05001baf89ebb5',
                    document_id=doc_id
                )

            return {"cleaned_up": len(duplicates)}

        except Exception as e:
            print(f"Cleanup error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
