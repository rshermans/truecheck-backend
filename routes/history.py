from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from database import get_session
from models.database import AnalysisResult
from services.pdf_generator import pdf_generator
from routes.auth import verify_token
from typing import List

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("/", response_model=List[AnalysisResult])
async def get_history(
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Get list of past verifications for authenticated user"""
    query = select(AnalysisResult).where(
        AnalysisResult.user_id == token_data["user_id"]
    ).order_by(AnalysisResult.timestamp.desc())
        
    results = session.exec(query).all()
    return results

@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_details(analysis_id: int, session: Session = Depends(get_session)):
    """Get details of a specific verification"""
    analysis = session.get(AnalysisResult, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

@router.get("/{analysis_id}/pdf")
async def download_report(analysis_id: int, session: Session = Depends(get_session)):
    """Generate and download PDF report"""
    analysis = session.get(AnalysisResult, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    pdf_buffer = pdf_generator.generate_report(analysis)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=truecheck_report_{analysis_id}.pdf"}
    )
