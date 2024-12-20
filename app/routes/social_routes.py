# app/routes/social_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.services.database_service import DatabaseService
from app.services.social_service import SocialService
from app.services.notification_service import NotificationService
from app.models.friendship import FriendRequest, Friendship
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.models.food_log import FeedItem
from app.config import settings
from appwrite.query import Query as AppWriteQuery

router = APIRouter(tags=["social"])

@router.post("/friends/request/{user_id}", response_model=FriendRequest)
async def send_friend_request(
    user_id: str,
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends(),
    notification_service: NotificationService = Depends()
):
    try:
        request = await social_service.send_friend_request(current_user.id, user_id)
        await notification_service.send_friend_activity(
            user_id,
            current_user.id,
            "sent you a friend request!"
        )
        return request
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/friends/requests")
async def get_friend_requests(
    type: str = Query("received", enum=["sent", "received"]),
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends()
):
    try:
        field = 'to_user' if type == 'received' else 'from_user'
        query = AppWriteQuery.equal(field, current_user.id)

        requests = social_service.database.list_documents(
            database_id=settings.DATABASE_ID,
            collection_id='67592a09000aff381e48',
            queries=[
                query,
                AppWriteQuery.equal('status', 'pending'),
                AppWriteQuery.order_desc('timestamp')
            ]
        )

        request_list = []
        for request in requests['documents']:
            # Get both users' details
            from_user = social_service.database.get_document(
                database_id=settings.DATABASE_ID,
                collection_id=social_service.users_collection,
                document_id=request['from_user']
            )
            
            to_user = social_service.database.get_document(
                database_id=settings.DATABASE_ID,
                collection_id=social_service.users_collection,
                document_id=request['to_user']
            )

            request_list.append({
                'id': request['$id'],
                'from_user': {
                    'id': from_user['$id'],
                    'username': from_user['username']
                },
                'to_user': {
                    'id': to_user['$id'],
                    'username': to_user['username']
                },
                'status': request['status'],
                'timestamp': request['timestamp']
            })

        return request_list

    except Exception as e:
        print(f"Get friend requests error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/users")
async def list_users(
   search: Optional[str] = None,
   current_user: User = Depends(get_current_user),
   database_service: DatabaseService = Depends()
):
   try:
       queries = [
           AppWriteQuery.limit(50),  # Limit results
           AppWriteQuery.order_desc('created_at')  # Most recent first
       ]

       # Add search query if provided
       if search:
           queries.append(Query.search('username', search))

       users = database_service.database.list_documents(
           database_id=settings.DATABASE_ID,
           collection_id='6758085b003d85763089',
           queries=queries
       )

       # Format user list and exclude current user
       user_list = []
       for user in users['documents']:
           if user['$id'] != current_user.id:  # Exclude current user
               user_list.append({
                   'id': user['$id'],
                   'username': user['username'],
                   'highest_streak': user.get('highest_streak', 0),
                   'total_points': user.get('total_points', 0),
                   'achievements_count': len(user.get('achievements', [])),
               })

       return user_list

   except Exception as e:
       print(f"List users error: {str(e)}")
       raise HTTPException(
           status_code=500,
           detail=str(e)
       )
    
@router.post("/friends/accept/{request_id}", response_model=FriendRequest)
async def accept_friend_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends(),
    notification_service: NotificationService = Depends()
):
    try:
        # Accept the request
        request = await social_service.accept_friend_request(request_id)
        
        # Send notification to the friend who sent the request
        await notification_service.send_friend_activity(
            request['from_user'],
            current_user.id,
            "accepted your friend request!"
        )
        
        return request
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/friends", response_model=List[Friendship])
async def get_friends(
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends()
):
    return await social_service.get_friends(current_user.id)

@router.get("/feed", response_model=List[FeedItem])
async def get_friend_feed(
    limit: int = Query(20, le=50),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends()
):
    return await social_service.get_friend_feed(
        current_user.id,
        limit,
        offset
    )

@router.post("/friends/cleanup", include_in_schema=False)  # Hidden admin endpoint
async def cleanup_friendships(
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends()
):
    return await social_service.cleanup_duplicate_friendships()