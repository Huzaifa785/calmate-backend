# app/models/user.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str]
    profile_image: Optional[str]
    current_streak: int = 0
    highest_streak: int = 0
    total_points: int = 0
    achievements: List[str] = []
    fcm_token: Optional[str]
    last_log_date: Optional[datetime]
    daily_calorie_goal: Optional[int] = None
    calories_consumed_today: Optional[int] = 0
    created_at: datetime
    updated_at: datetime