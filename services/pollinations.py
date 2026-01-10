"""
Pollinations Service for PostPro.
Image generation via Pollinations.ai
"""

import base64
import logging
import requests
import hashlib
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)

# API Configuration
POLLINATIONS_BASE_URL = 'https://image.pollinations.ai'
POLLINATIONS_MODELS_URL = 'https://image.pollinations.ai/models'
DEFAULT_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 2


# ============================================================================
# Pricing (approximate costs in USD)
# ============================================================================

IMAGE_PRICING = {
    "turbo": Decimal("0.001"),      # Ultra-fast, basic quality
    "flux": Decimal("0.003"),        # High quality, moderate speed  
    "flux-realism": Decimal("0.005"), # Photorealistic
    "flux-anime": Decimal("0.003"),   # Anime style
    "flux-3d": Decimal("0.003"),      # 3D rendering
    "gptimage": Decimal("0.010"),     # GPT-powered
    "gptimage-large": Decimal("0.015"), # Premium GPT-powered
    "_default": Decimal("0.003"),
}


@dataclass
class PollinationsImageResult:
    """Normalized image generation result."""
    image_data_url: str
    image_url: str
    model: str
    width: int
    height: int
    cost: Decimal
    seed: Optional[int] = None


class PollinationsError(Exception):
    """Base Pollinations error."""
    pass


class PollinationsService:
    """
    Image generation via Pollinations.ai
    """
    
    def get_available_models(self) -> list[str]:
        """
        Fetch list of available models from Pollinations.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(POLLINATIONS_MODELS_URL, timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                logger.info(f"Fetched {len(models)} models from Pollinations")
                return models
            else:
                logger.error(f"Failed to fetch Pollinations models: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Error fetching Pollinations models: {e}")
            return []
    
    def _calculate_cost(self, model: str) -> Decimal:
        """Calculate cost for image generation."""
        return IMAGE_PRICING.get(model, IMAGE_PRICING["_default"])
    
    def generate_image(
        self,
        prompt: str,
        model: str = 'flux',
        width: int = 1920,
        height: int = 1080,
        seed: Optional[int] = None,
        safe: bool = True,
        private: bool = True,
        enhance: bool = False,
        nologo: bool = True,
        download: bool = True
    ) -> PollinationsImageResult:
        """
        Generate image and optionally download as base64.
        
        Args:
            prompt: Text description of the image
            model: Model name (e.g., 'flux', 'turbo', 'flux-realism')
            width: Image width in pixels
            height: Image height in pixels
            seed: Random seed for reproducibility
            safe: Enable safe mode
            private: Private generation
            enhance: Auto-enhance prompt
            nologo: Remove Pollinations logo
            download: If True, downloads image and returns base64 data URL
        
        Returns:
            PollinationsImageResult with image data
        
        Raises:
            PollinationsError: If generation fails
        """
        # Generate seed from prompt if not provided
        if seed is None:
            seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
        
        # Build URL with query parameters
        import urllib.parse
        params = {
            'model': model,
            'width': width,
            'height': height,
            'seed': seed,
            'safe': 'true' if safe else 'false',
            'private': 'true' if private else 'false',
            'enhance': 'true' if enhance else 'false',
            'nologo': 'true' if nologo else 'false'
        }
        
        encoded_prompt = urllib.parse.quote(prompt)
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        image_url = f"{POLLINATIONS_BASE_URL}/prompt/{encoded_prompt}?{query_string}"
        
        logger.info(f"Generating Pollinations image with model {model}, size {width}x{height}")
        
        # Download image and convert to base64
        image_data_url = ""
        
        if download:
            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    response = requests.get(
                        image_url,
                        timeout=DEFAULT_TIMEOUT,
                        headers={"Accept": "image/*"}
                    )
                    
                    if response.status_code == 200:
                        content_type = response.headers.get("Content-Type", "image/png")
                        if ";" in content_type:
                            content_type = content_type.split(";")[0].strip()
                        
                        image_bytes = response.content
                        base64_data = base64.b64encode(image_bytes).decode("utf-8")
                        image_data_url = f"data:{content_type};base64,{base64_data}"
                        
                        logger.info(f"Image downloaded successfully ({len(image_bytes)} bytes)")
                        break
                    
                    elif response.status_code == 429:
                        logger.warning(f"Rate limited (attempt {attempt + 1})")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(RETRY_DELAY * (attempt + 2))
                            continue
                        raise PollinationsError("Rate limit exceeded")
                    
                    else:
                        logger.warning(f"Pollinations error {response.status_code} (attempt {attempt + 1})")
                        last_error = PollinationsError(f"API error: {response.status_code}")
                
                except requests.Timeout:
                    logger.warning(f"Timeout (attempt {attempt + 1})")
                    last_error = PollinationsError("Request timed out")
                
                except requests.RequestException as e:
                    logger.error(f"Request error: {e}")
                    last_error = PollinationsError(f"Request failed: {str(e)}")
                
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
            
            if not image_data_url and last_error:
                raise last_error
        
        return PollinationsImageResult(
            image_data_url=image_data_url,
            image_url=image_url,
            model=model,
            width=width,
            height=height,
            cost=self._calculate_cost(model),
            seed=seed,
        )
    
    def generate_image_for_post(
        self,
        title: str,
        keyword: str,
        model: str = 'flux',
        width: int = 1920,
        height: int = 1080,
        external_id: Optional[str] = None,
        **kwargs
    ) -> PollinationsImageResult:
        """
        Generate image for a blog post with optimized prompt.
        
        Args:
            title: Post title
            keyword: Focus keyword
            model: Pollinations model
            width: Image width
            height: Image height
            external_id: External ID for seed generation (idempotency)
            **kwargs: Additional parameters for generate_image
        
        Returns:
            PollinationsImageResult with image data
        """
        # Build optimized prompt for blog post
        prompt = f"Professional blog post featured image: {title}. Theme: {keyword}. High quality, modern, clean design."
        
        # Use external_id for seed if provided (ensures same image for same post)
        if external_id:
            seed = int(hashlib.md5(external_id.encode()).hexdigest()[:8], 16)
            kwargs['seed'] = seed
        
        return self.generate_image(
            prompt=prompt,
            model=model,
            width=width,
            height=height,
            **kwargs
        )
    
    def validate_model(self, model: str) -> bool:
        """
        Check if model name is valid.
        
        Args:
            model: Model name to validate
        
        Returns:
            True if valid, False otherwise
        """
        available_models = self.get_available_models()
        return model in available_models
