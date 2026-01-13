
import os
import django
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import sys
# Add project root to python path
sys.path.append(os.getcwd())

# Django setup removed (running via manage.py shell)

from apps.agencies.models import Agency, AgencyClientPlan
from apps.projects.models import Project, RSSFeed
from apps.automation.models import EditorialPlan, EditorialPlanItem, Post
from services.editorial_pipeline import EditorialPipelineService, PlanItemSchema

def test_phase2_logic():
    print("\n🚀 Starting Phase 2 Logic Test...\n")
    
    # 1. Setup Data
    agency = Agency.objects.first() or Agency.objects.create(name="Test Agency")
    
    # Create Plan 60
    client_plan, _ = AgencyClientPlan.objects.get_or_create(
        agency=agency,
        name="Plano 60 Teste",
        defaults={'posts_per_month': 60, 'price': 100}
    )
    
    project = Project.objects.create(
        agency=agency,
        name="Projeto Teste Phase 2",
        client_plan=client_plan,
        wordpress_url="https://example.com"
    )
    
    print(f"✅ Created Project with Plan: {client_plan.posts_per_month} posts/month")
    
    # =================================================================
    # TEST CASE 1: Calc Posts Per Day (No RSS)
    # =================================================================
    print("\n🧪 Test Case 1: Editorial Limits (No RSS)")
    
    # Logic simulation from webhooks/views.py
    posts_per_day = project.client_plan.posts_per_month // 30
    
    if posts_per_day != 2:
        print(f"❌ FAIL: Expected 2 posts/day, got {posts_per_day}")
    else:
        print(f"✅ PASS: Calculated {posts_per_day} posts/day correctly")
        
    # =================================================================
    # TEST CASE 2: Calc Posts Per Day (With RSS)
    # =================================================================
    print("\n🧪 Test Case 2: Editorial Limits (With RSS)")
    RSSFeed.objects.create(project=project, feed_url="http://test.com/rss", is_active=True)
    
    has_rss = RSSFeed.objects.filter(project=project, is_active=True).exists()
    
    posts_per_day_rss = 1 if has_rss else project.client_plan.posts_per_month // 30
    
    if posts_per_day_rss != 1:
        print(f"❌ FAIL: Expected 1 post/day with RSS, got {posts_per_day_rss}")
    else:
        print(f"✅ PASS: Calculated {posts_per_day_rss} post/day with RSS correctly")
        
    # =================================================================
    # TEST CASE 3: Item Generation & Schedule Time
    # =================================================================
    print("\n🧪 Test Case 3: Scheduling Logic")
    
    # Simulate Plan creation (using force 2 posts/day for test)
    plan = EditorialPlan.objects.create(
        project=project,
        keywords=['test'],
        start_date=date.today() + timedelta(days=1),
        posts_per_day=2,
        status='generating'
    )
    
    # Simulate Items (Day 1, Seq 0 and Seq 1)
    item1 = EditorialPlanItem.objects.create(
        plan=plan,
        day_index=1,
        title="Post Manhã",
        keyword_focus="test",
        scheduled_date=plan.start_date,
        external_id=f"{project.id}_{plan.id}_day_1_seq_0",
        status='pending'
    )
    
    item2 = EditorialPlanItem.objects.create(
        plan=plan,
        day_index=1,
        title="Post Tarde",
        keyword_focus="test",
        scheduled_date=plan.start_date,
        external_id=f"{project.id}_{plan.id}_day_1_seq_1",
        status='pending'
    )
    
    print(f"✅ Created Items: {item1.external_id} (ID: {item1.id}) and {item2.external_id} (ID: {item2.id})")
    
    # Debug: Check existence
    print(f"DEBUG: Checking item 1 in DB: {EditorialPlanItem.objects.filter(id=item1.id).exists()}")
    
    # Test Scheduling (Mocking tasks.py logic)
    from apps.automation.tasks import generate_post_from_plan_item
    
    # Mock run_full_pipeline and publish_to_wordpress to avoid external calls
    # run_full_pipeline is imported inside the function from apps.ai_engine.agents
    with patch('apps.ai_engine.agents.run_full_pipeline') as mock_pipeline, \
         patch('apps.automation.tasks.publish_to_wordpress') as mock_publish:
        
        # Run Task 1
        generate_post_from_plan_item(str(item1.id))
        post1 = Post.objects.get(external_id=item1.external_id)
        
        # Run Task 2
        generate_post_from_plan_item(str(item2.id))
        post2 = Post.objects.get(external_id=item2.external_id)
        
        # Verify Times
        hour1 = post1.scheduled_at.hour
        hour2 = post2.scheduled_at.hour
        
        print(f"  > Post 1 Scheduled Hour: {hour1}:00")
        print(f"  > Post 2 Scheduled Hour: {hour2}:00")
        
        if hour1 == 10 and hour2 == 16:
            print(f"✅ PASS: Scheduling logic correct (10h and 16h)")
            if post1.post_status == 'future':
                print(f"✅ PASS: Post status is 'future'")
        else:
            print(f"❌ FAIL: Expected 10 and 16, got {hour1} and {hour2}")
            
    # Cleanup
    project.delete()
    print("\n🧹 Cleanup completed")

if __name__ == "__main__":
    test_phase2_logic()
