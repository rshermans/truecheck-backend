from pydantic import BaseModel, Field
from typing import Optional, Dict, List

# Request Models
class Source(BaseModel):
    """Source reference model"""
    name: str
    url: Optional[str] = None
    reliability: str
    description: str

class ContentRequest(BaseModel):
    """Request model for content analysis"""
    type: str = Field(..., description="Type of content: text, url, or image")
    content: str = Field(..., description="Content to analyze")

class CrossVerificationRequest(BaseModel):
    """Request model for cross-verification"""
    content: str = Field(..., description="Original content")
    analysis: Dict = Field(..., description="Preliminary analysis results")

class ContextAnalysisRequest(BaseModel):
    """Request model for context analysis"""
    content: str = Field(..., description="Content to analyze")

class UserPerception(BaseModel):
    """User's perception scores"""
    sourceCredibility: int = Field(..., ge=0, le=100)
    criticalAnalysis: int = Field(..., ge=0, le=100)
    contextEvaluation: int = Field(..., ge=0, le=100)
    finalJudgment: int = Field(..., ge=0, le=100)

class AIAnalysis(BaseModel):
    """AI analysis scores"""
    sourceReliability: int = Field(..., ge=0, le=100)
    factualConsistency: int = Field(..., ge=0, le=100)
    contentQuality: int = Field(..., ge=0, le=100)
    technicalIntegrity: int = Field(..., ge=0, le=100)

    analysis: Optional[str] = "" # Added to support saving snippet
    sources: List[Source] = []

class FinalEvaluationRequest(BaseModel):
    """Request model for final evaluation"""
    user_perception: UserPerception
    ai_analysis: AIAnalysis
    student_name: Optional[str] = "Anônimo"
    original_content: str = ""  # NEW: Original submitted content
    content_type: str = "text"  # NEW: Type of content (text, url, image)

# Response Models
class CriterionDetail(BaseModel):
    """Detail of a single analysis criterion"""
    score: int = Field(..., ge=0, le=100)
    label: str
    description: str

class PreliminaryAnalysisResponse(BaseModel):
    """Response model for preliminary analysis"""
    analysis: str
    sourceReliability: int
    factualConsistency: int
    contentQuality: int
    technicalIntegrity: int

    details: Dict[str, CriterionDetail]
    sources: List[Source] = []

class CrossVerificationResponse(BaseModel):
    """Response model for cross-verification"""
    verification: str
    matches: List[str]
    sources_checked: int = 0
    reliability_score: int = 0

class ContextAnalysisResponse(BaseModel):
    """Response model for context analysis"""
    context: str
    sentiment: str
    temporal_relevance: Optional[str] = None
    political_context: Optional[str] = None

class FinalEvaluationResponse(BaseModel):
    """Response model for final evaluation"""
    userScore: int
    aiScore: int
    discrepancy: int
    discrepancyLevel: str
    feedback: str
    summary: str
