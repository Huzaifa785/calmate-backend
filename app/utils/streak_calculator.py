# app/utils/streak_calculator.py
from datetime import datetime, timedelta
from typing import Optional

class StreakCalculator:
    @staticmethod
    def calculate_streak(last_log_date: datetime, current_streak: int) -> tuple[int, bool]:
        """
        Calculate streak and whether it's maintained
        Returns (new_streak, is_maintained)
        """
        now = datetime.now()
        days_diff = (now - last_log_date).days
        
        if days_diff <= 1:
            return current_streak + 1, True
        elif days_diff <= 2:  # Grace period
            return current_streak, True
        else:
            return 0, False

    @staticmethod
    def get_streak_multiplier(streak_count: int) -> float:
        """Calculate point multiplier based on streak length"""
        if streak_count >= 30:
            return 3.0
        elif streak_count >= 14:
            return 2.0
        elif streak_count >= 7:
            return 1.5
        return 1.0