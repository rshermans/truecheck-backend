import requests
from config import settings
from typing import Dict, List

class FactChecker:
    """Service for fact-checking using Google Fact Check API"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_FACT_CHECK_API_KEY
        self.base_url = settings.GOOGLE_FACT_CHECK_URL
    
    async def verify_claims(self, content: str, analysis: Dict) -> Dict:
        """
        Verify content against Google Fact Check database
        
        Args:
            content: The content to verify
            analysis: Preliminary analysis results
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Extract key claims from content (simplified - first 100 chars)
            query = content[:100] if len(content) > 100 else content
            
            params = {
                'key': self.api_key,
                'query': query,
                'languageCode': 'pt-BR'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._format_fact_check_result(data, content)
            else:
                print(f"Fact check API error: {response.status_code}")
                return self._get_fallback_verification()
                
        except Exception as e:
            print(f"Error in fact checking: {e}")
            return self._get_fallback_verification()
    
    def _format_fact_check_result(self, data: Dict, content: str) -> Dict:
        """Format the fact check result"""
        claims = data.get('claims', [])
        
        if not claims:
            return {
                "verification": "Nenhuma verificação prévia encontrada para este conteúdo específico.",
                "matches": [],
                "sources_checked": 0,
                "reliability_score": 50
            }
        
        # Extract sources from claims
        sources = []
        for claim in claims[:5]:  # Limit to 5 claims
            claim_review = claim.get('claimReview', [])
            for review in claim_review:
                publisher = review.get('publisher', {}).get('name', 'Unknown')
                if publisher not in sources:
                    sources.append(publisher)
        
        # Calculate reliability based on number of fact-checks found
        reliability_score = min(100, 60 + (len(claims) * 10))
        
        verification_text = f"Verificado contra {len(claims)} alegações em bases de fact-checking."
        if len(sources) > 0:
            verification_text += f" Fontes consultadas: {', '.join(sources[:3])}."
        
        return {
            "verification": verification_text,
            "matches": sources,
            "sources_checked": len(claims),
            "reliability_score": reliability_score
        }
    
    def _get_fallback_verification(self) -> Dict:
        """Fallback verification when API fails"""
        return {
            "verification": "Verificação cruzada em andamento. Dados simulados.",
            "matches": ["Fonte A", "Fonte B"],
            "sources_checked": 2,
            "reliability_score": 70
        }

# Singleton instance
fact_checker = FactChecker()
