"""
Perplexity Trends Service for PostPro.
Generates trend packs using Perplexity Sonar via OpenRouter.
"""

import logging
from typing import Optional
from decimal import Decimal
from datetime import datetime, timedelta
from services.openrouter import OpenRouterService

logger = logging.getLogger(__name__)


class PerplexityTrendsService:
    """
    Generate trend packs using Perplexity Sonar via OpenRouter.
    """
    
    def __init__(self, openrouter_service: OpenRouterService):
        self.openrouter = openrouter_service
    
    def generate_trend_pack(
        self,
        keywords: list[str],
        model: str = 'perplexity/sonar',
        recency_days: int = 7,
        max_insights: int = 20
    ) -> dict:
        """
        Generate trend pack for given keywords.
        
        Args:
            keywords: List of 5-10 keywords
            model: Perplexity model ('perplexity/sonar' or 'perplexity/sonar-pro-search')
            recency_days: Search recency window (7 or 30 days)
            max_insights: Maximum number of insights to generate
        
        Returns:
            {
                'insights': [
                    {
                        'title': str,
                        'summary': str,
                        'references': [{'title': str, 'url': str, 'date': str}],
                        'relevance_score': float
                    }
                ],
                'tokens_used': int,
                'cost': Decimal
            }
        """
        logger.info(f"Generating trend pack for {len(keywords)} keywords with {model}")
        
        # Build prompt for Perplexity
        keywords_str = ', '.join(keywords)
        
        prompt = f"""You are a trend research analyst. Analyze current trends and insights related to these keywords: {keywords_str}

Search for the most relevant and recent information from the last {recency_days} days.

For each trend insight you find:
1. Provide a clear, descriptive title
2. Write a concise summary (2-3 sentences)
3. Include references with titles, URLs, and dates
4. Assign a relevance score (0.0 to 1.0) based on how well it matches the keywords

Return EXACTLY {max_insights} trend insights in valid JSON format:

{{
  "insights": [
    {{
      "title": "Trend Title",
      "summary": "Brief summary of the trend...",
      "references": [
        {{
          "title": "Article Title",
          "url": "https://...",
          "date": "2026-01-08"
        }}
      ],
      "relevance_score": 0.95
    }}
  ]
}}

Focus on actionable, current trends that would be valuable for content creation."""
        
        messages = [
            {
                'role': 'user',
                'content': prompt
            }
        ]
        
        try:
            # Call Perplexity via OpenRouter
            result = self.openrouter.generate_text(
                messages=messages,
                model=model,
                temperature=0.7,
                max_tokens=4096
            )
            
            # Parse response
            import json
            content = result.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            insights = data.get('insights', [])
            
            logger.info(f"Generated {len(insights)} trend insights")
            
            return {
                'insights': insights,
                'tokens_used': result.usage['total_tokens'],
                'cost': result.cost
            }
            
        except Exception as e:
            logger.error(f"Failed to generate trend pack: {e}")
            raise
    
    def validate_trend_pack(self, trend_pack_data: dict) -> bool:
        """
        Validate trend pack structure.
        
        Args:
            trend_pack_data: Trend pack dict
        
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(trend_pack_data, dict):
            return False
        
        insights = trend_pack_data.get('insights', [])
        
        if not isinstance(insights, list) or len(insights) == 0:
            return False
        
        # Validate each insight
        for insight in insights:
            if not all(key in insight for key in ['title', 'summary', 'references', 'relevance_score']):
                return False
            
            if not isinstance(insight['references'], list):
                return False
        
        return True
    
    def get_top_insights(self, trend_pack_data: dict, limit: int = 10) -> list[dict]:
        """
        Get top N insights by relevance score.
        
        Args:
            trend_pack_data: Trend pack dict
            limit: Number of top insights to return
        
        Returns:
            List of top insights sorted by relevance_score
        """
        insights = trend_pack_data.get('insights', [])
        
        # Sort by relevance score (descending)
        sorted_insights = sorted(
            insights,
            key=lambda x: x.get('relevance_score', 0),
            reverse=True
        )
        
        return sorted_insights[:limit]
