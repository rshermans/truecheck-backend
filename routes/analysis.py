from fastapi import APIRouter, HTTPException, Depends
from models.schemas import (
    ContentRequest,
    PreliminaryAnalysisResponse,
    CrossVerificationRequest,
    CrossVerificationResponse,
    ContextAnalysisRequest,
    ContextAnalysisResponse,
    FinalEvaluationRequest,
    FinalEvaluationResponse
)
from services.ai_analyzer import ai_analyzer
from services.fact_checker import fact_checker
from services.context_analyzer import context_analyzer

from typing import Dict
from sqlmodel import Session
from database import get_session
from models.database import AnalysisResult
from routes.auth import verify_token
import json

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@router.post("/preliminary", response_model=PreliminaryAnalysisResponse)
async def preliminary_analysis(request: ContentRequest):
    """
    Perform preliminary analysis of content
    
    This endpoint analyzes the submitted content and returns:
    - Overall analysis summary
    - Source reliability score
    - Factual consistency score
    - Content quality score
    - Technical integrity score
    - Detailed criteria breakdown
    """
    try:
        result = await ai_analyzer.analyze_content(request.type, request.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/cross-verification", response_model=CrossVerificationResponse)
async def cross_verification(request: CrossVerificationRequest):
    """
    Perform cross-verification against trusted sources
    
    This endpoint verifies the content against:
    - Google Fact Check database
    - Known fact-checking organizations
    - Trusted news sources
    """
    try:
        result = await fact_checker.verify_claims(request.content, request.analysis)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.post("/context", response_model=ContextAnalysisResponse)
async def context_analysis(request: ContextAnalysisRequest):
    """
    Analyze the context and sentiment of content
    
    This endpoint provides:
    - Political/social context
    - Sentiment analysis
    - Temporal relevance
    """
    try:
        result = await context_analyzer.analyze_context(request.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context analysis failed: {str(e)}")

@router.post("/final", response_model=Dict)
async def final_evaluation(
    request: FinalEvaluationRequest,
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """
    Final evaluation comparing user perception vs AI analysis
    Requires authentication
    """
    try:
        # Calculate user score (average of all user ratings)
        user_score = round(
            (request.user_perception.sourceCredibility +
             request.user_perception.criticalAnalysis +
             request.user_perception.contextEvaluation +
             request.user_perception.finalJudgment) / 4
        )

        # Calculate AI score (average of all AI metrics)
        ai_score = round(
            (request.ai_analysis.sourceReliability +
             request.ai_analysis.factualConsistency +
             request.ai_analysis.contentQuality +
             request.ai_analysis.technicalIntegrity) / 4
        )

        # Calculate discrepancy
        discrepancy = abs(user_score - ai_score)

        # Determine discrepancy level and feedback
        if discrepancy <= 10:
            discrepancy_level = "Baixa"
            feedback = "Sua avaliação está muito alinhada com a análise automatizada. Você demonstrou boa capacidade de análise crítica!"
        elif discrepancy <= 25:
            discrepancy_level = "Moderada"
            feedback = "Há algumas diferenças entre sua avaliação e a análise automatizada. Considere revisar os critérios de verificação."
        else:
            discrepancy_level = "Alta"
            feedback = "Há uma diferença significativa entre sua avaliação e a análise automatizada. Isso pode indicar vieses cognitivos ou falta de informação. Recomendamos aprofundar a análise."

        result_data = {
            "userScore": user_score,
            "aiScore": ai_score,
            "discrepancy": discrepancy,
            "discrepancyLevel": discrepancy_level,
            "feedback": feedback,
            "summary": f"Análise concluída. Score do usuário: {user_score}, Score da IA: {ai_score}."
        }
        
        # Save to Database
        db_entry = AnalysisResult(
            content=request.ai_analysis.analysis[:100] + "...", # Store snippet
            ai_score=ai_score,
            user_score=user_score,
            discrepancy=discrepancy,
            discrepancy_level=discrepancy_level,
            verdict="Confiável" if ai_score > 70 else "Suspeito", # Simple logic for now
            user_id=token_data["user_id"],
            student_name=token_data["username"],  # For backward compat display
            full_json_data=json.dumps({
                "request": request.dict(),
                "result": result_data
            })
        )
        
        # Save sources if available
        if hasattr(request.ai_analysis, 'sources'):
            db_entry.sources = [s.dict() for s in request.ai_analysis.sources]
            
        session.add(db_entry)
        session.commit()
        session.refresh(db_entry)
        
        # Add ID to response
        result_data["id"] = db_entry.id
        
        # Gamification: Award XP (isolated to prevent breaking main flow)
        try:
            from services.gamification import award_xp
            from models.database import User
            
            user = session.get(User, token_data["user_id"])
            if user:
                # Base XP for completing analysis
                base_xp = 10
                
                # Bonus XP based on accuracy (low discrepancy = better analysis)
                if discrepancy <= 10:
                    bonus_xp = 5  # Excellent accuracy
                elif discrepancy <= 25:
                    bonus_xp = 2  # Good accuracy
                else:
                    bonus_xp = 0  # Needs improvement
                
                total_xp = base_xp + bonus_xp
                xp_result = award_xp(user, total_xp, session)
                result_data["xp_earned"] = xp_result
        except Exception as xp_error:
            # Log error but don't fail the request
            print(f"XP award failed: {xp_error}")
            result_data["xp_earned"] = None

        return result_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
