import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from services.openrouter_models import OpenRouterModelsService
from apps.agencies.models import Agency

def check_models():
    # Get API key from first agency
    agency = Agency.objects.first()
    if not agency:
        print("No agency found")
        return
        
    api_key = agency.get_openrouter_key()
    if not api_key:
        print("No API key found in agency")
        return

    service = OpenRouterModelsService(api_key)
    print("Fetching models from OpenRouter...")
    models = service.get_models(force_refresh=True)
    
    keywords = ["flux", "gemini", "stable", "diffusion", "dall-e"]
    
    print(f"\nScanning {len(models)} models for keywords: {keywords}\n")
    
    found = []
    for m in models:
        mid = m['id'].lower()
        if any(k in mid for k in keywords):
            # Check if it supports image
            is_image = False
            arch = m.get('architecture', {})
            if 'image' in arch.get('output_modalities', []) or 'image' in m.get('modalities', []):
                is_image = True
            
            # Print if relevant
            msg = f"{m['id']} (Image: {is_image})"
            print(msg)
            if is_image:
                found.append(m['id'])

    print("\nConfirmed Image Models:")
    for f in found:
        print(f" - {f}")

if __name__ == "__main__":
    check_models()
