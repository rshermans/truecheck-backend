import openai
from config import settings
from typing import Dict
import json

class ContextAnalyzer:
    """Service for analyzing content context and sentiment"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def analyze_context(self, content: str) -> Dict:
        """
        Analyze the context and sentiment of content
        
        Args:
            content: The content to analyze
            
        Returns:
            Dictionary with context analysis
        """
        try:
            prompt = self._build_context_prompt(content)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Você é um especialista em análise de contexto e sentimento.
                        Analise o conteúdo fornecido e identifique o contexto político, social e temporal.
                        Retorne APENAS um objeto JSON válido."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return self._format_context_result(result)
            
        except Exception as e:
            print(f"Error in context analysis: {e}")
            return self._get_fallback_context()
    
    def _build_context_prompt(self, content: str) -> str:
        """Build the context analysis prompt"""
        return f"""Analise o contexto do seguinte conteúdo:

Conteúdo: {content}

Retorne um JSON com a seguinte estrutura:
{{
    "context": "Descrição breve do contexto (político, social, econômico, etc.)",
    "sentiment": "Positivo/Neutro/Negativo",
    "temporal_relevance": "Atual/Recente/Histórico",
    "political_context": "Descrição do contexto político se relevante, ou null"
}}"""
    
    def _format_context_result(self, result: Dict) -> Dict:
        """Format the context result"""
        return {
            "context": result.get("context", "Contexto geral"),
            "sentiment": result.get("sentiment", "Neutro"),
            "temporal_relevance": result.get("temporal_relevance"),
            "political_context": result.get("political_context")
        }
    
    def _get_fallback_context(self) -> Dict:
        """Fallback context when API fails"""
        return {
            "context": "Contexto geral de notícias",
            "sentiment": "Neutro",
            "temporal_relevance": "Atual",
            "political_context": None
        }

# Singleton instance
context_analyzer = ContextAnalyzer()
