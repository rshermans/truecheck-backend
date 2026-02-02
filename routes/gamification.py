from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_session
from models.database import User
from routes.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/gamification", tags=["gamification"])


class XPUpdate(BaseModel):
    xp_amount: int
    reason: str


# XP thresholds for levels
LEVEL_THRESHOLDS = [
    0,      # Level 1
    100,    # Level 2
    250,    # Level 3
    500,    # Level 4
    1000,   # Level 5
    2000,   # Level 6
    3500,   # Level 7
    5500,   # Level 8
    8000,   # Level 9
    11000,  # Level 10
]


def calculate_level(xp: int) -> int:
    """Calculate level based on XP"""
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp >= threshold:
            level = i + 1
        else:
            break
    return level


def get_xp_for_next_level(current_level: int) -> int:
    """Get XP required for next level"""
    if current_level >= len(LEVEL_THRESHOLDS):
        return LEVEL_THRESHOLDS[-1]
    return LEVEL_THRESHOLDS[current_level]


@router.get("/profile")
async def get_gamification_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get user's gamification profile (XP, level, etc.)"""
    xp = current_user.xp or 0
    level = calculate_level(xp)
    xp_for_next = get_xp_for_next_level(level)
    xp_for_current = LEVEL_THRESHOLDS[level - 1] if level > 0 else 0
    
    return {
        "xp": xp,
        "level": level,
        "xp_for_next_level": xp_for_next,
        "xp_progress": xp - xp_for_current,
        "xp_needed": xp_for_next - xp_for_current,
        "username": current_user.username
    }


@router.post("/add-xp")
async def add_xp(
    xp_data: XPUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Add XP to user (internal use for rewarding activities)"""
    current_xp = current_user.xp or 0
    old_level = calculate_level(current_xp)
    
    new_xp = current_xp + xp_data.xp_amount
    current_user.xp = new_xp
    session.add(current_user)
    session.commit()
    
    new_level = calculate_level(new_xp)
    leveled_up = new_level > old_level
    
    return {
        "success": True,
        "xp_added": xp_data.xp_amount,
        "new_xp_total": new_xp,
        "new_level": new_level,
        "leveled_up": leveled_up,
        "reason": xp_data.reason
    }


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = 10,
    session: Session = Depends(get_session)
):
    """Get top users by XP"""
    users = session.query(User).order_by(User.xp.desc()).limit(limit).all()
    
    return [
        {
            "rank": i + 1,
            "username": user.username,
            "xp": user.xp or 0,
            "level": calculate_level(user.xp or 0)
        }
        for i, user in enumerate(users)
    ]
