"""
Editorial Pipeline Service for PostPro.
Orchestrates editorial plan generation with AI-powered title creation and anti-cannibalization.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

from apps.automation.models import (
    EditorialPlan, EditorialPlanItem, TrendPack, SiteProfile
)
from apps.projects.models import Project
from services.openrouter import OpenRouterService
from services.perplexity import PerplexityTrendsService
from services.site_profile import SiteProfileService

logger = logging.getLogger(__name__)


class EditorialPipelineService:
    """
    Generate and manage editorial plans with AI-powered content strategy.
    """
    
    def __init__(self, project: Project, openrouter_service: OpenRouterService):
        self.project = project
        self.agency = project.agency
        self.openrouter = openrouter_service
        self.perplexity = PerplexityTrendsService(openrouter_service)
    
    def create_editorial_plan(
        self,
        keywords: list[str],
        start_date: datetime.date,
        posts_per_day: int = 1,
        use_trends: bool = True,
        recency_days: int = 7
    ) -> EditorialPlan:
        """
        Create a new 30-day editorial plan.
        
        Args:
            keywords: 5-10 seed keywords
            start_date: When to start publishing
            posts_per_day: Number of posts per day (default: 1)
            use_trends: Whether to use Perplexity trends
            recency_days: Trend recency window (7 or 30 days)
        
        Returns:
            EditorialPlan instance (status: GENERATING)
        """
        logger.info(f"Creating editorial plan for {self.project.name} with {len(keywords)} keywords")
        
        # Get or create site profile
        site_profile_service = SiteProfileService(self.project)
        site_profile = site_profile_service.get_or_create_profile()
        
        # Create plan
        plan = EditorialPlan.objects.create(
            project=self.project,
            site_profile=site_profile,
            keywords=keywords,
            start_date=start_date,
            posts_per_day=posts_per_day,
            status=EditorialPlan.Status.GENERATING
        )
        
        logger.info(f"Created plan {plan.id}")
        
        # Generate trend pack if requested
        if use_trends:
            try:
                trend_pack = self._generate_trend_pack(keywords, recency_days)
                plan.trend_pack = trend_pack
                plan.save()
            except Exception as e:
                logger.error(f"Failed to generate trend pack: {e}")
                # Continue without trends
        
        # Generate 30 titles
        self._generate_titles(plan, site_profile)
        
        # Update status
        plan.status = EditorialPlan.Status.PENDING_APPROVAL
        plan.save()
        
        logger.info(f"Plan {plan.id} ready for approval")
        
        return plan
    
    def _generate_trend_pack(self, keywords: list[str], recency_days: int) -> TrendPack:
        """
        Generate trend pack using Perplexity Sonar.
        
        Args:
            keywords: Seed keywords
            recency_days: Recency window
        
        Returns:
            TrendPack instance
        """
        logger.info(f"Generating trend pack for {len(keywords)} keywords")
        
        # Get model from agency policy
        model_policy = self.agency.model_policies.filter(is_active=True).first()
        trends_model = model_policy.planning_trends_model if model_policy else 'perplexity/sonar'
        
        # Generate trends
        result = self.perplexity.generate_trend_pack(
            keywords=keywords,
            model=trends_model,
            recency_days=recency_days,
            max_insights=20
        )
        
        # Create TrendPack
        trend_pack = TrendPack.objects.create(
            agency=self.agency,
            keywords=keywords,
            recency_days=recency_days,
            model_used=trends_model,
            insights=result['insights'],
            tokens_used=result['tokens_used'],
            cost=result['cost'],
            expires_at=datetime.now() + timedelta(days=7)
        )
        
        logger.info(f"Created trend pack {trend_pack.id} with {len(result['insights'])} insights")
        
        return trend_pack
    
    def _generate_titles(self, plan: EditorialPlan, site_profile: SiteProfile) -> None:
        """
        Generate 30 titles for the editorial plan.
        
        Args:
            plan: EditorialPlan instance
            site_profile: SiteProfile for anti-cannibalization
        """
        logger.info(f"Generating 30 titles for plan {plan.id}")
        
        # Get existing titles for anti-cannibalization
        existing_titles = [post['title'] for post in site_profile.recent_posts]
        
        # Get model from agency policy
        model_policy = self.agency.model_policies.filter(is_active=True).first()
        titles_model = model_policy.planning_titles_model if model_policy else 'mistralai/mistral-nemo'
        
        # Build prompt
        prompt = self._build_titles_prompt(plan, site_profile, existing_titles)
        
        # Generate titles via OpenRouter
        messages = [{'role': 'user', 'content': prompt}]
        
        result = self.openrouter.generate_text(
            messages=messages,
            model=titles_model,
            temperature=0.8,
            max_tokens=4096
        )
        
        # Parse response
        titles_data = self._parse_titles_response(result.content)
        
        # Create EditorialPlanItem for each title
        for idx, title_data in enumerate(titles_data[:30], start=1):
            scheduled_date = plan.start_date + timedelta(days=idx - 1)
            
            item = EditorialPlanItem.objects.create(
                plan=plan,
                day_index=idx,
                title=title_data['title'],
                keyword_focus=title_data.get('keyword', plan.keywords[0]),
                cluster=title_data.get('cluster', ''),
                search_intent=title_data.get('intent', 'informational'),
                trend_references=title_data.get('trend_refs', []),
                scheduled_date=scheduled_date,
                status=EditorialPlanItem.Status.PENDING
            )
            
            # Generate external_id
            item.external_id = item.generate_external_id()
            item.save()
        
        logger.info(f"Created {len(titles_data[:30])} plan items")
    
    def _build_titles_prompt(
        self,
        plan: EditorialPlan,
        site_profile: SiteProfile,
        existing_titles: list[str]
    ) -> str:
        """Build prompt for title generation."""
        
        keywords_str = ', '.join(plan.keywords)
        site_name = site_profile.site_name
        
        # Include trend insights if available
        trend_context = ""
        if plan.trend_pack:
            top_insights = plan.trend_pack.insights[:10]
            trend_context = "\n\n**TRENDING TOPICS:**\n"
            for insight in top_insights:
                trend_context += f"- {insight['title']}: {insight['summary'][:100]}...\n"
        
        # Anti-cannibalization context
        existing_context = ""
        if existing_titles:
            existing_context = f"\n\n**EXISTING TITLES (avoid similar topics):**\n"
            for title in existing_titles[:20]:
                existing_context += f"- {title}\n"
        
        prompt = f"""You are a content strategist creating a 30-day editorial calendar for "{site_name}".

**SEED KEYWORDS:** {keywords_str}
{trend_context}
{existing_context}

**TASK:** Generate EXACTLY 30 blog post titles that:
1. Cover diverse angles and subtopics related to the seed keywords
2. Are SEO-optimized and click-worthy
3. Avoid duplicating existing content
4. Include a mix of search intents (informational, commercial, how-to, listicle)
5. Are organized into thematic clusters

**OUTPUT FORMAT (valid JSON):**
```json
{{
  "titles": [
    {{
      "title": "10 Proven Strategies for...",
      "keyword": "main keyword",
      "cluster": "beginner tips",
      "intent": "informational",
      "trend_refs": [0, 2]
    }}
  ]
}}
```

Generate all 30 titles now. Be creative and diverse!"""
        
        return prompt
    
    def _parse_titles_response(self, content: str) -> list[dict]:
        """
        Parse AI response into structured titles data.
        
        Args:
            content: AI response content
        
        Returns:
            List of title dicts
        """
        import json
        
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        try:
            data = json.loads(content)
            titles = data.get('titles', [])
            
            logger.info(f"Parsed {len(titles)} titles from AI response")
            return titles
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse titles JSON: {e}")
            # Fallback: return empty list
            return []
    
    def approve_plan(self, plan: EditorialPlan, approved_by) -> None:
        """
        Approve an editorial plan.
        
        Args:
            plan: EditorialPlan instance
            approved_by: User who approved
        """
        plan.status = EditorialPlan.Status.APPROVED
        plan.approved_by = approved_by
        plan.approved_at = datetime.now()
        plan.save()
        
        # Update all items to SCHEDULED
        plan.items.update(status=EditorialPlanItem.Status.SCHEDULED)
        
        logger.info(f"Plan {plan.id} approved by {approved_by.email}")
    
    def reject_plan(self, plan: EditorialPlan, reason: str) -> None:
        """
        Reject an editorial plan.
        
        Args:
            plan: EditorialPlan instance
            reason: Rejection reason
        """
        plan.status = EditorialPlan.Status.REJECTED
        plan.rejection_reason = reason
        plan.save()
        
        logger.info(f"Plan {plan.id} rejected: {reason}")
    
    def activate_plan(self, plan: EditorialPlan) -> None:
        """
        Activate an approved plan (start scheduling posts).
        
        Args:
            plan: EditorialPlan instance
        """
        if plan.status != EditorialPlan.Status.APPROVED:
            raise ValueError("Can only activate approved plans")
        
        plan.status = EditorialPlan.Status.ACTIVE
        plan.save()
        
        logger.info(f"Plan {plan.id} activated")
    
    def check_anti_cannibalization(
        self,
        title: str,
        existing_titles: list[str],
        threshold: float = 0.7
    ) -> bool:
        """
        Check if a title is too similar to existing content.
        
        Args:
            title: New title to check
            existing_titles: List of existing titles
            threshold: Similarity threshold (0-1)
        
        Returns:
            True if title is unique enough, False if too similar
        """
        # Simple word overlap check (can be enhanced with embeddings)
        title_words = set(title.lower().split())
        
        for existing in existing_titles:
            existing_words = set(existing.lower().split())
            
            # Calculate Jaccard similarity
            intersection = title_words & existing_words
            union = title_words | existing_words
            
            if len(union) > 0:
                similarity = len(intersection) / len(union)
                
                if similarity > threshold:
                    logger.warning(f"Title too similar: '{title}' vs '{existing}' ({similarity:.2f})")
                    return False
        
        return True
