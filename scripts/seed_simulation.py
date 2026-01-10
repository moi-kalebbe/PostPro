
import os
import sys
import django
import random
import uuid
from datetime import timedelta
from decimal import Decimal

# Setup Django if run directly
if __name__ == "__main__":
    # Add project root to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from django.utils import timezone
from apps.agencies.models import Agency
from apps.projects.models import Project, ProjectContentSettings
from apps.automation.models import Post, BatchJob

def log(msg):
    # Log to both console and file
    print(msg)
    with open('seeding.log', 'a', encoding='utf-8') as f:
        f.write(msg + "\n")

def run():
    open('seeding.log', 'w').close() # Clear log
    log("🚀 Starting Data Simulation...")

    agency = Agency.objects.first()
    if not agency:
        log("❌ No agency found.")
        # Create one
        try:
             agency = Agency.objects.create(name="Demo Agency", slug="demo-agency")
             log("✅ Created Demo Agency")
        except Exception as e:
             log(f"Critcal fail creation agency: {e}")
             return
    
    log(f"🏢 Using Agency: {agency.name}")

    projects_data = [
        {"name": "Tech Daily News", "niche": "Technology", "status": True},
        {"name": "Healthy Living Pro", "niche": "Health", "status": True},
        {"name": "Crypto Signals VIP", "niche": "Finance", "status": False},
        {"name": "Global Travel Guide", "niche": "Travel", "status": True},
        {"name": "Pet Lovers Blog", "niche": "Pets", "status": True},
    ]

    created_projects = []
    for p_data in projects_data:
        try:
            project, created = Project.objects.get_or_create(
                name=p_data["name"],
                defaults={
                    "agency": agency,
                    "wordpress_url": f"https://{p_data['name'].lower().replace(' ', '')}.com",
                    "wordpress_username": "admin",
                    "is_active": p_data["status"],
                    "text_model": "anthropic/claude-3.5-sonnet",
                    "image_model": "pollinations/flux",
                    "tone": "professional"
                }
            )
            # Ensure Settings
            if not hasattr(project, 'content_settings'):
                ProjectContentSettings.objects.create(project=project)
            
            created_projects.append(project)
            log(f"✅ Project managed: {project.name}")
        except Exception as e:
            log(f"❌ Error project {p_data['name']}: {e}")

    log("\n📦 Generating Jobs and Posts...")
    
    # Valid Statuses from model
    # GENERATING, PENDING_REVIEW, APPROVED, PUBLISHED, FAILED
    statuses = [
        ('published', 0.4),
        ('approved', 0.2),
        ('pending_review', 0.2),
        ('generating', 0.1),
        ('failed', 0.1)
    ]

    total_posts_created = 0
    
    for project in created_projects:
        for i in range(random.randint(2, 4)):
            try:
                batch = BatchJob.objects.create(
                    project=project,
                    original_filename=f"keywords_import_{i}.csv",
                    status='completed', # BatchJob.Status.COMPLETED
                    total_rows=random.randint(5, 15),
                    processed_rows=0, # Will update
                    estimated_cost=Decimal(random.uniform(0.5, 2.0))
                )
                
                rows_count = batch.total_rows
                
                for j in range(rows_count):
                    # Pick status
                    r = random.random()
                    cumulative = 0
                    chosen_status = 'published'
                    for status, weight in statuses:
                        cumulative += weight
                        if r <= cumulative:
                            chosen_status = status
                            break
                    
                    # Date
                    days_ago = random.randint(0, 30)
                    date = timezone.now() - timedelta(days=days_ago)

                    # Costs
                    txt_cost = Decimal(random.uniform(0.005, 0.05))
                    img_cost = Decimal(random.uniform(0.02, 0.08))
                    
                    post = Post.objects.create(
                        project=project,
                        batch_job=batch,
                        keyword=f"How to {project.name.split()[0]} {uuid.uuid4().hex[:4]}",
                        content=f"<p>Simulated content for {project.name}...</p>",
                        title=f"The Ultimate Guide to {project.name} Topic {j}",
                        status=chosen_status,
                        post_status='publish',
                        text_generation_cost=txt_cost,
                        image_generation_cost=img_cost,
                        total_cost=txt_cost + img_cost,
                        tokens_total=random.randint(800, 3000),
                    published_at=date if chosen_status == 'published' else None
                    )
                    # Hack date
                    Post.objects.filter(id=post.id).update(created_at=date)
                    total_posts_created += 1

                    # Generate Artifacts for Step Breakdown
                    from apps.automation.models import PostArtifact
                    
                    # 1. Research
                    PostArtifact.objects.create(
                        post=post,
                        step='research',
                        parsed_output={"data": "Simulated Research"},
                        cost=txt_cost * Decimal('0.1'),
                        tokens_used=100,
                        created_at=date
                    )
                    # 2. Strategy
                    PostArtifact.objects.create(
                        post=post,
                        step='strategy',
                        parsed_output={"plan": "Simulated Strategy"},
                        cost=txt_cost * Decimal('0.1'),
                        tokens_used=100,
                        created_at=date
                    )
                    # 3. Article (Main Request)
                    PostArtifact.objects.create(
                        post=post,
                        step='article',
                        parsed_output={"html": post.content},
                        cost=txt_cost * Decimal('0.8'),
                        tokens_used=int(post.tokens_total * 0.8),
                        created_at=date
                    )
                    # 4. Image
                    PostArtifact.objects.create(
                        post=post,
                        step='image',
                        parsed_output={"url": "http://example.com/image.jpg"},
                        cost=img_cost,
                        tokens_used=0,
                        created_at=date
                    )

                
                # Update batch
                batch.processed_rows = rows_count
                batch.save()
                log(f"   Batch {batch.id} created with {rows_count} posts")

            except Exception as e:
                log(f"❌ Error Batch/Post: {e}")

    log(f"📝 Created {total_posts_created} posts total.")
    
    # Update Agency
    count = Post.objects.filter(project__agency=agency).count()
    agency.current_month_posts = count
    agency.save()
    log("✅ Simulation Complete!")

if __name__ == "__main__":
    run()
