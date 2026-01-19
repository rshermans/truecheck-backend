from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from database import get_session
from models.database import News
from routes.admin import verify_admin
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("/", response_model=List[News])
async def get_news(
    language: Optional[str] = None,
    category: Optional[str] = None,
    verdict: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Get news with filters"""
    query = select(News).order_by(News.published_at.desc())
    
    if language and language != 'all':
        query = query.where(News.language == language)
        
    if category and category != 'all':
        query = query.where(News.category == category)
        
    if verdict and verdict != 'all':
        query = query.where(News.verdict == verdict)
        
    if start_date:
        query = query.where(News.published_at >= start_date)
        
    if end_date:
        query = query.where(News.published_at <= end_date)
        
    if search:
        # Simple case-insensitive search
        query = query.where(
            (News.title.ilike(f"%{search}%")) | 
            (News.summary.ilike(f"%{search}%"))
        )
        
    query = query.limit(limit)
    return session.exec(query).all()

@router.post("/", response_model=News)
async def create_news(
    news: News,
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Manually add a news item (Admin only)"""
    session.add(news)
    session.commit()
    session.refresh(news)
    return news

@router.get("/sources", response_model=List[dict])
async def get_news_sources(
    user: dict = Depends(verify_admin)
):
    """Get status of all news sources"""
    from services.news_aggregator import NewsAggregator
    aggregator = NewsAggregator()
    return aggregator.get_sources_status()

@router.post("/sources/toggle", response_model=dict)
async def toggle_news_source(
    source_id: str,
    enabled: bool,
    user: dict = Depends(verify_admin)
):
    """Enable or disable a news source"""
    from services.news_aggregator import NewsAggregator
    aggregator = NewsAggregator()
    if aggregator.toggle_source(source_id, enabled):
        return {"message": f"Source {source_id} updated", "enabled": enabled}
    raise HTTPException(status_code=404, detail="Source not found")

@router.post("/update", response_model=dict)
async def update_news_feed(
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """
    Trigger news update from configured sources
    """
    from services.news_aggregator import NewsAggregator
    
    # 1. Cleanup old Mock Data if exists (Legacy cleanup)
    mock_urls = [
        'https://factuel.afp.com/doc.afp.com.34KL8QA',
        'https://factuel.afp.com/doc.afp.com.34KL8QB',
        'https://factcheck.afp.com/doc.afp.com.34KL8QD'
    ]
    for url in mock_urls:
        try:
            statement = select(News).where(News.url == url)
            results = session.exec(statement).all()
            for news in results:
                session.delete(news)
        except: pass
            
    # 2. Run Aggregator
    aggregator = NewsAggregator()
    added_count = await aggregator.update_all(session)
    
    return {"message": f"News feed updated. Added {added_count} new articles from active sources."}
