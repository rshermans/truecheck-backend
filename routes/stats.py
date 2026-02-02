from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from database import get_session
from models.database import AnalysisResult
from typing import Dict
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("/", response_model=Dict)
async def get_statistics(session: Session = Depends(get_session)):
    """Get platform statistics"""
    
    # Total verifications
    total_verifications = session.exec(
        select(func.count(AnalysisResult.id))
    ).one()
    
    # Average AI score (accuracy proxy)
    avg_ai_score = session.exec(
        select(func.avg(AnalysisResult.ai_score))
    ).one() or 0
    
    # Average discrepancy (learning indicator)
    avg_discrepancy = session.exec(
        select(func.avg(AnalysisResult.discrepancy))
    ).one() or 0
    
    # Count of low discrepancy (< 15) - "badges earned"
    good_analyses = session.exec(
        select(func.count(AnalysisResult.id)).where(AnalysisResult.discrepancy < 15)
    ).one()
    
    # Monthly Active Users (MAU) - users who performed verifications in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = session.exec(
        select(func.count(func.distinct(AnalysisResult.user_id)))
        .where(AnalysisResult.timestamp >= thirty_days_ago)
        .where(AnalysisResult.user_id.isnot(None))  # Only count authenticated users
    ).one()
    
    # Fallback: if no activity in last 30 days, show total registered users
    if active_users == 0:
        from models.database import User
        active_users = session.exec(
            select(func.count(User.id)).where(User.is_active == True)
        ).one()
    
    return {
        "total_verifications": total_verifications,
        "accuracy_rate": round(avg_ai_score) if avg_ai_score else 0,
        "active_users": active_users,
        "badges_earned": good_analyses
    }
