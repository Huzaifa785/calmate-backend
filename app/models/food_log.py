from pydantic import BaseModel, Field, validator
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json

class FoodLog(BaseModel):
    id: str
    user_id: str
    food_name: str
    portion_size: float
    calories: float
    macronutrients: Dict[str, float]
    image_url: str
    visibility: str
    reactions: List[str] = Field(default_factory=list)
    timestamp: datetime
    new_achievements: Optional[List[Dict[str, Any]]] = None

class FeedItem(BaseModel):
    id: str
    user_id: str
    username: str
    food_name: str
    portion_size: float
    calories: float
    macronutrients: Dict[str, float]
    image_url: str
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }