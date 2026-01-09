"""
Celery tasks for PostPro automation.
Handles batch processing, post regeneration, and WordPress publishing.
"""

import logging
import base64
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
    
    try:
        batch_job = BatchJob.objects.select_related(
            'project', 'project__agency'
        ).get(id=batch_job_id)
    except BatchJob.DoesNotExist:
        logger.error(f"BatchJob {batch_job_id} not found")
        return
    
    project = batch_job.project
    agency = project.agency
    
    # Check if dry run
    if batch_job.is_dry_run:
        return process_dry_run(batch_job)
    
    # Get API key
    api_key = agency.get_openrouter_key()
    if not api_key:
        batch_job.mark_failed("No OpenRouter API key configured")
        return
    
    # Mark as processing
    batch_job.status = BatchJob.Status.PROCESSING
    batch_job.save()
    
    # Read CSV/XLSX
    try:
        keywords = read_keywords_from_file(batch_job)
        batch_job.total_rows = len(keywords)
        batch_job.save()
    except Exception as e:
        batch_job.mark_failed(f"Failed to read file: {e}")
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
            
        except Exception as e:
            logger.error(f"Failed to process keyword '{keyword}': {e}")
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
        return []
    
    file_path = batch_job.csv_file.path
    
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'utf-8-sig']
        df = None
        error_msg = ""
        
        for encoding in encodings:
            try:
                # Use sniffing to find delimiter
                sep = ',' # Default
                try:
                    with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
                        # Read a sample. If file is small, read all.
                        sample = csvfile.read(2048)
                        if not sample: # Empty file
                            continue
                        sniffer = csv.Sniffer()
                        dialect = sniffer.sniff(sample, delimiters=[',', ';', '\t', '|'])
                        sep = dialect.delimiter
                except Exception:
                    # Fallback to comma if sniffing fails (e.g. single column)
                    sep = ','
                
                df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                logger.info(f"Successfully read CSV with encoding {encoding} and separator '{sep}'")
                break
            except Exception as e:
                error_msg = str(e)
                continue
        
        if df is None:
            raise ValueError(f"Could not read CSV file. Last error: {error_msg}")
    
    # Look for keyword column
    keyword_col = None
    target_cols = ['keyword', 'keywords', 'palavra-chave', 'palavra_chave', 'topic', 'tema', 'assunto']
    
    for col in df.columns:
        if str(col).lower().strip() in target_cols:
            keyword_col = col
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
