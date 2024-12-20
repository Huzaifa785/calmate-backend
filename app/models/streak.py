# app/models/streak.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Streak(BaseModel):
    id: str
    user_id: str
    friend_id: Optional[str]
    streak_type: str  # "personal", "friend"
    current_count: int
    last_maintained: datetime
    multiplier: float = 1.0