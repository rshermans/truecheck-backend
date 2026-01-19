"""
Gamification Service
Handles XP calculation, level progression, and rewards
"""
from typing import Tuple, Dict
from sqlmodel import Session
from models.database import User


# Level progression table (exponential growth)
LEVEL_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 250,
    4: 500,
    5: 850,
    6: 1300,
    7: 1850,
    8: 2500,
    9: 3250,
    10: 4100
}


def calculate_level(xp: int) -> int:
    """
    Calculate user level based on total XP
    
    Args:
        xp: Total experience points
        
    Returns:
        Current level (1-10)
    """
    for level in range(10, 0, -1):
        if xp >= LEVEL_THRESHOLDS[level]:
            return level
    return 1


def get_xp_for_next_level(current_xp: int) -> Tuple[int, int]:
    """
    Get XP progress for current level
    
    Args:
        current_xp: Total XP accumulated
        
    Returns:
        Tuple of (current_level_xp, xp_needed_for_next_level)
        
    Example:
        User has 150 XP (Level 2)
        Level 2 starts at 100 XP, Level 3 at 250 XP
        Returns (50, 150) -> 50 XP into level, 150 XP needed to reach Level 3
    """
    current_level = calculate_level(current_xp)
    
    if current_level >= 10:
        # Max level reached
        return (current_xp - LEVEL_THRESHOLDS[10], 0)
    
    level_start_xp = LEVEL_THRESHOLDS[current_level]
    next_level_xp = LEVEL_THRESHOLDS[current_level + 1]
    
    xp_in_current_level = current_xp - level_start_xp
    xp_needed = next_level_xp - level_start_xp
    
    return (xp_in_current_level, xp_needed)


def award_xp(user: User, amount: int, session: Session) -> Dict:
    """
    Award XP to user and handle level-up logic
    
    Args:
        user: User object to award XP to
        amount: XP amount to award
        session: Database session
        
    Returns:
        Dict with award details:
        {
            "xp_earned": int,
            "total_xp": int,
            "old_level": int,
            "new_level": int,
            "level_up": bool,
            "progress": {"current": int, "needed": int}
        }
    """
    old_level = user.level
    old_xp = user.xp
    
    # Add XP
    user.xp += amount
    
    # Recalculate level
    new_level = calculate_level(user.xp)
    user.level = new_level
    
    # Get progress
    current, needed = get_xp_for_next_level(user.xp)
    
    # Save to database
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {
        "xp_earned": amount,
        "total_xp": user.xp,
        "old_level": old_level,
        "new_level": new_level,
        "level_up": new_level > old_level,
        "progress": {
            "current": current,
            "needed": needed
        }
    }
