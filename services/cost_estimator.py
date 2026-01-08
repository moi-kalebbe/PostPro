"""
Cost Estimator Service for PostPro.
Estimates costs for dry-run simulations without calling OpenRouter.
"""

from decimal import Decimal
from typing import Optional
from dataclasses import dataclass


@dataclass
class EstimationResult:
    """Cost estimation result."""
    total_posts: int
    research_tokens: int
    strategy_tokens: int
    article_tokens: int
    total_tokens: int
    text_cost: Decimal
    image_count: int
    image_cost: Decimal
    total_cost: Decimal


# Token estimation heuristics per step
TOKEN_ESTIMATES = {
    "research": {
        "prompt": 500,
        "completion": 700,
        "total": 1200,
    },
    "strategy": {
        "prompt": 400,
        "completion": 500,
        "total": 900,
    },
    "article": {
        "prompt": 1500,
        "completion": 5000,
        "total": 6500,
    },
}

# Tone adjustments (multipliers)
TONE_MULTIPLIERS = {
    "formal": 1.0,
    "casual": 1.0,
    "technical": 1.3,  # Technical content uses more tokens
}

# Model pricing (per 1M tokens, average of input/output)
MODEL_PRICING = {
    "anthropic/claude-3.5-sonnet": 9.0,
    "anthropic/claude-3-haiku": 0.75,
    "openai/gpt-4o": 6.25,
    "openai/gpt-4o-mini": 0.375,
    "openai/gpt-4-turbo": 20.0,
    "google/gemini-pro-1.5": 3.125,
    "google/gemini-flash-1.5": 0.1875,
    "meta-llama/llama-3.1-70b-instruct": 0.635,
    "meta-llama/llama-3.1-8b-instruct": 0.06,
    "_default": 3.0,
}

# Image pricing per image
IMAGE_PRICING = {
    "openai/gpt-4o": 0.02,
    "openai/gpt-4o-mini": 0.01,
    "_default": 0.02,
}


class CostEstimator:
    """
    Estimates costs for batch jobs without calling APIs.
    Used for dry-run / simulation mode.
    """
    
    def __init__(
        self,
        text_model: str = "anthropic/claude-3.5-sonnet",
        image_model: str = "openai/gpt-4o-mini",
        tone: str = "casual",
    ):
        self.text_model = text_model
        self.image_model = image_model
        self.tone = tone
        self.tone_multiplier = TONE_MULTIPLIERS.get(tone, 1.0)
    
    def _get_text_price(self) -> Decimal:
        """Get price per 1M tokens for text model."""
        price = MODEL_PRICING.get(self.text_model, MODEL_PRICING["_default"])
        return Decimal(str(price))
    
    def _get_image_price(self) -> Decimal:
        """Get price per image."""
        price = IMAGE_PRICING.get(self.image_model, IMAGE_PRICING["_default"])
        return Decimal(str(price))
    
    def estimate_single_post(
        self,
        generate_image: bool = True,
    ) -> dict:
        """
        Estimate cost for a single post.
        
        Returns:
            Dict with token and cost breakdown
        """
        # Calculate tokens with tone adjustment
        research_tokens = int(TOKEN_ESTIMATES["research"]["total"] * self.tone_multiplier)
        strategy_tokens = int(TOKEN_ESTIMATES["strategy"]["total"] * self.tone_multiplier)
        article_tokens = int(TOKEN_ESTIMATES["article"]["total"] * self.tone_multiplier)
        
        total_tokens = research_tokens + strategy_tokens + article_tokens
        
        # Calculate text cost
        text_cost = (Decimal(total_tokens) / Decimal(1_000_000)) * self._get_text_price()
        
        # Image cost
        image_cost = self._get_image_price() if generate_image else Decimal(0)
        
        return {
            "research_tokens": research_tokens,
            "strategy_tokens": strategy_tokens,
            "article_tokens": article_tokens,
            "total_tokens": total_tokens,
            "text_cost": round(text_cost, 6),
            "image_cost": round(image_cost, 6),
            "total_cost": round(text_cost + image_cost, 6),
        }
    
    def estimate_batch(
        self,
        keyword_count: int,
        generate_images: bool = True,
    ) -> EstimationResult:
        """
        Estimate cost for a batch of keywords.
        
        Args:
            keyword_count: Number of keywords/posts to generate
            generate_images: Whether images will be generated
        
        Returns:
            EstimationResult with full breakdown
        """
        single = self.estimate_single_post(generate_image=generate_images)
        
        research_tokens = single["research_tokens"] * keyword_count
        strategy_tokens = single["strategy_tokens"] * keyword_count
        article_tokens = single["article_tokens"] * keyword_count
        total_tokens = single["total_tokens"] * keyword_count
        
        text_cost = single["text_cost"] * keyword_count
        image_count = keyword_count if generate_images else 0
        image_cost = single["image_cost"] * keyword_count
        total_cost = single["total_cost"] * keyword_count
        
        return EstimationResult(
            total_posts=keyword_count,
            research_tokens=research_tokens,
            strategy_tokens=strategy_tokens,
            article_tokens=article_tokens,
            total_tokens=total_tokens,
            text_cost=text_cost,
            image_count=image_count,
            image_cost=image_cost,
            total_cost=total_cost,
        )
    
    @staticmethod
    def estimate_from_options(
        keyword_count: int,
        text_model: str,
        image_model: str,
        tone: str,
        generate_images: bool,
    ) -> EstimationResult:
        """
        Static method to estimate from batch options.
        
        Convenience method for use in views/tasks.
        """
        estimator = CostEstimator(
            text_model=text_model,
            image_model=image_model,
            tone=tone,
        )
        return estimator.estimate_batch(
            keyword_count=keyword_count,
            generate_images=generate_images,
        )


def format_cost(cost: Decimal) -> str:
    """Format cost for display."""
    return f"${cost:.4f}"


def format_tokens(tokens: int) -> str:
    """Format token count for display."""
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.2f}M"
    elif tokens >= 1_000:
        return f"{tokens / 1_000:.1f}K"
    return str(tokens)
