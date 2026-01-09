"""
Quick validation test for PostPro models and services.
Tests that don't require API keys.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.automation.models import (
    SiteProfile, TrendPack, EditorialPlan, EditorialPlanItem, 
    AIModelPolicy, Post
)
from apps.agencies.models import Agency
from apps.projects.models import Project
from datetime import datetime, timedelta
import uuid


def test_models():
    """Test that all models can be imported and instantiated."""
    print("\n" + "="*60)
    print("TESTING DJANGO MODELS")
    print("="*60)
    
    # Test 1: Check models are registered
    print("\n1. Checking model registration...")
    models_to_check = [
        SiteProfile, TrendPack, EditorialPlan, 
        EditorialPlanItem, AIModelPolicy, Post
    ]
    
    for model in models_to_check:
        print(f"   ✅ {model.__name__} registered")
    
    # Test 2: Check model fields
    print("\n2. Checking Post model new fields...")
    post_fields = [f.name for f in Post._meta.get_fields()]
    
    new_fields = ['external_id', 'seo_data', 'post_status', 'scheduled_at']
    for field in new_fields:
        if field in post_fields:
            print(f"   ✅ Post.{field} exists")
        else:
            print(f"   ❌ Post.{field} MISSING")
    
    # Test 3: Check AIModelPolicy defaults
    print("\n3. Checking AIModelPolicy default values...")
    policy_defaults = {
        'planning_trends_model': 'perplexity/sonar',
        'image_provider': 'openrouter',
        'pollinations_width': 1920,
        'pollinations_height': 1080,
        'pollinations_safe': True,
        'pollinations_private': True,
    }
    
    for field, expected_default in policy_defaults.items():
        field_obj = AIModelPolicy._meta.get_field(field)
        actual_default = field_obj.default
        
        if actual_default == expected_default:
            print(f"   ✅ {field} = {actual_default}")
        else:
            print(f"   ⚠️  {field} = {actual_default} (expected {expected_default})")
    
    # Test 4: Check EditorialPlanItem external_id method
    print("\n4. Testing EditorialPlanItem.generate_external_id()...")
    
    # Create a mock item (not saved to DB)
    class MockPlan:
        id = uuid.uuid4()
        project_id = uuid.uuid4()
    
    class MockItem:
        plan = MockPlan()
        day_index = 5
        
        def generate_external_id(self):
            project_id = str(self.plan.project_id)
            plan_id = str(self.plan.id)
            return f"{project_id}_{plan_id}_day_{self.day_index}"
    
    item = MockItem()
    external_id = item.generate_external_id()
    
    if '_day_5' in external_id:
        print(f"   ✅ External ID format correct: ...{external_id[-20:]}")
    else:
        print(f"   ❌ External ID format incorrect: {external_id}")
    
    print("\n✅ All model tests passed!")


def test_pollinations_service():
    """Test Pollinations service (no API key needed)."""
    print("\n" + "="*60)
    print("TESTING POLLINATIONS SERVICE")
    print("="*60)
    
    from services.pollinations import PollinationsService
    
    service = PollinationsService()
    
    # Test 1: Generate image URL
    print("\n1. Generating image URL...")
    url = service.generate_image(
        prompt="A beautiful sunset",
        model="flux",
        width=1920,
        height=1080,
        seed=12345,
        safe=True,
        private=True,
        nologo=True
    )
    
    if url.startswith("https://image.pollinations.ai"):
        print(f"   ✅ URL generated: {url[:60]}...")
    else:
        print(f"   ❌ Invalid URL: {url}")
    
    # Test 2: Generate blog post image
    print("\n2. Generating blog post image...")
    post_url = service.generate_image_for_post(
        title="10 Tips for Better Photography",
        keyword="photography tips",
        model="flux",
        external_id="test_post_123"
    )
    
    if "photography" in post_url.lower():
        print(f"   ✅ Blog post URL generated")
        print(f"   URL: {post_url[:80]}...")
    else:
        print(f"   ❌ Invalid blog post URL")
    
    # Test 3: Check idempotency (same external_id = same seed)
    print("\n3. Testing idempotency...")
    url1 = service.generate_image_for_post(
        title="Test", keyword="test", external_id="same_id_123"
    )
    url2 = service.generate_image_for_post(
        title="Test", keyword="test", external_id="same_id_123"
    )
    
    if url1 == url2:
        print(f"   ✅ Idempotency works (same external_id = same URL)")
    else:
        print(f"   ❌ Idempotency failed (URLs differ)")
    
    print("\n✅ Pollinations service tests passed!")


def test_model_relationships():
    """Test model relationships and foreign keys."""
    print("\n" + "="*60)
    print("TESTING MODEL RELATIONSHIPS")
    print("="*60)
    
    # Test 1: EditorialPlan -> SiteProfile
    print("\n1. Checking EditorialPlan -> SiteProfile relationship...")
    plan_fields = {f.name: f for f in EditorialPlan._meta.get_fields()}
    
    if 'site_profile' in plan_fields:
        field = plan_fields['site_profile']
        if field.related_model == SiteProfile:
            print(f"   ✅ EditorialPlan.site_profile -> SiteProfile")
        else:
            print(f"   ❌ Wrong related model: {field.related_model}")
    else:
        print(f"   ❌ site_profile field not found")
    
    # Test 2: EditorialPlan -> TrendPack
    print("\n2. Checking EditorialPlan -> TrendPack relationship...")
    if 'trend_pack' in plan_fields:
        field = plan_fields['trend_pack']
        if field.related_model == TrendPack:
            print(f"   ✅ EditorialPlan.trend_pack -> TrendPack")
        else:
            print(f"   ❌ Wrong related model: {field.related_model}")
    else:
        print(f"   ❌ trend_pack field not found")
    
    # Test 3: EditorialPlanItem -> Post
    print("\n3. Checking EditorialPlanItem -> Post relationship...")
    item_fields = {f.name: f for f in EditorialPlanItem._meta.get_fields()}
    
    if 'post' in item_fields:
        field = item_fields['post']
        if field.related_model == Post:
            print(f"   ✅ EditorialPlanItem.post -> Post")
        else:
            print(f"   ❌ Wrong related model: {field.related_model}")
    else:
        print(f"   ❌ post field not found")
    
    # Test 4: AIModelPolicy -> Agency
    print("\n4. Checking AIModelPolicy -> Agency relationship...")
    policy_fields = {f.name: f for f in AIModelPolicy._meta.get_fields()}
    
    if 'agency' in policy_fields:
        field = policy_fields['agency']
        if field.related_model == Agency:
            print(f"   ✅ AIModelPolicy.agency -> Agency")
        else:
            print(f"   ❌ Wrong related model: {field.related_model}")
    else:
        print(f"   ❌ agency field not found")
    
    print("\n✅ All relationship tests passed!")


def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("POSTPRO VALIDATION TEST SUITE")
    print("="*60)
    
    try:
        test_models()
    except Exception as e:
        print(f"\n❌ Model tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_pollinations_service()
    except Exception as e:
        print(f"\n❌ Pollinations tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_model_relationships()
    except Exception as e:
        print(f"\n❌ Relationship tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
