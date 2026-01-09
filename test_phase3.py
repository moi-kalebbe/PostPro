"""
Test script for Phase 3: Editorial Pipeline Services
Tests SiteProfileService, EditorialPipelineService, and anti-cannibalization.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from services.site_profile import SiteProfileService
from services.editorial_pipeline import EditorialPipelineService
from apps.projects.models import Project
from apps.automation.models import SiteProfile, EditorialPlan
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_site_profile_service():
    """Test SiteProfileService WordPress REST API integration."""
    print("\n" + "="*60)
    print("TESTING SITE PROFILE SERVICE")
    print("="*60)
    
    # Test 1: Check if service can be instantiated
    print("\n1. Testing service instantiation...")
    
    # Get first project (or skip if none exists)
    project = Project.objects.first()
    
    if not project:
        print("   ⚠️  No projects found in database. Skipping test.")
        print("   💡 Create a project first to test this service.")
        return
    
    try:
        service = SiteProfileService(project)
        print(f"   ✅ Service created for project: {project.name}")
        print(f"   WordPress URL: {project.wordpress_url}")
    except Exception as e:
        print(f"   ❌ Failed to create service: {e}")
        return
    
    # Test 2: Test URL construction
    print("\n2. Testing WordPress REST API URL construction...")
    expected_url = f"{project.wordpress_url.rstrip('/')}/wp-json/wp/v2"
    
    if service.wp_rest_api == expected_url:
        print(f"   ✅ REST API URL correct: {service.wp_rest_api}")
    else:
        print(f"   ❌ REST API URL incorrect")
        print(f"      Expected: {expected_url}")
        print(f"      Got: {service.wp_rest_api}")
    
    # Test 3: Test anti-cannibalization helpers
    print("\n3. Testing anti-cannibalization helpers...")
    
    # Create mock profile
    mock_profile = SiteProfile(
        project=project,
        home_url=project.wordpress_url,
        site_name="Test Site",
        categories=[
            {'id': 1, 'name': 'Technology', 'slug': 'tech', 'count': 10},
            {'id': 2, 'name': 'Business', 'slug': 'business', 'count': 5}
        ],
        tags=[
            {'id': 1, 'name': 'AI', 'slug': 'ai', 'count': 8},
            {'id': 2, 'name': 'Marketing', 'slug': 'marketing', 'count': 6}
        ],
        recent_posts=[
            {'id': 1, 'title': '10 Tips for Better SEO', 'excerpt': '...', 'categories': [1], 'tags': [1]},
            {'id': 2, 'title': 'How to Use AI in Marketing', 'excerpt': '...', 'categories': [2], 'tags': [1, 2]}
        ]
    )
    
    # Test get_existing_titles
    titles = service.get_existing_titles(mock_profile)
    if len(titles) == 2:
        print(f"   ✅ Extracted {len(titles)} existing titles")
        print(f"      - {titles[0]}")
        print(f"      - {titles[1]}")
    else:
        print(f"   ❌ Expected 2 titles, got {len(titles)}")
    
    # Test get_existing_keywords
    keywords = service.get_existing_keywords(mock_profile)
    expected_keywords = {'technology', 'business', 'ai', 'marketing'}
    
    if keywords == expected_keywords:
        print(f"   ✅ Extracted keywords: {keywords}")
    else:
        print(f"   ⚠️  Keywords differ from expected")
        print(f"      Expected: {expected_keywords}")
        print(f"      Got: {keywords}")
    
    # Test analyze_content_themes
    themes = service.analyze_content_themes(mock_profile)
    if len(themes) > 0:
        print(f"   ✅ Identified {len(themes)} content themes")
        print(f"      Themes: {', '.join(themes[:5])}")
    else:
        print(f"   ❌ No themes identified")
    
    print("\n✅ SiteProfileService tests completed!")


def test_editorial_pipeline_service():
    """Test EditorialPipelineService title generation logic."""
    print("\n" + "="*60)
    print("TESTING EDITORIAL PIPELINE SERVICE")
    print("="*60)
    
    # Test 1: Check if service can be instantiated
    print("\n1. Testing service instantiation...")
    
    project = Project.objects.first()
    
    if not project:
        print("   ⚠️  No projects found in database. Skipping test.")
        return
    
    # Check if agency has OpenRouter key
    agency = project.agency
    api_key = agency.get_openrouter_key()
    
    if not api_key:
        print("   ⚠️  No OpenRouter API key configured for agency.")
        print("   💡 Configure API key to test full pipeline.")
        print("   Testing without API key (structure only)...")
    
    try:
        from services.openrouter import OpenRouterService
        
        if api_key:
            openrouter = OpenRouterService(api_key)
        else:
            # Mock service for testing
            openrouter = None
        
        if openrouter:
            service = EditorialPipelineService(project, openrouter)
            print(f"   ✅ Service created for project: {project.name}")
        else:
            print(f"   ⚠️  Service requires OpenRouter API key")
            
    except Exception as e:
        print(f"   ❌ Failed to create service: {e}")
        return
    
    # Test 2: Test anti-cannibalization logic
    print("\n2. Testing anti-cannibalization logic...")
    
    if openrouter:
        existing_titles = [
            "10 Tips for Better SEO",
            "How to Improve Your SEO Rankings",
            "Complete Guide to Content Marketing"
        ]
        
        # Test similar title (should fail)
        similar_title = "10 Best Tips for Better SEO"
        is_unique = service.check_anti_cannibalization(similar_title, existing_titles, threshold=0.7)
        
        if not is_unique:
            print(f"   ✅ Correctly detected similar title")
            print(f"      New: '{similar_title}'")
            print(f"      Existing: '{existing_titles[0]}'")
        else:
            print(f"   ❌ Failed to detect similar title")
        
        # Test unique title (should pass)
        unique_title = "The Future of Artificial Intelligence in Healthcare"
        is_unique = service.check_anti_cannibalization(unique_title, existing_titles, threshold=0.7)
        
        if is_unique:
            print(f"   ✅ Correctly identified unique title")
            print(f"      Title: '{unique_title}'")
        else:
            print(f"   ❌ Incorrectly flagged unique title as duplicate")
    
    # Test 3: Test JSON parsing
    print("\n3. Testing AI response parsing...")
    
    if openrouter:
        # Mock AI response
        mock_response = """```json
{
  "titles": [
    {
      "title": "10 Proven Strategies for Content Marketing Success",
      "keyword": "content marketing",
      "cluster": "marketing basics",
      "intent": "informational",
      "trend_refs": [0, 1]
    },
    {
      "title": "How to Create a Winning SEO Strategy in 2026",
      "keyword": "seo strategy",
      "cluster": "seo fundamentals",
      "intent": "how-to",
      "trend_refs": [2]
    }
  ]
}
```"""
        
        try:
            titles = service._parse_titles_response(mock_response)
            
            if len(titles) == 2:
                print(f"   ✅ Parsed {len(titles)} titles from AI response")
                print(f"      - {titles[0]['title']}")
                print(f"      - {titles[1]['title']}")
            else:
                print(f"   ❌ Expected 2 titles, got {len(titles)}")
                
        except Exception as e:
            print(f"   ❌ Failed to parse response: {e}")
    
    print("\n✅ EditorialPipelineService tests completed!")


def test_model_relationships():
    """Test that models can be queried correctly."""
    print("\n" + "="*60)
    print("TESTING MODEL RELATIONSHIPS")
    print("="*60)
    
    from apps.automation.models import (
        SiteProfile, EditorialPlan, EditorialPlanItem
    )
    
    # Test 1: Check SiteProfile query
    print("\n1. Testing SiteProfile queries...")
    profile_count = SiteProfile.objects.count()
    print(f"   ✅ Found {profile_count} site profiles in database")
    
    # Test 2: Check EditorialPlan query
    print("\n2. Testing EditorialPlan queries...")
    plan_count = EditorialPlan.objects.count()
    print(f"   ✅ Found {plan_count} editorial plans in database")
    
    # Test 3: Check EditorialPlanItem query
    print("\n3. Testing EditorialPlanItem queries...")
    item_count = EditorialPlanItem.objects.count()
    print(f"   ✅ Found {item_count} editorial plan items in database")
    
    # Test 4: Test relationships
    if plan_count > 0:
        print("\n4. Testing plan → items relationship...")
        plan = EditorialPlan.objects.first()
        items = plan.items.all()
        print(f"   ✅ Plan {plan.id} has {items.count()} items")
    
    print("\n✅ Model relationship tests completed!")


def main():
    """Run all Phase 3 tests."""
    print("\n" + "="*60)
    print("PHASE 3 VALIDATION TEST SUITE")
    print("="*60)
    
    try:
        test_site_profile_service()
    except Exception as e:
        print(f"\n❌ SiteProfileService tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_editorial_pipeline_service()
    except Exception as e:
        print(f"\n❌ EditorialPipelineService tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_model_relationships()
    except Exception as e:
        print(f"\n❌ Model relationship tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("PHASE 3 VALIDATION COMPLETE")
    print("="*60 + "\n")
    
    print("📝 NEXT STEPS:")
    print("1. Configure OpenRouter API key for full testing")
    print("2. Create a test project with WordPress URL")
    print("3. Run: python test_phase3.py")
    print("4. Check Django admin for created models")
    print()


if __name__ == '__main__':
    main()
