import asyncio
import logging
from sqlmodel import Session, select
from database import engine
from models.database import News
from services.news_aggregator import NewsAggregator, GoogleFactCheckSource, ClaimReviewScraperSource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrueCheckAggregator")

async def test_aggregator():
    print("🚀 Starting TrueCheck News Aggregator Test...")
    
    with Session(engine) as session:
        # 1. Cleanup Mock Data
        print("🧹 Cleaning up mock data...")
        mock_urls = [
            'https://factuel.afp.com/doc.afp.com.34KL8QA',
            'https://factuel.afp.com/doc.afp.com.34KL8QB',
            'https://factcheck.afp.com/doc.afp.com.34KL8QD'
        ]
        deleted = 0
        for url in mock_urls:
            statement = select(News).where(News.url == url)
            results = session.exec(statement).all()
            for news in results:
                session.delete(news)
                deleted += 1
        
        # Also clean generic AFP mock if found by title
        mocks_by_title = session.exec(select(News).where(News.source == "AFP Portugal").where(News.tags.contains("imagem manipulada"))).all()
        for news in mocks_by_title:
             session.delete(news)
             deleted += 1
             
        session.commit()
        print(f"✅ Deleted {deleted} mock articles.")
        
        # 2. Run Aggregator
        print("📡 Initializing sources...")
        aggregator = NewsAggregator()
        
        # Google API
        aggregator.add_source(GoogleFactCheckSource())
        
        # Scrapers
        pt_sources = [
            "https://poligrafo.sapo.pt",
            "https://observador.pt/factcheck"
        ]
        aggregator.add_source(ClaimReviewScraperSource(pt_sources))
        
        # 3. Update
        print("🔄 Fetching updates (this may take a moment)...")
        count = await aggregator.update_all(session)
        
        print(f"✨ Update complete! Added {count} new articles.")
        
        # 4. Verify Content
        latest = session.exec(select(News).order_by(News.published_at.desc()).limit(5)).all()
        print("\n📰 Latest Articles:")
        for news in latest:
            print(f"   - [{news.source}] {news.title[:60]}... ({news.verdict})")

if __name__ == "__main__":
    asyncio.run(test_aggregator())
