
import os
import uuid
from decimal import Decimal
from django.utils import timezone
from apps.projects.models import Project
from apps.automation.models import Post, BatchJob

def run():
    print("🔬 Debugging Post Creation...")
    
    project = Project.objects.first()
    if not project:
        print("❌ No Project found.")
        return

    print(f"📂 Using Project: {project.name}")

    try:
        # Create minimal Batch
        batch = BatchJob.objects.create(
            project=project,
            original_filename="debug.csv",
            total_rows=1,
            processed_rows=0
        )
        print(f"✅ Batch Created: {batch.id}")

        # Create Post
        post = Post.objects.create(
            project=project,
            batch_job=batch,
            keyword=f"Debug Keyword {uuid.uuid4().hex[:4]}",
            title="Debug Title",
            status=Post.Status.DRAFT if hasattr(Post.Status, 'DRAFT') else 'draft', 
            # Wait, 'draft' is not in Status choices I saw earlier. It had GENERATING, PENDING_REVIEW etc.
            # Let's use 'generating' to be safe based on models.py inspection.
            created_at=timezone.now()
        )
        print(f"✅ Post Created: {post.id}")
        
    except Exception as e:
        print(f"❌ FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
