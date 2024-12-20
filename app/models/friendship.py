# app/models/friendship.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FriendRequest(BaseModel):
    id: str
    from_user: str
    to_user: str
    status: str  # "pending", "accepted", "rejected"
    timestamp: datetime

# app/models/friendship.py
class Friendship(BaseModel):
    id: str
    user_id: str
    friend_id: str
    username: str
    streak_count: int
    last_interaction: datetime
    status: str