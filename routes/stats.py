from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from database import get_session
from models.database import AnalysisResult
from typing import Dict

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
    
    return {
        "total_verifications": total_verifications,
        "accuracy_rate": round(avg_ai_score) if avg_ai_score else 0,
        "active_users": 1,  # For now, single user mode
        "badges_earned": good_analyses
    }
