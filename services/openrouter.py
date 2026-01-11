"""
OpenRouter API Service for PostPro.
Handles text and image generation with schema validation.
"""

import json
import time
import logging
import requests
from typing import Optional
from decimal import Decimal
from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

# API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
DEFAULT_TIMEOUT = 120
MAX_RETRIES = 3
RETRY_DELAY = 2


# ============================================================================
# Response Schemas (Pydantic)
# ============================================================================

class OpenRouterUsage(BaseModel):
    """Token usage from OpenRouter."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class OpenRouterTextResult:
    """Normalized text generation result."""
    content: str
    model: str
    usage: dict
    raw: dict
    cost: Decimal


@dataclass
class OpenRouterImageResult:
    """Normalized image generation result."""
    image_data_url: str
    model: str
    raw: dict
    cost: Decimal


# Agent Response Schemas
class ResearchSchema(BaseModel):
    """Research agent output schema."""
    statistics: list[str] = Field(..., min_length=3)
    trends: list[str] = Field(..., min_length=2)
    questions: list[str] = Field(..., min_length=3)
    key_points: list[str] = Field(default=[], description="Key points to cover in the article")


class StrategySchema(BaseModel):
    """Strategy agent output schema."""
    title: str = Field(..., max_length=300)
    meta_description: str = Field(..., max_length=300)
    slug: str = Field(default="", description="URL-friendly slug")
    h2_sections: list[str] = Field(..., min_length=5, max_length=8)
    image_alt_text: str = Field(default="", description="Alt text for featured image")


# ============================================================================
# Pricing Tables
# ============================================================================

# Prices per 1M tokens (input/output)
PRICING_PER_MILLION = {
    # Anthropic
    "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
    
    # OpenAI
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4-turbo": {"input": 10.00, "output": 30.00},
    
    # Google
    "google/gemini-pro-1.5": {"input": 1.25, "output": 5.00},
    "google/gemini-flash-1.5": {"input": 0.075, "output": 0.30},
    
    # Meta
    "meta-llama/llama-3.1-70b-instruct": {"input": 0.52, "output": 0.75},
    "meta-llama/llama-3.1-8b-instruct": {"input": 0.06, "output": 0.06},
    
    # Default fallback
    "_default": {"input": 1.00, "output": 3.00},
}

# Image prices per generation
IMAGE_PRICING = {
    "openai/gpt-4o": 0.02,  # Per image
    "openai/gpt-4o-mini": 0.01,
    "_default": 0.02,
}


# ============================================================================
# Custom Exceptions
# ============================================================================

class OpenRouterError(Exception):
    """Base OpenRouter error."""
    pass


class InsufficientCreditsError(OpenRouterError):
    """Raised when OpenRouter account has no credits."""
    pass


class RateLimitError(OpenRouterError):
    """Raised when rate limited."""
    pass


class InvalidResponseError(OpenRouterError):
    """Raised when response doesn't match expected schema."""
    pass


# ============================================================================
# OpenRouter Service
# ============================================================================

class OpenRouterService:
    """
    Service for interacting with OpenRouter API.
    Supports text and image generation with retry logic.
    """
    
    def __init__(self, api_key: str, site_url: str = "", site_name: str = "PostPro"):
        self.api_key = api_key
        self.site_url = site_url
        self.site_name = site_name
    
    def _get_headers(self) -> dict:
        """Build request headers."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name
        return headers
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
        """Calculate cost based on token usage."""
        pricing = PRICING_PER_MILLION.get(model, PRICING_PER_MILLION["_default"])
        
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        
        return Decimal(str(round(input_cost + output_cost, 6)))
    
    def _calculate_image_cost(self, model: str) -> Decimal:
        """Calculate cost for image generation."""
        price = IMAGE_PRICING.get(model, IMAGE_PRICING["_default"])
        return Decimal(str(price))
    
    def generate_text(
        self,
        messages: list[dict],
        model: str = "anthropic/claude-3.5-sonnet",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> OpenRouterTextResult:
        """
        Generate text completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            OpenRouterTextResult with content, usage, and cost
        
        Raises:
            InsufficientCreditsError: If no credits
            RateLimitError: If rate limited
            OpenRouterError: For other errors
        """
        # Validate messages
        valid_messages = [
            msg for msg in messages
            if msg.get('role') and msg.get('content')
        ]
        
        if not valid_messages:
            raise OpenRouterError("No valid messages provided")
        
        payload = {
            "model": model,
            "messages": valid_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    OPENROUTER_API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=DEFAULT_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    
                    return OpenRouterTextResult(
                        content=content,
                        model=model,
                        usage={
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0),
                        },
                        raw=data,
                        cost=self._calculate_cost(
                            model,
                            usage.get("prompt_tokens", 0),
                            usage.get("completion_tokens", 0)
                        )
                    )
                
                elif response.status_code == 402:
                    raise InsufficientCreditsError("OpenRouter account has no credits")
                
                elif response.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    raise RateLimitError("Rate limit exceeded")
                
                else:
                    error_msg = response.text[:500]
                    logger.error(f"OpenRouter error {response.status_code}: {error_msg}")
                    last_error = OpenRouterError(f"API error: {response.status_code}")
                    
            except requests.Timeout:
                last_error = OpenRouterError("Request timeout")
            except requests.RequestException as e:
                last_error = OpenRouterError(f"Request failed: {str(e)}")
            
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
        
        raise last_error or OpenRouterError("Unknown error")
    
    def generate_image(
        self,
        prompt: str,
        model: str = "openai/gpt-4o-mini",
    ) -> OpenRouterImageResult:
        """
        Generate an image using OpenRouter's image modality.
        
        Args:
            prompt: Text description of the image
            model: Model that supports image generation
        
        Returns:
            OpenRouterImageResult with base64 data URL
        """
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"],
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    OPENROUTER_API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=DEFAULT_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract image from response
                    message = data["choices"][0]["message"]
                    images = message.get("images", [])
                    
                    if not images:
                        raise OpenRouterError("No image in response")
                    
                    image_data = images[0]
                    
                    # Validate it's a data URL
                    if not image_data.startswith("data:image/"):
                        raise OpenRouterError("Invalid image data URL")
                    
                    return OpenRouterImageResult(
                        image_data_url=image_data,
                        model=model,
                        raw=data,
                        cost=self._calculate_image_cost(model)
                    )
                
                elif response.status_code == 402:
                    raise InsufficientCreditsError("No credits for image generation")
                
                elif response.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    raise RateLimitError("Rate limit exceeded")
                
                else:
                    logger.error(f"Image generation error: {response.status_code}")
                    
            except requests.Timeout:
                pass
            except requests.RequestException as e:
                logger.error(f"Image request error: {e}")
            
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
        
        raise OpenRouterError("Image generation failed after retries")
    
    def generate_with_schema(
        self,
        messages: list[dict],
        schema_class: type[BaseModel],
        model: str = "anthropic/claude-3.5-sonnet",
        max_retries: int = 2,
    ) -> tuple[BaseModel, OpenRouterTextResult]:
        """
        Generate text and validate against a Pydantic schema.
        
        Args:
            messages: Chat messages
            schema_class: Pydantic model class for validation
            model: Model to use
            max_retries: Retry count for schema validation
        
        Returns:
            Tuple of (parsed_object, raw_result)
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            # Generate
            result = self.generate_text(messages, model=model)
            
            # Try to parse JSON
            content = result.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                data = json.loads(content)
                parsed = schema_class(**data)
                return parsed, result
                
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                logger.warning(f"Schema validation failed attempt {attempt + 1}: {e}")
                
                if attempt < max_retries:
                    # Add correction prompt
                    messages = messages + [
                        {"role": "assistant", "content": result.content},
                        {
                            "role": "user",
                            "content": f"Your response was not valid JSON or didn't match the schema. "
                                      f"Error: {str(e)}\n\n"
                                      f"Please return ONLY valid JSON matching this schema: "
                                      f"{schema_class.model_json_schema()}"
                        }
                    ]
        
        raise InvalidResponseError(f"Failed to get valid schema response: {last_error}")
    
    def validate_api_key(self) -> tuple[bool, str]:
        """Validate the API key by fetching models."""
        try:
            response = requests.get(
                OPENROUTER_MODELS_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "API key valid"
            elif response.status_code == 401:
                return False, "Invalid API key"
            else:
                return False, f"Error: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"Connection error: {e}"
