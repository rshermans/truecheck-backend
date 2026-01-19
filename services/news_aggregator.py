from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import httpx
import json
import os
from bs4 import BeautifulSoup
import feedparser
from sqlmodel import Session, select
from models.database import News
from config import settings
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_FILE = "sources_config.json"

class NewsSource(ABC):
    """Abstract base class for news sources"""
    
    def __init__(self, name: str, enabled: bool = True, languages: List[str] = None):
        self.name = name
        self.enabled = enabled
        self.languages = languages or ["pt"]
        self.stats = {"last_run": None, "last_count": 0, "total_count": 0}
    
    @abstractmethod
    async def fetch(self, session: Session) -> int:
        """Fetch news and save to database. Returns count of new items."""
        pass

    def update_stats(self, count: int):
        self.stats["last_run"] = datetime.now().isoformat()
        self.stats["last_count"] = count
        self.stats["total_count"] += count

class GoogleFactCheckSource(NewsSource):
    """Source: Google Fact Check Tools API"""
    
    def __init__(self, enabled: bool = True, languages: List[str] = None, stats: Dict = None):
        super().__init__("Google Fact Check API", enabled, languages or ["pt", "en"])
        if stats: self.stats = stats
    
    async def fetch(self, session: Session) -> int:
        if not self.enabled:
            return 0
            
        api_key = settings.GOOGLE_FACT_CHECK_API_KEY
        if not api_key:
            logger.warning("Google Fact Check API Key not configured")
            return 0
            
        total_added = 0
        
        async with httpx.AsyncClient() as client:
            for lang in self.languages:
                try:
                    added = await self._fetch_lang(client, session, api_key, lang)
                    total_added += added
                except Exception as e:
                    logger.error(f"Error fetching Google API for {lang}: {e}")

        self.update_stats(total_added)
        return total_added

    async def _fetch_lang(self, client, session, api_key, lang):
        added_count = 0
        response = await client.get(
            "https://factchecktools.googleapis.com/v1alpha1/claims:search",
            params={
                "key": api_key,
                "query": "fact check",
                "languageCode": lang,
                "pageSize": 20,
                "maxAgeDays": 60
            },
            timeout=15.0
        )
        
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            
            for claim in claims:
                try:
                    claim_text = claim.get("text", "")
                    claim_review = claim.get("claimReview", [{}])[0]
                    publisher = claim_review.get("publisher", {}).get("name", "Unknown")
                    url = claim_review.get("url", "")
                    title = claim_review.get("title", claim_text[:100]) or claim_text[:100]
                    review_date = claim_review.get("reviewDate")
                    textual_rating = claim_review.get("textualRating", "Unknown")
                    
                    if not url: continue
                        
                    # Map rating to verdict (Multi-language support)
                    verdict = "Parcial"
                    rating_lower = textual_rating.lower()
                    
                    false_terms = ["falso", "false", "fake", "mentira", "incorrect", "incorrecto", "faux"]
                    true_terms = ["verdadeiro", "true", "correct", "correto", "vrai", "autêntico"]
                    
                    if any(x in rating_lower for x in false_terms):
                        verdict = "Falso"
                    elif any(x in rating_lower for x in true_terms):
                        verdict = "Verdadeiro"
                        
                    # Check Deduplication
                    exists = session.exec(select(News).where(News.url == url)).first()
                    if not exists:
                        news_item = News(
                            title=title,
                            summary=claim_text,
                            url=url,
                            source=publisher,
                            verdict=verdict,
                            published_at=datetime.fromisoformat(review_date.replace('Z', '+00:00')) if review_date else datetime.now(),
                            language=lang,
                            category="Geral",
                            tags=json.dumps(["fact-check", "google-api", publisher.lower().replace(" ", "-")])
                        )
                        session.add(news_item)
                        added_count += 1
                except Exception as e:
                    continue
            session.commit()
        return added_count

class RSSFeedSource(NewsSource):
    """Source: RSS Feed Parser"""
    
    def __init__(self, name: str, feed_url: str, enabled: bool = True, language: str = "pt", stats: Dict = None):
        super().__init__(name, enabled, [language])
        self.feed_url = feed_url
        if stats: self.stats = stats
        
    async def fetch(self, session: Session) -> int:
        if not self.enabled: return 0
            
        logger.info(f"Fetching RSS feed: {self.name}")
        added_count = 0
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.feed_url, timeout=15.0)
                if response.status_code != 200: return 0
                xml_content = response.text
                
            feed = feedparser.parse(xml_content)
            
            for entry in feed.entries[:15]:
                try:
                    url = entry.link
                    title = entry.title
                    summary =  getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    
                    if session.exec(select(News).where(News.url == url)).first(): continue
                        
                    verdict = "Parcial"
                    text_to_check = (title + " " + summary).lower()
                    
                    false_terms = ["falso", "mentira", "fake", "incorrecto", "enganoso", "false"]
                    true_terms = ["verdadeiro", "correto", "autêntico", "true", "correct"]
                    
                    if any(x in text_to_check for x in false_terms): verdict = "Falso"
                    elif any(x in text_to_check for x in true_terms): verdict = "Verdadeiro"
                    
                    pub_date = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                         pub_date = datetime(*entry.published_parsed[:6])
                    
                    tags_list = ["rss", self.name.lower().replace(" ", "-")]
                    if hasattr(entry, 'tags'): tags_list.extend([t.term for t in entry.tags])
                        
                    news_item = News(
                        title=title,
                        summary=BeautifulSoup(summary, "html.parser").get_text()[:500],
                        url=url,
                        source=self.name,
                        verdict=verdict,
                        published_at=pub_date,
                        language=self.languages[0],
                        category="Fact Check",
                        tags=json.dumps(tags_list[:5])
                    )
                    session.add(news_item)
                    added_count += 1
                except: continue
            
            session.commit()
        except Exception as e:
            logger.error(f"Error processing RSS {self.name}: {e}")
            
        self.update_stats(added_count)
        return added_count

class ClaimReviewScraperSource(NewsSource):
    """Source: Scraping pages looking for ClaimReview JSON-LD"""
    
    def __init__(self, name: str, urls: List[str], enabled: bool = True, language: str = "pt", stats: Dict = None):
        super().__init__(name, enabled, [language])
        self.urls = urls
        if stats: self.stats = stats
        
    async def fetch(self, session: Session) -> int:
        if not self.enabled: return 0
            
        added_count = 0
        async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": "TrueCheck/1.3"}) as client:
            for source_url in self.urls:
                try:
                    logger.info(f"Scraping {source_url}...")
                    response = await client.get(source_url, timeout=20.0)
                    if response.status_code != 200: continue
                        
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links_to_check = set()
                    
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if not href or len(href) < 10 or href.startswith('#') or href.startswith('javascript:'): continue
                        if href.startswith('/'): href = source_url.rstrip('/') + href
                        elif not href.startswith('http'): continue
                        if source_url in href or source_url.replace('https://', '').split('/')[0] in href:
                             links_to_check.add(href)
                            
                    scored_links = []
                    keywords = ['fact-check', 'fake', 'true', 'boolean', 'rating', 'review']
                    
                    for link in links_to_check:
                        score = 0
                        lower_link = link.lower()
                        if any(k in lower_link for k in ['fact-check', 'factcheck']): score += 5
                        if any(k in lower_link for k in ['verdadeiro', 'falso', 'enganoso', 'false', 'true']): score += 2
                        if len(link) > 50: score += 1
                        scored_links.append((score, link))
                    
                    scored_links.sort(key=lambda x: x[0], reverse=True)
                    valid_links = [l[1] for l in scored_links[:12] if l[0] > 0]
                    
                    for link in valid_links:
                        if session.exec(select(News).where(News.url == link)).first(): continue
                        try:
                            resp = await client.get(link, timeout=10.0)
                            if resp.status_code == 200:
                                count = self._parse_article(session, resp.text, link, source_url)
                                added_count += count
                        except: continue
                except Exception as e:
                    logger.error(f"Error scraping {source_url}: {e}")
                    
            session.commit()
        
        self.update_stats(added_count)
        return added_count

    def _parse_article(self, session: Session, html: str, url: str, source_domain: str) -> int:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            schemas = soup.find_all('script', type='application/ld+json')
            
            for script in schemas:
                try:
                    data = json.loads(script.string)
                    objects = data.get('@graph', [data]) if isinstance(data, dict) else data
                    if isinstance(objects, dict): objects = [objects]
                    
                    for obj in objects:
                        if obj.get('@type') == 'ClaimReview':
                            item = obj.get('itemReviewed', {})
                            claim = item.get('name') or item.get('text') or "Fact Check"
                            review_rating = obj.get('reviewRating', {})
                            rating_val = review_rating.get('alternateName') or review_rating.get('ratingValue')
                            author = obj.get('author', {}).get('name') or self.name
                            
                            verdict = "Parcial"
                            if rating_val:
                                r = str(rating_val).lower()
                                if any(x in r for x in ["falso", "false", "fake", "incorrect", "mentira"]): verdict = "Falso"
                                elif any(x in r for x in ["verdadeiro", "true", "correct", "correto"]): verdict = "Verdadeiro"
                            
                            title = soup.title.string if soup.title else claim[:100]
                            date_str = obj.get('datePublished') or datetime.now().isoformat()
                            try: pub_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            except: pub_date = datetime.now()

                            news_item = News(
                                title=title,
                                summary=claim[:500] if claim else "Verificação",
                                url=url,
                                source=author,
                                verdict=verdict,
                                published_at=pub_date,
                                language=self.languages[0],
                                category="Fact Check",
                                tags=json.dumps(["scraped", "claim-review", author.lower().replace(" ", "-")])
                            )
                            session.add(news_item)
                            return 1
                except: continue
        except: pass
        return 0

class NewsAggregator:
    def __init__(self):
        self.sources: Dict[str, NewsSource] = {}
        self.load_config()

    def load_config(self):
        """Load source configuration from JSON"""
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            except: pass
        
        # Helper to get config dict
        def get_conf(key, default_enabled=True):
            val = config.get(key)
            if isinstance(val, bool): return {"enabled": val, "stats": {}}
            if isinstance(val, dict): return val
            return {"enabled": default_enabled, "stats": {}}

        # Google API
        c_google = get_conf("google_api")
        self.sources["google_api"] = GoogleFactCheckSource(
            enabled=c_google.get("enabled", True),
            languages=c_google.get("languages", ["pt", "en", "es"]),
            stats=c_google.get("stats")
        )
        
        # Poligrafo Scraper
        c_poli = get_conf("poligrafo_scraper")
        self.sources["poligrafo_scraper"] = ClaimReviewScraperSource(
            "Polígrafo Scraper", ["https://poligrafo.sapo.pt"],
            enabled=c_poli.get("enabled", True),
            language="pt",
            stats=c_poli.get("stats")
        )
                                    
        # Observador Scraper
        c_obs = get_conf("observador_scraper")
        self.sources["observador_scraper"] = ClaimReviewScraperSource(
            "Observador Scraper", ["https://observador.pt/factcheck"],
            enabled=c_obs.get("enabled", True),
            language="pt",
            stats=c_obs.get("stats")
        )
                                    
        # RSS Sources
        c_rss_poli = get_conf("poligrafo_rss")
        self.sources["poligrafo_rss"] = RSSFeedSource(
            "Polígrafo RSS", "https://poligrafo.sapo.pt/rss",
            enabled=c_rss_poli.get("enabled", True),
            language="pt",
            stats=c_rss_poli.get("stats")
        )

    def save_config(self):
        """Save current configuration to JSON"""
        config = {}
        for k, v in self.sources.items():
            config[k] = {
                "enabled": v.enabled,
                "languages": v.languages,
                "stats": v.stats,
                "type": v.__class__.__name__
            }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_sources_status(self) -> List[Dict]:
        return [
            {
                "id": k, 
                "name": v.name, 
                "enabled": v.enabled, 
                "type": v.__class__.__name__,
                "languages": v.languages,
                "stats": v.stats
            } 
            for k, v in self.sources.items()
        ]

    def toggle_source(self, source_id: str, enabled: bool):
        if source_id in self.sources:
            self.sources[source_id].enabled = enabled
            self.save_config()
            return True
        return False

    async def update_all(self, session: Session) -> int:
        total = 0
        for key, source in self.sources.items():
            try:
                if source.enabled:
                    logger.info(f"Running source: {source.name}")
                    total += await source.fetch(session)
            except Exception as e:
                logger.error(f"Source {source.name} failed: {e}")
        self.save_config() # Save stats updates
        return total
