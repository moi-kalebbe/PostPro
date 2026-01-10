"""
Celery tasks for PostPro automation.
Handles batch processing, post regeneration, and WordPress publishing.
"""

import logging
import base64
import os
import pandas as pd
from io import BytesIO
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_csv_batch(self, batch_job_id: str):
    """
    Process a CSV/XLSX batch file and generate posts.
    
    Args:
        batch_job_id: UUID of the BatchJob
    """
    from apps.automation.models import BatchJob, Post
    from apps.ai_engine.agents import run_full_pipeline
    from services.openrouter import OpenRouterService
    from services.cost_estimator import CostEstimator
    
    logger.info(f"Starting CSV batch processing for job {batch_job_id}")
    
    try:
        batch_job = BatchJob.objects.select_related(
            'project', 'project__agency'
        ).get(id=batch_job_id)
    except BatchJob.DoesNotExist:
        logger.error(f"BatchJob {batch_job_id} not found")
        return
    
    project = batch_job.project
    agency = project.agency
    
    logger.info(f"Processing batch for project: {project.name}, file: {batch_job.original_filename}")
    
    # Check if dry run
    if batch_job.is_dry_run:
        logger.info("Dry run mode enabled")
        return process_dry_run(batch_job)
    
    # Get API key
    api_key = agency.get_openrouter_key()
    if not api_key:
        logger.error("No OpenRouter API key configured")
        batch_job.mark_failed("No OpenRouter API key configured")
        return
    
    # Mark as processing
    batch_job.status = BatchJob.Status.PROCESSING
    batch_job.save()
    
    # Read CSV/XLSX
    try:
        logger.info(f"Attempting to read keywords from file: {batch_job.csv_file}")
        keywords = read_keywords_from_file(batch_job)
        logger.info(f"Successfully read {len(keywords)} keywords: {keywords[:5]}...")
        batch_job.total_rows = len(keywords)
        batch_job.save()
    except Exception as e:
        error_msg = f"Failed to read file: {e}"
        logger.error(error_msg)
        logger.exception("Full traceback:")
        batch_job.mark_failed(error_msg)
        return
    
    # Options
    options = batch_job.options or {}
    generate_images = options.get("generate_images", True)
    auto_publish = options.get("auto_publish", False)
    
    # Initialize OpenRouter
    openrouter = OpenRouterService(
        api_key=api_key,
        site_url=settings.SITE_URL,
        site_name="PostPro"
    )
    
    # Process each keyword
    errors = []
    for i, keyword in enumerate(keywords):
        try:
            logger.info(f"Processing keyword {i+1}/{len(keywords)}: {keyword}")
            
            # Create post
            post = Post.objects.create(
                batch_job=batch_job,
                project=project,
                keyword=keyword.strip(),
                status=Post.Status.GENERATING,
            )
            
            # Run pipeline
            run_full_pipeline(
                post=post,
                openrouter=openrouter,
                generate_image=generate_images,
            )
            
            # Upload image to Supabase if generated
            if generate_images and post.step_state.get("image") == "completed":
                upload_image_to_supabase(post)
            
            # Auto-publish if enabled
            if auto_publish:
                publish_to_wordpress.delay(str(post.id))
            
            # Update progress
            batch_job.processed_rows = i + 1
            batch_job.save()
            
            # Update agency monthly counter
            agency.current_month_posts += 1
            agency.save(update_fields=['current_month_posts'])
            
            logger.info(f"Successfully processed keyword: {keyword}")
            
        except Exception as e:
            logger.error(f"Failed to process keyword '{keyword}': {e}")
            logger.exception("Full traceback:")
            errors.append({
                "keyword": keyword,
                "error": str(e),
                "row": i + 1,
            })
    
    # Complete batch
    if errors:
        batch_job.error_log = {"errors": errors}
    
    batch_job.mark_completed()
    
    logger.info(f"Batch {batch_job_id} completed: {batch_job.processed_rows}/{batch_job.total_rows}")


def process_dry_run(batch_job):
    """
    Process a dry-run simulation without calling APIs.
    """
    from services.cost_estimator import CostEstimator
    
    project = batch_job.project
    options = batch_job.options or {}
    
    # Read keywords
    try:
        keywords = read_keywords_from_file(batch_job)
    except Exception as e:
        batch_job.mark_failed(f"Failed to read file: {e}")
        return
    
    # Estimate costs
    estimator = CostEstimator(
        text_model=project.get_text_model(),
        image_model=project.get_image_model(),
        tone=project.tone,
    )
    
    result = estimator.estimate_batch(
        keyword_count=len(keywords),
        generate_images=options.get("generate_images", True),
    )
    
    # Store simulation report
    batch_job.total_rows = len(keywords)
    batch_job.processed_rows = len(keywords)
    batch_job.estimated_cost = result.total_cost
    batch_job.error_log = {
        "simulation_report": {
            "total_posts": result.total_posts,
            "research_tokens": result.research_tokens,
            "strategy_tokens": result.strategy_tokens,
            "article_tokens": result.article_tokens,
            "total_tokens": result.total_tokens,
            "text_cost": str(result.text_cost),
            "image_count": result.image_count,
            "image_cost": str(result.image_cost),
            "total_cost": str(result.total_cost),
        },
        "keywords": keywords,
    }
    
    batch_job.mark_completed()
    logger.info(f"Dry-run completed for batch {batch_job.id}: estimated ${result.total_cost}")


def read_keywords_from_file(batch_job) -> list[str]:
    """
    Read keywords from CSV or XLSX file with robust encoding and delimiter detection.
    """
    import csv
    
    if not batch_job.csv_file:
        logger.error("No CSV file attached to batch job")
        raise ValueError("No CSV file attached to batch job")
    
    file_path = batch_job.csv_file.path
    logger.info(f"Reading keywords from file path: {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        # Try to read directly from the file field if it's stored differently
        try:
            content = batch_job.csv_file.read().decode('utf-8')
            logger.info(f"Read file content directly from field, length: {len(content)}")
            batch_job.csv_file.seek(0)  # Reset file pointer
            # Parse as CSV from string
            from io import StringIO
            df = pd.read_csv(StringIO(content))
        except Exception as e:
            logger.error(f"Failed to read file content directly: {e}")
            raise FileNotFoundError(f"CSV file not found at path: {file_path}")
    elif file_path.endswith('.xlsx'):
        logger.info("Reading as XLSX file")
        df = pd.read_excel(file_path)
    else:
        logger.info("Reading as CSV file")
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'utf-8-sig']
        df = None
        error_msg = ""
        
        for encoding in encodings:
            try:
                # Use sniffing to find delimiter
                sep = ','  # Default
                try:
                    with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
                        # Read a sample. If file is small, read all.
                        sample = csvfile.read(2048)
                        if not sample:  # Empty file
                            logger.warning(f"Empty file with encoding {encoding}")
                            continue
                        logger.info(f"File sample with {encoding}: {sample[:100]}...")
                        sniffer = csv.Sniffer()
                        try:
                            dialect = sniffer.sniff(sample, delimiters=[',', ';', '\t', '|'])
                            sep = dialect.delimiter
                        except csv.Error:
                            # Single column CSV won't have delimiter to detect
                            sep = ','
                            logger.info("Could not sniff delimiter, using comma as default")
                except Exception as sniff_error:
                    # Fallback to comma if sniffing fails (e.g. single column)
                    logger.info(f"Sniffing failed: {sniff_error}, using comma")
                    sep = ','
                
                df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                logger.info(f"Successfully read CSV with encoding {encoding} and separator '{sep}'")
                logger.info(f"DataFrame shape: {df.shape}, columns: {list(df.columns)}")
                break
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Failed with encoding {encoding}: {e}")
                continue
        
        if df is None:
            raise ValueError(f"Could not read CSV file. Last error: {error_msg}")
    
    # Look for keyword column
    keyword_col = None
    target_cols = ['keyword', 'keywords', 'palavra-chave', 'palavra_chave', 'topic', 'tema', 'assunto']
    
    logger.info(f"Looking for keyword column in: {list(df.columns)}")
    
    for col in df.columns:
        if str(col).lower().strip() in target_cols:
            keyword_col = col
            logger.info(f"Found keyword column: {keyword_col}")
            break
    
    if keyword_col is None:
        # Use first column if it looks like text
        keyword_col = df.columns[0]
        logger.warning(f"No keyword column found. Using first column: {keyword_col}")
        
        # If we fell back to the first column (likely because of missing header), 
        # include the header itself as it might be a keyword.
        keywords = [str(keyword_col)] + df[keyword_col].dropna().astype(str).tolist()
    else:
        keywords = df[keyword_col].dropna().astype(str).tolist()
    
    # Clean and filter
    keywords = [k.strip() for k in keywords if k.strip()]
    
    logger.info(f"Extracted {len(keywords)} keywords: {keywords}")
    
    if not keywords:
        raise ValueError("No valid keywords found in file")
        
    return keywords


def upload_image_to_supabase(post):
    """Upload featured image to Supabase Storage."""
    from supabase import create_client
    
    # Get the image artifact
    artifact = post.artifacts.filter(
        step='image',
        is_active=True
    ).first()
    
    if not artifact:
        return
    
    # We don't store the full base64 in artifact, need to regenerate
    # For now, skip - in production, store temp file or pass directly
    # This is a placeholder for the actual implementation
    logger.info(f"Image upload placeholder for post {post.id}")


@shared_task(bind=True, max_retries=2)
def regenerate_post_step(self, post_id: str, step: str, preserve_downstream: bool = False):
    """
    Regenerate a single step of a post.
    
    Args:
        post_id: UUID of the Post
        step: Step to regenerate ('research', 'strategy', 'article', 'image')
        preserve_downstream: If False, invalidate downstream steps
    """
    from apps.automation.models import Post
    from apps.ai_engine.agents import ResearchAgent, StrategyAgent, ArticleAgent, ImageAgent
    from services.openrouter import OpenRouterService
    
    try:
        post = Post.objects.select_related(
            'project', 'project__agency'
        ).get(id=post_id)
    except Post.DoesNotExist:
        logger.error(f"Post {post_id} not found")
        return
    
    agency = post.project.agency
    api_key = agency.get_openrouter_key()
    
    if not api_key:
        logger.error(f"No API key for post {post_id}")
        return
    
    openrouter = OpenRouterService(
        api_key=api_key,
        site_url=settings.SITE_URL,
        site_name="PostPro"
    )
    
    try:
        if step == 'research':
            agent = ResearchAgent(openrouter, post)
            research_data = agent.run()
            
            if not preserve_downstream:
                # Invalidate downstream
                post.step_state['strategy'] = 'pending'
                post.step_state['article'] = 'pending'
                post.save()
        
        elif step == 'strategy':
            agent = StrategyAgent(openrouter, post)
            agent.run(post.research_data)
            
            if not preserve_downstream:
                post.step_state['article'] = 'pending'
                post.save()
        
        elif step == 'article':
            agent = ArticleAgent(openrouter, post)
            agent.run(post.research_data, post.strategy_data)
        
        elif step == 'image':
            agent = ImageAgent(openrouter, post)
            agent.run(post.title)
            upload_image_to_supabase(post)
        
        # Recalculate costs
        post.update_total_cost()
        
        logger.info(f"Regenerated {step} for post {post_id}")
        
    except Exception as e:
        logger.error(f"Failed to regenerate {step} for post {post_id}: {e}")
        raise


@shared_task(bind=True, max_retries=3)
def publish_to_wordpress(self, post_id: str):
    """
    Publish a post to WordPress with idempotency.
    
    Args:
        post_id: UUID of the Post
    """
    from apps.automation.models import Post, ActivityLog
    from services.wordpress import send_to_postpro_plugin
    from services.idempotency import IdempotencyGuard
    
    try:
        post = Post.objects.select_related('project').get(id=post_id)
    except Post.DoesNotExist:
        logger.error(f"Post {post_id} not found")
        return
    
    # Check if already published
    if post.status == Post.Status.PUBLISHED and post.wordpress_post_id:
        logger.info(f"Post {post_id} already published as WP#{post.wordpress_post_id}")
        return {"already_published": True, "post_id": post.wordpress_post_id}
    
    project = post.project
    
    # Generate idempotency key
    idempotency_key = post.generate_wordpress_idempotency_key()
    post.save()
    
    # Use idempotency guard
    with IdempotencyGuard(
        'wordpress_publish',
        project.id,
        post.id,
        'v1',
        post_id=post.id
    ) as guard:
        
        if guard.already_completed:
            # Already published, get result
            wp_post_id = guard.metadata.get('wordpress_post_id')
            if wp_post_id:
                post.mark_published(wp_post_id, guard.metadata.get('edit_url', ''))
            return guard.metadata
        
        # Send to WordPress plugin
        result = send_to_postpro_plugin(
            site_url=project.wordpress_url,
            license_key=str(project.license_key),
            post_data={
                "title": post.title,
                "content": post.content,
                "meta_description": post.meta_description,
                "featured_image_url": post.featured_image_url,
                "postpro_post_id": str(post.id),
            },
            idempotency_key=idempotency_key,
        )
        
        if result.get("success"):
            wp_post_id = result.get("post_id")
            edit_url = result.get("edit_url", "")
            
            post.mark_published(wp_post_id, edit_url)
            
            # Log activity
            ActivityLog.objects.create(
                agency=project.agency,
                project=project,
                action="WP_PUBLISHED",
                entity_type="Post",
                entity_id=str(post.id),
                metadata={
                    "wordpress_post_id": wp_post_id,
                    "keyword": post.keyword,
                }
            )
            
            guard.complete({
                "wordpress_post_id": wp_post_id,
                "edit_url": edit_url,
            })
            
            logger.info(f"Published post {post_id} as WP#{wp_post_id}")
            return result
        
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Failed to publish post {post_id}: {error}")
            raise Exception(error)
@shared_task(bind=True, max_retries=3)
def generate_editorial_plan(self, plan_id: str, avoid_topics: list = None):
    """
    Generate titles for an editorial plan using AI.
    
    Args:
        plan_id: UUID of the EditorialPlan
        avoid_topics: List of topic titles to avoid (from rejected plans)
    """
    from apps.automation.models import EditorialPlan
    from services.editorial_pipeline import EditorialPipelineService
    from services.openrouter import OpenRouterService
    from services.site_profile import SiteProfileService
    
    logger.info(f"Generating editorial plan {plan_id}")
    if avoid_topics:
        logger.info(f"Avoiding {len(avoid_topics)} previously rejected topics")
    
    try:
        plan = EditorialPlan.objects.select_related(
            'project', 'project__agency'
        ).get(id=plan_id)
    except EditorialPlan.DoesNotExist:
        logger.error(f"EditorialPlan {plan_id} not found")
        return
    
    project = plan.project
    agency = project.agency
    
    # Get OpenRouter API key
    api_key = agency.get_openrouter_key()
    if not api_key:
        logger.error(f"No OpenRouter API key for agency {agency.name}")
        plan.status = EditorialPlan.Status.REJECTED
        plan.save()
        return
    
    try:
        # Initialize services
        openrouter = OpenRouterService(api_key)
        pipeline = EditorialPipelineService(project, openrouter)
        
        # Ensure site profile exists
        if not plan.site_profile:
             site_profile_service = SiteProfileService(project)
             plan.site_profile = site_profile_service.get_or_create_profile()
             plan.save()
        
        # Generate items (and trends if needed)
        # Pass avoid_topics to pipeline for history-aware generation
        pipeline._generate_plan_items(plan, plan.trend_pack, days=30, avoid_topics=avoid_topics or [])
        
        # Update status
        plan.status = EditorialPlan.Status.PENDING_APPROVAL
        plan.save()
        
        logger.info(f"Editorial plan {plan_id} generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating editorial plan {plan_id}: {e}")
        plan.status = EditorialPlan.Status.FAILED
        plan.save()
        raise


@shared_task(bind=True, max_retries=3)
def process_scheduled_posts():
    """
    Process scheduled editorial plan items that are due today.
    Creates posts for items with scheduled_date = today.
    """
    from apps.automation.models import EditorialPlanItem
    from datetime import date
    
    logger.info("Processing scheduled editorial plan items")
    
    # Get items scheduled for today
    today = date.today()
    items = EditorialPlanItem.objects.filter(
        scheduled_date=today,
        status=EditorialPlanItem.Status.SCHEDULED,
        post__isnull=True
    ).select_related('plan', 'plan__project', 'plan__project__agency')
    
    logger.info(f"Found {items.count()} items to process")
    
    for item in items:
        try:
            # Create post from editorial plan item
            generate_post_from_plan_item.delay(str(item.id))
            
            # Update item status
            item.status = EditorialPlanItem.Status.GENERATING
            item.save()
            
        except Exception as e:
            logger.error(f"Error scheduling post for item {item.id}: {e}")


@shared_task(bind=True, max_retries=3)
def generate_post_from_plan_item(self, item_id: str):
    """
    Generate a full post from an editorial plan item.
    
    Args:
        item_id: UUID of the EditorialPlanItem
    """
    from apps.automation.models import EditorialPlanItem, Post
    from apps.ai_engine.agents import run_full_pipeline
    from services.openrouter import OpenRouterService
    
    logger.info(f"Generating post from plan item {item_id}")
    
    try:
        item = EditorialPlanItem.objects.select_related(
            'plan', 'plan__project', 'plan__project__agency'
        ).get(id=item_id)
    except EditorialPlanItem.DoesNotExist:
        logger.error(f"EditorialPlanItem {item_id} not found")
        return
    
    project = item.plan.project
    agency = project.agency
    
    # Get OpenRouter API key
    api_key = agency.get_openrouter_key()
    if not api_key:
        logger.error(f"No OpenRouter API key for agency {agency.name}")
        item.status = EditorialPlanItem.Status.FAILED
        item.save()
        return
    
    try:
        # Create Post instance
        post = Post.objects.create(
            project=project,
            keyword=item.keyword_focus,
            title=item.title,
            external_id=item.external_id,
            status=Post.Status.GENERATING,
            post_status='future',
            scheduled_at=item.scheduled_date
        )
        
        # Link to plan item
        item.post = post
        item.save()
        
        logger.info(f"Created post {post.id} for item {item.id}")
        
        # Run full AI pipeline
        openrouter = OpenRouterService(api_key)
        
        # run_full_pipeline populates the post object directly
        run_full_pipeline(
            post=post,
            openrouter=openrouter,
            generate_image=True,
        )
        
        # Post is already populated by the pipeline
        # Add SEO data from editorial plan item
        post.seo_data = {
            'keyword': item.keyword_focus,
            'seo_title': post.title,
            'seo_description': post.meta_description,
            'cluster': item.cluster,
            'search_intent': item.search_intent
        }
        
        post.status = Post.Status.APPROVED
        post.save()
        
        # Update item status
        item.status = EditorialPlanItem.Status.COMPLETED
        item.save()
        
        logger.info(f"Post {post.id} generated successfully")
        
        # Import and call publish task
        from apps.automation.tasks import publish_to_wordpress
        publish_to_wordpress.delay(str(post.id))
        
    except Exception as e:
        logger.error(f"Error generating post from item {item_id}: {e}")
        item.status = EditorialPlanItem.Status.FAILED
        item.save()
        raise


@shared_task(bind=True, max_retries=3)
def sync_site_profile(self, project_id: str):
    """
    Sync WordPress site profile for a project.
    
    Args:
        project_id: UUID of the Project
    """
    from apps.projects.models import Project
    from services.site_profile import SiteProfileService
    
    logger.info(f"Syncing site profile for project {project_id}")
    
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error(f"Project {project_id} not found")
        return
    
    try:
        service = SiteProfileService(project)
        profile = service.sync_profile()
        
        logger.info(f"Site profile synced for {project.name}: {profile.site_name}")
        
    except Exception as e:
        logger.error(f"Error syncing site profile for project {project_id}: {e}")
        raise
