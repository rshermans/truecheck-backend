import openai
from config import settings
from typing import Dict
import json

class AIAnalyzer:
    """Service for AI-powered content analysis using OpenAI GPT"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def analyze_content(self, content_type: str, content: str) -> Dict:
        """
        Perform comprehensive content analysis
        
        Args:
            content_type: Type of content (text, url, image)
            content: The content to analyze
            
        Returns:
            Dictionary with analysis results and detailed criteria
        """
        try:
            prompt = self._build_analysis_prompt(content_type, content)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Você é um especialista em verificação de fatos e análise de mídia.
                        Sua tarefa é analisar conteúdo e fornecer uma avaliação objetiva baseada em critérios específicos.
                        Retorne APENAS um objeto JSON válido, sem texto adicional."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return self._format_analysis_result(result)
            
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            return self._get_fallback_analysis()
    
    def _build_analysis_prompt(self, content_type: str, content: str) -> str:
        """Build the analysis prompt for GPT"""
        return f"""Atue como um Verificador de Fatos Sênior e Analista de Mídia rigoroso.
Sua tarefa é analisar o conteúdo abaixo com extremo rigor e ceticismo.

Tipo de conteúdo: {content_type}
Conteúdo: {content}

DIRETRIZES DE PONTUAÇÃO (Seja rigoroso!):
- 90-100: Excepcional. Fontes citadas, verificável, imparcial, tecnicamente perfeito.
- 70-89: Bom. Maioria verificável, mas pode ter pequenos viéses ou falta de contexto.
- 50-69: Regular. Afirmações sem fontes, linguagem emotiva, ou falta de clareza.
- 30-49: Fraco. Indícios de desinformação, viés forte, erros lógicos.
- 0-29: Crítico. Fake news provável, discurso de ódio, ou conteúdo fabricado.

CRITÉRIOS DE ANÁLISE:
1. Confiabilidade da Fonte: O conteúdo cita fontes? Elas são verificáveis?
2. Consistência Factual: As afirmações batem com o consenso científico/histórico?
3. Qualidade do Conteúdo: Gramática, estrutura, clareza.
4. Integridade Técnica: Há sinais de manipulação (se for imagem/url)?

Retorne um JSON ESTRITAMENTE com esta estrutura:
{{
    "analysis": "Análise crítica e detalhada (3-4 frases). Aponte explicitamente pontos fortes e fracos.",
    "sourceReliability": <0-100>,
    "factualConsistency": <0-100>,
    "contentQuality": <0-100>,
    "technicalIntegrity": <0-100>,
    "sources": [
        {{
            "name": "Nome da fonte ou referência",
            "url": "URL se disponível, ou null",
            "reliability": "Alta/Média/Baixa",
            "description": "Breve descrição da fonte"
        }}
    ],
    "details": {{
        "sensationalism": {{
            "score": <0-100, nota alta = pouco sensacionalista>,
            "label": "Baixo Risco/Moderado/Alto Risco",
            "description": "Explique o tom do texto"
        }},
        "grammar": {{
            "score": <0-100>,
            "label": "Excelente/Bom/Regular/Fraco",
            "description": "Avalie a escrita"
        }},
        "urlReliability": {{
            "score": <0-100>,
            "label": "Confiável/Moderado/Suspeito/N/A",
            "description": "Avalie se há links confiáveis"
        }},
        "sourceRecognition": {{
            "score": <0-100>,
            "label": "Reconhecida/Parcial/Desconhecida/N/A",
            "description": "As fontes citadas são conhecidas?"
        }},
        "factOpinion": {{
            "score": <0-100, nota alta = puramente factual>,
            "label": "Factual/Misto/Opinativo",
            "description": "Distinga fato de opinião"
        }},
        "temporalContext": {{
            "score": <0-100>,
            "label": "Atual/Recente/Desatualizado/Atemporal",
            "description": "O conteúdo é atual?"
        }}
    }}
}}"""
    
    def _format_analysis_result(self, result: Dict) -> Dict:
        """Format the analysis result to match expected schema"""
        return {
            "analysis": result.get("analysis", "Análise concluída."),
            "sourceReliability": result.get("sourceReliability", 75),
            "factualConsistency": result.get("factualConsistency", 75),
            "contentQuality": result.get("contentQuality", 75),
            "technicalIntegrity": result.get("technicalIntegrity", 75),
            "sources": result.get("sources", []),
            "details": result.get("details", self._get_default_details())
        }
    
    def _get_default_details(self) -> Dict:
        """Get default details structure"""
        return {
            "sensationalism": {
                "score": 70,
                "label": "Moderado",
                "description": "Análise em andamento"
            },
            "grammar": {
                "score": 80,
                "label": "Bom",
                "description": "Análise em andamento"
            },
            "urlReliability": {
                "score": 75,
                "label": "Moderado",
                "description": "Análise em andamento"
            },
            "sourceRecognition": {
                "score": 70,
                "label": "Parcial",
                "description": "Análise em andamento"
            },
            "factOpinion": {
                "score": 75,
                "label": "Misto",
                "description": "Análise em andamento"
            },
            "temporalContext": {
                "score": 80,
                "label": "Recente",
                "description": "Análise em andamento"
            }
        }
    
    def _get_fallback_analysis(self) -> Dict:
        """Fallback analysis when API fails"""
        return {
            "analysis": "Análise preliminar concluída com dados simulados (API indisponível).",
            "sourceReliability": 75,
            "factualConsistency": 80,
            "contentQuality": 75,
            "technicalIntegrity": 85,
            "details": self._get_default_details()
        }

# Singleton instance
ai_analyzer = AIAnalyzer()
