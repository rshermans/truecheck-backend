"""
Student Profile Routes
Endpoints for student statistics, progress, and gamification data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import Dict
from database import get_session
from models.database import User, AnalysisResult
from routes.auth import verify_token
from services.gamification import calculate_level, get_xp_for_next_level

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/profile")
async def get_student_profile(
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
) -> Dict:
    """
    Get student profile with gamification data
    
    Returns:
        {
            "username": str,
            "level": int,
            "xp": int,
            "xp_progress": {"current": int, "needed": int},
            "total_analyses": int,
            "avg_accuracy": float
        }
    """
    user = session.get(User, token_data["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get XP progress
    current_xp, needed_xp = get_xp_for_next_level(user.xp)
    
    # Get analysis statistics
    analyses = session.exec(
        select(AnalysisResult).where(AnalysisResult.user_id == user.id)
    ).all()
    
    total_analyses = len(analyses)
    
    # Calculate average accuracy (inverse of discrepancy)
    if total_analyses > 0:
        avg_discrepancy = sum(a.discrepancy for a in analyses) / total_analyses
        # Convert to accuracy percentage (lower discrepancy = higher accuracy)
        avg_accuracy = max(0, 100 - avg_discrepancy)
    else:
        avg_accuracy = 0
    
    return {
        "username": user.username,
        "level": user.level,
        "xp": user.xp,
        "xp_progress": {
            "current": current_xp,
            "needed": needed_xp
        },
        "total_analyses": total_analyses,
        "avg_accuracy": round(avg_accuracy, 1)
    }


@router.get("/stats")
async def get_student_stats(
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
) -> Dict:
    """
    Get detailed student statistics
    
    Returns:
        {
            "recent_analyses": [...],
            "xp_history": [...],
            "accuracy_trend": [...]
        }
    """
    user = session.get(User, token_data["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recent analyses (last 10)
    recent_analyses = session.exec(
        select(AnalysisResult)
        .where(AnalysisResult.user_id == user.id)
        .order_by(AnalysisResult.timestamp.desc())
        .limit(10)
    ).all()
    
    # Format recent analyses
    analyses_data = [
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "user_score": a.user_score,
            "ai_score": a.ai_score,
            "discrepancy": a.discrepancy,
            "verdict": a.verdict
        }
        for a in recent_analyses
    ]
    
    return {
        "recent_analyses": analyses_data,
        "total_xp": user.xp,
        "current_level": user.level
    }
