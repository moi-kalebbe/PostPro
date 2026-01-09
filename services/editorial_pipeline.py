"""
Editorial Pipeline Service.
Orchestrates the generation of editorial plans using AI agents.
"""

import logging
import json
from datetime import date, timedelta
from typing import Optional
from pydantic import BaseModel, Field

from django.utils import timezone
from django.db import transaction

from apps.projects.models import Project
from apps.automation.models import (
    EditorialPlan, 
    EditorialPlanItem, 
    TrendPack, 
    SiteProfile, 
    AIModelPolicy
)
from services.openrouter import OpenRouterService
from services.perplexity import PerplexityTrendsService
from services.site_profile import SiteProfileService

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Schemas
# ============================================================================

class PlanItemSchema(BaseModel):
    """Schema for a single day's content plan."""
    day: int = Field(..., ge=1, le=30, description="Day number in the plan (1-30)")
    title: str = Field(..., description="Optimized blog post title")
    keyword_focus: str = Field(..., description="Primary keyword to target")
    search_intent: str = Field(..., description="informational, commercial, or navigational")
    cluster: str = Field(..., description="Topic cluster or category name")
    rationale: str = Field(..., description="Why this topic was chosen")

class EditorialPlanSchema(BaseModel):
    """Schema for the full editorial plan."""
    items: list[PlanItemSchema] = Field(..., min_length=5, description="List of plan items")


# ============================================================================
# Service Class
# ============================================================================

class EditorialPipelineService:
    """
    Service to generate editorial plans using AI agents.
    """
    
    def __init__(self, project: Project, openrouter_service: OpenRouterService):
        self.project = project
        self.openrouter = openrouter_service
        self.perplexity = PerplexityTrendsService(openrouter_service)
        self.site_profile_service = SiteProfileService(project)
        
        # Load policy
        self.policy = AIModelPolicy.objects.filter(
            agency=project.agency, 
            is_active=True
        ).first()
        
        # Default models if policy missing
        self.trends_model = self.policy.planning_trends_model if self.policy else 'perplexity/sonar'
        self.planning_model = self.policy.planning_titles_model if self.policy else 'anthropic/claude-3.5-sonnet'
    
    def create_editorial_plan(
        self,
        keywords: list[str],
        start_date: date,
        posts_per_day: int = 1,
        use_trends: bool = True,
        days_to_plan: int = 30
    ) -> EditorialPlan:
        """
        Create a new editorial plan.
        """
        # 1. Create Plan Record
        plan = EditorialPlan.objects.create(
            project=self.project,
            keywords=keywords,
            start_date=start_date,
            posts_per_day=posts_per_day,
            status=EditorialPlan.Status.GENERATING
        )
        
        try:
            # 2. Sync Site Profile (for context/cannibalization)
            site_profile = self.site_profile_service.sync_profile()
            plan.site_profile = site_profile
            plan.save()
            
            # 3. Generate Trends (if requested)
            trend_pack = None
            if use_trends:
                trend_pack = self._generate_trends(keywords)
                plan.trend_pack = trend_pack
                plan.save()
            
            # 4. Generate Plan Items
            self._generate_plan_items(plan, trend_pack, days_to_plan)
            
            # 5. Finalize
            plan.status = EditorialPlan.Status.PENDING_APPROVAL
            plan.save()
            
            logger.info(f"Editorial plan {plan.id} created with {plan.items.count()} items")
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create editorial plan {plan.id}: {str(e)}")
            plan.status = EditorialPlan.Status.REJECTED
            plan.rejection_reason = f"Generation failed: {str(e)}"
            plan.save()
            raise
    
    def _generate_trends(self, keywords: list[str]) -> TrendPack:
        """Generate or reuse trend pack."""
        # Reuse existing recent pack if available
        existing_pack = TrendPack.objects.filter(
            agency=self.project.agency,
            keywords=keywords,
            created_at__gte=timezone.now() - timedelta(days=3)
        ).first()
        
        if existing_pack:
            return existing_pack
            
        # Generate new pack
        data = self.perplexity.generate_trend_pack(
            keywords=keywords,
            model=self.trends_model,
            recency_days=self.policy.trends_recency_days if self.policy else 7
        )
        
        # Save pack
        pack = TrendPack.objects.create(
            agency=self.project.agency,
            keywords=keywords,
            model_used=self.trends_model,
            insights=data['insights'],
            tokens_used=data['tokens_used'],
            cost=data['cost'],
            expires_at=timezone.now() + timedelta(days=7)
        )
        return pack
    
    def _generate_plan_items(
        self, 
        plan: EditorialPlan, 
        trend_pack: Optional[TrendPack],
        days: int,
        avoid_topics: list = None
    ):
        """Generate title ideas and create PlanItems."""
        
        # Prepare context
        profile = plan.site_profile
        existing_titles = [p['title'] for p in profile.recent_posts] if profile else []
        
        trends_context = ""
        if trend_pack:
            insights = sorted(trend_pack.insights, key=lambda x: x.get('relevance_score', 0), reverse=True)[:10]
            trends_context = "Incorporate these current trends:\n" + "\n".join(
                [f"- {i['title']}: {i['summary']}" for i in insights]
            )
        
        keywords_str = ", ".join(plan.keywords)
        
        # Build avoid topics list (existing + rejected)
        all_avoid = list(existing_titles[:20])
        if avoid_topics:
            all_avoid.extend(avoid_topics)
        
        avoid_section = ""
        if all_avoid:
            avoid_section = f"""
AVOID these topics (already exist or rejected):
{json.dumps(all_avoid[:50], ensure_ascii=False)}
"""
        
        prompt = f"""Create a {days}-day editorial calendar for a blog about: {keywords_str}.
        
Site Context:
Name: {profile.site_name if profile else 'Blog'}
Existing Content Themes: {', '.join([c['name'] for c in profile.categories]) if profile else 'General'}
Tone: {self.project.tone}

{trends_context}
{avoid_section}

Requirements:
1. Generate exactly 1 post idea per day for {days} days.
2. Ensure a mix of informational (guides, how-to) and commercial (reviews, comparisons) intent.
3. Group topics into logical clusters.
4. Titles must be click-worthy and SEO optimized.
5. Use Portuguese (Brazil).
6. NEVER repeat topics from the AVOID list above.

Return ONLY valid JSON matching the schema."""
        
        # Call LLM
        messages = [{"role": "user", "content": prompt}]
        
        try:
            parsed, result = self.openrouter.generate_with_schema(
                messages,
                EditorialPlanSchema,
                model=self.planning_model
            )
            
            # Save items
            items_to_create = []
            for item in parsed.items:
                # Basic anti-cannibalization check (fuzzy match skip)
                if any(item.title.lower() in et.lower() for et in existing_titles):
                    continue
                
                # Calculate date
                sched_date = plan.start_date + timedelta(days=item.day - 1)
                
                # Generate stable external_id
                # Format: {project_id}_{plan_id}_day_{day}
                ext_id = f"{self.project.id}_{plan.id}_day_{item.day}"
                
                items_to_create.append(EditorialPlanItem(
                    plan=plan,
                    day_index=item.day,
                    title=item.title,
                    keyword_focus=item.keyword_focus,
                    cluster=item.cluster,
                    search_intent=item.search_intent,
                    scheduled_date=sched_date,
                    external_id=ext_id,
                    status=EditorialPlanItem.Status.PENDING
                ))
            
            # Bulk create
            with transaction.atomic():
                EditorialPlanItem.objects.bulk_create(items_to_create)
                
        except Exception as e:
            logger.error(f"Error generation plan items: {e}")
            raise
