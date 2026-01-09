"""
OpenRouter Models Service for PostPro.
Fetches and caches available models from OpenRouter API.
"""

import logging
import requests
from typing import Optional
from django.core.cache import cache
from decimal import Decimal

logger = logging.getLogger(__name__)

# API Configuration
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
CACHE_KEY_PREFIX = 'openrouter_models'
CACHE_DURATION = 3600  # 1 hour


class OpenRouterModelsService:
    """
    Fetch and cache available models from OpenRouter API.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_models(self, force_refresh: bool = False) -> list[dict]:
        """
        Fetch models list with caching.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
        
        Returns:
            List of model dicts with structure:
            [{
                'id': str,
                'name': str,
                'pricing': {'prompt': str, 'completion': str, 'image': str},
                'context_length': int,
                'modalities': list[str],  # ['text', 'image']
                'architecture': dict,
                'top_provider': dict,
                ...
            }]
        """
        cache_key = f'{CACHE_KEY_PREFIX}_all'
        
        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"Returning {len(cached)} models from cache")
                return cached
        
        try:
            response = requests.get(
                OPENROUTER_MODELS_URL,
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                
                # Cache the result
                cache.set(cache_key, models, CACHE_DURATION)
                logger.info(f"Fetched and cached {len(models)} models from OpenRouter")
                
                return models
            else:
                logger.error(f"Failed to fetch models: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Error fetching models from OpenRouter: {e}")
            return []
    
    def get_text_models(self, force_refresh: bool = False) -> list[dict]:
        """
        Filter models that support text generation.
        
        Returns:
            List of text-capable models
        """
        all_models = self.get_models(force_refresh)
        
        text_models = [
            model for model in all_models
            if 'text' in model.get('modalities', []) or not model.get('modalities')
        ]
        
        logger.info(f"Found {len(text_models)} text models")
        return text_models
    
    def get_image_models(self, force_refresh: bool = False) -> list[dict]:
        """
        Filter models that support image generation.
        
        Returns:
            List of image-capable models
        """
        all_models = self.get_models(force_refresh)
        
        image_models = [
            model for model in all_models
            if 'image' in model.get('modalities', [])
        ]
        
        logger.info(f"Found {len(image_models)} image models")
        return image_models
    
    def get_model_by_id(self, model_id: str, force_refresh: bool = False) -> Optional[dict]:
        """
        Get specific model details by ID.
        
        Args:
            model_id: Model identifier (e.g., 'openai/gpt-4o')
        
        Returns:
            Model dict or None if not found
        """
        all_models = self.get_models(force_refresh)
        
        for model in all_models:
            if model.get('id') == model_id:
                return model
        
        logger.warning(f"Model {model_id} not found in catalog")
        return None
    
    def validate_model_exists(self, model_id: str, force_refresh: bool = False) -> bool:
        """
        Check if model ID exists in current catalog.
        
        Args:
            model_id: Model identifier
        
        Returns:
            True if model exists, False otherwise
        """
        return self.get_model_by_id(model_id, force_refresh) is not None
    
    def get_model_pricing(self, model_id: str, force_refresh: bool = False) -> Optional[dict]:
        """
        Get pricing information for a specific model.
        
        Args:
            model_id: Model identifier
        
        Returns:
            Pricing dict with 'prompt', 'completion', 'image' keys (all in USD per token/image)
            or None if model not found
        """
        model = self.get_model_by_id(model_id, force_refresh)
        
        if not model:
            return None
        
        pricing = model.get('pricing', {})
        
        return {
            'prompt': Decimal(pricing.get('prompt', '0')),
            'completion': Decimal(pricing.get('completion', '0')),
            'image': Decimal(pricing.get('image', '0')),
        }
    
    def get_recommended_models_by_category(self, category: str = 'budget') -> dict:
        """
        Get recommended models by category (free/budget/premium).
        
        Args:
            category: 'free', 'budget', or 'premium'
        
        Returns:
            Dict with recommended model IDs for each stage
        """
        presets = {
            'free': {
                'text': [
                    'meta-llama/llama-3.3-70b-instruct:free',
                    'mistralai/devstral-2-2512:free'
                ],
                'image': []  # No free image models typically
            },
            'budget': {
                'text': [
                    'mistralai/mistral-nemo',
                    'openai/gpt-oss-120b',
                    'openai/gpt-5-nano',
                    'deepseek/deepseek-v3.1',
                    'deepseek/deepseek-v3-0324'
                ],
                'image': [
                    'sourceful/riverflow-v2-fast-preview',
                    'sourceful/riverflow-v2-standard-preview',
                    'bytedance/seedream-4.5'
                ]
            },
            'premium': {
                'text': [
                    'google/gemini-2.5-pro',
                    'openai/gpt-5.2',
                    'openai/gpt-5-mini'
                ],
                'image': [
                    'black-forest-labs/flux.2-pro',
                    'black-forest-labs/flux.2-max',
                    'google/gemini-2.5-flash-image',
                    'openai/gpt-5-image-mini'
                ]
            }
        }
        
        return presets.get(category, presets['budget'])
    
    def filter_available_from_preset(self, preset_models: list[str]) -> list[str]:
        """
        Filter preset model IDs to only those currently available in OpenRouter.
        
        Args:
            preset_models: List of model IDs from preset
        
        Returns:
            List of model IDs that are actually available
        """
        all_models = self.get_models()
        available_ids = {model['id'] for model in all_models}
        
        return [model_id for model_id in preset_models if model_id in available_ids]
