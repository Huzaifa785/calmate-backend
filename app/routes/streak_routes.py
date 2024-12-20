# app/routes/streak_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.streak_service import StreakService
from app.services.gamification_service import GamificationService
from app.models.user import User
from app.dependencies.auth import get_current_user

router = APIRouter(tags=["streaks"])

@router.get("/current")
async def get_current_streak(
    current_user: User = Depends(get_current_user),
    streak_service: StreakService = Depends()
):
    return await streak_service.get_user_streak(current_user.id)

@router.get("/leaderboard")
async def get_streak_leaderboard(
    limit: int = Query(10, le=50),
    current_user: User = Depends(get_current_user),
    gamification_service: GamificationService = Depends()
):
    return await gamification_service.get_leaderboard(limit)