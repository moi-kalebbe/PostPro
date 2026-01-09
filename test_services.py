"""
Test script for OpenRouter Models API and Pollinations integration.
Run this to verify the services are working correctly.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from services.openrouter_models import OpenRouterModelsService
from services.pollinations import PollinationsService

def test_openrouter_models():
    """Test OpenRouter Models API."""
    print("\n" + "="*60)
    print("TESTING OPENROUTER MODELS API")
    print("="*60)
    
    # You need to provide an API key
    api_key = input("Enter your OpenRouter API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⚠️  Skipping OpenRouter test (no API key provided)")
        return
    
    service = OpenRouterModelsService(api_key)
    
    # Test 1: Fetch all models
    print("\n1. Fetching all models...")
    models = service.get_models()
    print(f"✅ Found {len(models)} total models")
    
    if models:
        print(f"   Sample model: {models[0]['id']}")
    
    # Test 2: Get text models
    print("\n2. Filtering text models...")
    text_models = service.get_text_models()
    print(f"✅ Found {len(text_models)} text models")
    
    # Test 3: Get image models
    print("\n3. Filtering image models...")
    image_models = service.get_image_models()
    print(f"✅ Found {len(image_models)} image models")
    
    if image_models:
        print(f"   Sample image model: {image_models[0]['id']}")
    
    # Test 4: Get specific model
    print("\n4. Getting specific model (perplexity/sonar)...")
    model = service.get_model_by_id('perplexity/sonar')
    if model:
        print(f"✅ Found model: {model['name']}")
        print(f"   Pricing: {model.get('pricing', {})}")
    else:
        print("❌ Model not found")
    
    # Test 5: Get recommended models
    print("\n5. Getting recommended models (budget category)...")
    recommended = service.get_recommended_models_by_category('budget')
    print(f"✅ Budget text models: {recommended['text'][:3]}")
    print(f"✅ Budget image models: {recommended['image'][:2]}")
    
    print("\n✅ OpenRouter Models API test completed!")


def test_pollinations():
    """Test Pollinations API."""
    print("\n" + "="*60)
    print("TESTING POLLINATIONS API")
    print("="*60)
    
    service = PollinationsService()
    
    # Test 1: Get available models
    print("\n1. Fetching available models...")
    models = service.get_available_models()
    print(f"✅ Found {len(models)} Pollinations models")
    
    if models:
        print(f"   Available models: {', '.join(models[:5])}")
    
    # Test 2: Generate image URL
    print("\n2. Generating image URL...")
    prompt = "A beautiful sunset over mountains, professional photography"
    image_url = service.generate_image(
        prompt=prompt,
        model='flux',
        width=1920,
        height=1080,
        safe=True,
        private=True,
        nologo=True
    )
    print(f"✅ Generated image URL:")
    print(f"   {image_url}")
    
    # Test 3: Generate image for blog post
    print("\n3. Generating image for blog post...")
    post_image_url = service.generate_image_for_post(
        title="10 Tips for Better Photography",
        keyword="photography tips",
        model='flux',
        external_id="test_post_123"
    )
    print(f"✅ Generated blog post image URL:")
    print(f"   {post_image_url}")
    
    print("\n✅ Pollinations API test completed!")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("POSTPRO SERVICES TEST SUITE")
    print("="*60)
    
    try:
        test_openrouter_models()
    except Exception as e:
        print(f"\n❌ OpenRouter test failed: {e}")
    
    try:
        test_pollinations()
    except Exception as e:
        print(f"\n❌ Pollinations test failed: {e}")
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
