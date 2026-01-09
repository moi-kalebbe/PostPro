"""
Pollinations Service for PostPro.
Image generation via Pollinations.ai
"""

import logging
import requests
import hashlib
from typing import Optional

logger = logging.getLogger(__name__)

# API Configuration
POLLINATIONS_BASE_URL = 'https://image.pollinations.ai'
POLLINATIONS_MODELS_URL = 'https://image.pollinations.ai/models'


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
        nologo: bool = True
    ) -> str:
        """
        Generate image and return URL.
        
        Pollinations uses GET requests with query parameters.
        The URL itself is the image.
        
        Args:
            prompt: Text description of the image
            model: Model name (e.g., 'flux', 'turbo', 'flux-realism')
            width: Image width in pixels
            height: Image height in pixels
            seed: Random seed for reproducibility (if None, uses hash of prompt)
            safe: Enable safe mode (filter NSFW content)
            private: Private generation (not stored publicly)
            enhance: Auto-enhance prompt
            nologo: Remove Pollinations logo
        
        Returns:
            Image URL (the URL is the image itself)
        """
        # Generate seed from prompt if not provided (for idempotency)
        if seed is None:
            seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
        
        # Build URL with query parameters
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
        
        # URL encode the prompt
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Build final URL
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        image_url = f"{POLLINATIONS_BASE_URL}/prompt/{encoded_prompt}?{query_string}"
        
        logger.info(f"Generated Pollinations image URL with model {model}, size {width}x{height}")
        
        return image_url
    
    def generate_image_for_post(
        self,
        title: str,
        keyword: str,
        model: str = 'flux',
        width: int = 1920,
        height: int = 1080,
        external_id: Optional[str] = None,
        **kwargs
    ) -> str:
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
            Image URL
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
