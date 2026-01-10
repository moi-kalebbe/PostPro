"""
AI Agents for PostPro content generation pipeline.

Pipeline: Research → Strategy → Article → Image
"""

import re
import logging
from typing import Optional
from decimal import Decimal

from services.openrouter import (
    OpenRouterService,
    ResearchSchema,
    StrategySchema,
    OpenRouterTextResult,
    OpenRouterImageResult,
    InvalidResponseError,
)
from services.pollinations import (
    PollinationsService,
    PollinationsImageResult,
    PollinationsError,
)
from apps.automation.models import Post, PostArtifact

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for AI agents."""
    
    def __init__(self, openrouter: OpenRouterService, post: Post):
        self.openrouter = openrouter
        self.post = post
        self.project = post.project
        self._site_profile = None
        self._content_settings = None
    
    @property
    def content_settings(self):
        """Get content settings for the project (auto-creates if needed)."""
        if self._content_settings is None:
            self._content_settings = self.project.content_settings
        return self._content_settings
    
    @property
    def site_profile(self):
        """Lazy load site profile for the project."""
        if self._site_profile is None:
            from apps.automation.models import SiteProfile
            self._site_profile = SiteProfile.objects.filter(
                project=self.project
            ).order_by('-created_at').first()
        return self._site_profile
    
    @property
    def language(self) -> str:
        """Get content language from ProjectContentSettings, SiteProfile, or default to pt-BR."""
        # Priority 1: ProjectContentSettings
        if self.content_settings and self.content_settings.language:
            return self.content_settings.language
        # Priority 2: SiteProfile
        if self.site_profile and self.site_profile.language:
            return self.site_profile.language
        # Default
        return 'pt-BR'
    
    @property
    def site_context(self) -> str:
        """Build site context string from SiteProfile."""
        if not self.site_profile:
            return ""
        
        context_parts = []
        if self.site_profile.site_name:
            context_parts.append(f"Site: {self.site_profile.site_name}")
        if self.site_profile.categories:
            category_names = [c.get('name', c) for c in self.site_profile.categories[:5]]
            context_parts.append(f"Categories: {', '.join(category_names)}")
        if self.site_profile.tone_analysis:
            context_parts.append(f"Tone: {self.site_profile.tone_analysis[:100]}")
        
        return "\n".join(context_parts)
    
    @property
    def custom_instructions(self) -> str:
        """Get custom instructions from ProjectContentSettings."""
        parts = []
        if self.content_settings.custom_writing_style:
            parts.append(f"Writing Style: {self.content_settings.custom_writing_style}")
        if self.content_settings.custom_instructions:
            parts.append(f"Additional Instructions: {self.content_settings.custom_instructions}")
        if self.content_settings.avoid_topics:
            avoid_list = self.content_settings.get_avoid_topics_list()
            if avoid_list:
                parts.append(f"Topics to AVOID: {', '.join(avoid_list)}")
        return "\n".join(parts)
    
    def save_artifact(
        self,
        step: str,
        input_prompt: str,
        system_prompt: str,
        result: OpenRouterTextResult,
        parsed_output: dict,
    ) -> PostArtifact:
        """Save artifact and deactivate previous versions."""
        artifact = PostArtifact.objects.create(
            post=self.post,
            step=step,
            input_prompt=input_prompt,
            system_prompt=system_prompt,
            model_used=result.model,
            provider_response=result.raw,
            parsed_output=parsed_output,
            tokens_used=result.usage.get("total_tokens", 0),
            cost=result.cost,
            is_active=True,
        )
        artifact.deactivate_previous()
        return artifact


class ResearchAgent(BaseAgent):
    """
    Agent 1: Research
    Gathers statistics, trends, and questions about the keyword.
    Uses Perplexity Sonar for real-time web search when available.
    """
    
    def _get_system_prompt(self) -> str:
        """Build system prompt with language specification."""
        return f"""You are an expert content researcher. Your task is to gather relevant, current information about a topic for creating a comprehensive blog article.

IMPORTANT: All research output must be in {self.language}.

Return your research as VALID JSON ONLY (no markdown, no commentary) with this exact structure:
{{
    "statistics": ["stat1 with source", "stat2 with source", "stat3 with source"],
    "trends": ["current trend 1", "current trend 2"],
    "questions": ["common question 1", "common question 2", "common question 3"],
    "key_points": ["important point 1", "important point 2"]
}}

Requirements:
- statistics: At least 3 relevant statistics or data points (include sources when possible)
- trends: At least 2 current trends related to the topic
- questions: At least 3 questions that readers commonly ask about this topic
- key_points: 2-3 key points that must be covered in the article

Focus on accurate, relevant, and recent information. Prioritize data from the last 90 days."""
    
    def run(self) -> dict:
        """Execute research and return parsed data."""
        # Detect model
        research_model = self.project.get_research_model()
        is_perplexity = "perplexity" in research_model.lower() or "sonar" in research_model.lower()

        # Build context from site profile
        site_context = self.site_context
        context_section = f"\nSite Context:\n{site_context}" if site_context else ""
        
        input_prompt = f"""Research the following topic for a blog article:

Keyword: {self.post.keyword}
Target Language: {self.language}
Target Tone: {self.project.tone}
Industry Context: Blog content for a professional website{context_section}

Provide comprehensive, current research data in JSON format.
All content must be written in {self.language}."""

        # Perplexity Optimization
        if is_perplexity:
            input_prompt += f"""

IMPORTANT: Use your online search capabilities to find the most RECENT information (last 30-90 days).
Ensure the output is strictly valid JSON."""
        
        system_prompt = self._get_system_prompt()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_prompt},
        ]
        
        try:
            parsed, result = self.openrouter.generate_with_schema(
                messages=messages,
                schema_class=ResearchSchema,
                model=research_model,
            )
            
            output_dict = parsed.model_dump()
            
            # Save artifact
            self.save_artifact(
                step=PostArtifact.Step.RESEARCH,
                input_prompt=input_prompt,
                system_prompt=system_prompt,
                result=result,
                parsed_output=output_dict,
            )
            
            # Update post
            self.post.research_data = output_dict
            self.post.text_generation_cost += result.cost
            self.post.tokens_total += result.usage.get("total_tokens", 0)
            self.post.step_state["research"] = "completed"
            self.post.save()
            
            return output_dict
            
        except InvalidResponseError as e:
            self.post.step_state["research"] = "failed"
            self.post.save()
            logger.error(f"Research agent failed for {self.post.id}: {e}")
            raise


class StrategyAgent(BaseAgent):
    """
    Agent 2: SEO Strategy
    Creates title, meta description, and article structure.
    """
    
    def _get_system_prompt(self) -> str:
        """Build system prompt with language and structure settings."""
        settings = self.content_settings
        min_h2 = settings.h2_sections_min
        max_h2 = settings.h2_sections_max
        
        return f"""You are an expert SEO strategist and content planner. Your task is to create an optimized structure for a blog article.

IMPORTANT: All output must be in {self.language}.

Return your strategy as VALID JSON ONLY (no markdown, no commentary) with this exact structure:
{{
    "title": "SEO-optimized title (max 60 chars)",
    "meta_description": "Compelling meta description (max 160 chars)",
    "h2_sections": ["Section 1", "Section 2", "Section 3", "Section 4", "Section 5"]
}}

Requirements:
- title: Catchy, SEO-friendly, includes main keyword, written in {self.language}
- meta_description: Compelling, includes keyword, encourages clicks, in {self.language}
- h2_sections: {min_h2}-{max_h2} logical sections for the article, in {self.language}

Focus on SEO best practices and reader engagement."""
    
    def run(self, research_data: dict) -> dict:
        """Execute strategy planning and return parsed data."""
        system_prompt = self._get_system_prompt()
        
        input_prompt = f"""Create an SEO strategy for this blog article:

Keyword: {self.post.keyword}
Target Language: {self.language}
Target Tone: {self.project.tone}

Research Data:
- Statistics: {research_data.get('statistics', [])}
- Trends: {research_data.get('trends', [])}
- Questions: {research_data.get('questions', [])}
- Key Points: {research_data.get('key_points', [])}

Create an optimized article structure in JSON format.
All content must be written in {self.language}."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_prompt},
        ]
        
        try:
            parsed, result = self.openrouter.generate_with_schema(
                messages=messages,
                schema_class=StrategySchema,
                model=self.project.get_text_model(),
            )
            
            output_dict = parsed.model_dump()
            
            # Save artifact
            self.save_artifact(
                step=PostArtifact.Step.STRATEGY,
                input_prompt=input_prompt,
                system_prompt=system_prompt,
                result=result,
                parsed_output=output_dict,
            )
            
            # Update post
            self.post.strategy_data = output_dict
            self.post.title = output_dict["title"]
            self.post.meta_description = output_dict["meta_description"]
            self.post.text_generation_cost += result.cost
            self.post.tokens_total += result.usage.get("total_tokens", 0)
            self.post.step_state["strategy"] = "completed"
            self.post.save()
            
            return output_dict
            
        except InvalidResponseError as e:
            self.post.step_state["strategy"] = "failed"
            self.post.save()
            logger.error(f"Strategy agent failed for {self.post.id}: {e}")
            raise


class ArticleAgent(BaseAgent):
    """
    Agent 3: Article Writer
    Writes the full article content in HTML.
    """
    
    def _get_system_prompt(self) -> str:
        """Build system prompt with language and word count from settings."""
        settings = self.content_settings
        min_words = settings.min_word_count
        max_words = settings.max_word_count
        
        return f"""You are an expert blog writer. Write a comprehensive, engaging article based on the provided structure.

CRITICAL: Write the ENTIRE article in {self.language}. Do NOT write in any other language.

Requirements:
- Write in HTML format (NO markdown)
- DO NOT include <h1> tags (title is added separately)
- Use <h2> for section headings
- Use <p> for paragraphs
- Use <ul>/<li> for lists where appropriate
- Use <strong> and <em> for emphasis
- Write {min_words}-{max_words} words
- Include all provided sections
- Incorporate statistics naturally
- DO NOT include <script> tags or any JavaScript
- DO NOT include <style> tags

Return ONLY the HTML content, no commentary or explanation."""
    
    def run(self, research_data: dict, strategy_data: dict) -> str:
        """Execute article writing and return HTML content."""
        system_prompt = self._get_system_prompt()
        
        tone_instructions = {
            "formal": "Use professional, formal language appropriate for business contexts.",
            "casual": "Use friendly, conversational language that's easy to read.",
            "technical": "Use precise technical language with proper terminology.",
        }
        
        # Build site context
        site_context = self.site_context
        context_section = f"\nSite Context:\n{site_context}" if site_context else ""
        
        # Build custom instructions section
        custom_instr = self.custom_instructions
        custom_section = f"\n\nCustom Instructions:\n{custom_instr}" if custom_instr else ""
        
        # Structural instructions (Conditional)
        structural_instructions = []
        if self.content_settings.include_summary:
            structural_instructions.append("- INCLUDE a brief Executive Summary at the beginning.")
        
        if self.content_settings.include_faq:
            structural_instructions.append("- INCLUDE a dedicated 'Frequently Asked Questions' section at the end (using <h2>).")
        else:
            structural_instructions.append("- Do NOT create a dedicated FAQ section. Address questions naturally if relevant.")

        if self.content_settings.include_conclusion:
            structural_instructions.append("- INCLUDE a dedicated Conclusion section.")
        else:
            structural_instructions.append("- Do NOT create a dedicated Conclusion section.")
            
        structural_str = "\n".join(structural_instructions)
        
        input_prompt = f"""Write a complete blog article with this structure:

Title: {strategy_data.get('title', self.post.keyword)}
Language: {self.language}
Target Word Count: {self.content_settings.min_word_count}-{self.content_settings.max_word_count} words
Sections to cover:
{chr(10).join(f'- {section}' for section in strategy_data.get('h2_sections', []))}

Structural Requirements:
{structural_str}

Research to incorporate:
- Key Statistics: {research_data.get('statistics', [])}
- Industry Trends: {research_data.get('trends', [])}
- Questions to Answer: {research_data.get('questions', [])}
- Key Points: {research_data.get('key_points', [])}{context_section}{custom_section}

Ensure the content flows logically and addresses the user's intent.

Tone: {tone_instructions.get(self.project.tone, tone_instructions['casual'])}

IMPORTANT: Write the entire article in {self.language}. Do NOT write in English unless {self.language} is en-US or en-GB.

Write the article in clean HTML format."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_prompt},
        ]
        
        result = self.openrouter.generate_text(
            messages=messages,
            model=self.project.get_text_model(),
            max_tokens=8192,
        )
        
        content = result.content
        
        # Validate HTML content
        content = self._sanitize_html(content)
        is_valid, issues = self._validate_html(content)
        
        if not is_valid:
            logger.warning(f"Article validation issues: {issues}")
        
        # Save artifact
        self.save_artifact(
            step=PostArtifact.Step.ARTICLE,
            input_prompt=input_prompt,
            system_prompt=system_prompt,
            result=result,
            parsed_output={"html": content, "validation_issues": issues},
        )
        
        # Update post
        self.post.content = content
        self.post.text_generation_cost += result.cost
        self.post.tokens_total += result.usage.get("total_tokens", 0)
        self.post.step_state["article"] = "completed"
        self.post.save()
        
        return content
    
    def _sanitize_html(self, html: str) -> str:
        """Remove potentially dangerous elements from HTML."""
        # Remove script tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove style tags
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove on* event handlers
        html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        # Remove h1 tags
        html = re.sub(r'<h1[^>]*>.*?</h1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        return html.strip()
    
    def _validate_html(self, html: str) -> tuple[bool, list]:
        """Validate HTML structure."""
        issues = []
        
        # Check for h2 sections
        h2_count = len(re.findall(r'<h2[^>]*>', html, re.IGNORECASE))
        if h2_count < 3:
            issues.append(f"Only {h2_count} H2 sections found (expected 5+)")
        
        # Check for paragraphs
        p_count = len(re.findall(r'<p[^>]*>', html, re.IGNORECASE))
        if p_count < 5:
            issues.append(f"Only {p_count} paragraphs found")
        
        # Check word count (rough estimate)
        text_only = re.sub(r'<[^>]+>', ' ', html)
        word_count = len(text_only.split())
        if word_count < 800:
            issues.append(f"Only ~{word_count} words (expected 1200+)")
        
        return len(issues) == 0, issues


class ImageAgent(BaseAgent):
    """
    Agent 4: Image Generator
    Creates featured image for the article.
    Supports both OpenRouter and Pollinations for image generation.
    """
    
    def _is_pollinations_model(self, model: str) -> bool:
        """Check if the model is a Pollinations model."""
        return model.startswith("pollinations/")
    
    def _get_pollinations_model_name(self, model: str) -> str:
        """Extract Pollinations model name from full identifier."""
        # e.g., "pollinations/flux" -> "flux"
        if model.startswith("pollinations/"):
            return model.split("/", 1)[1]
        return model
    
    def run(self, title: str = None) -> str:
        """Generate featured image and return data URL."""
        style_prompts = {
            "photographic": "photorealistic, high quality photo, professional photography",
            "illustration": "modern digital illustration, clean vector style",
            "minimalist": "minimalist design, simple shapes, modern aesthetic",
        }
        
        style = style_prompts.get(self.project.image_style, style_prompts["photographic"])
        
        prompt = f"""Create a professional blog featured image for an article about: {title or self.post.keyword}

Style: {style}
Requirements:
- Clean, professional look
- No text overlays
- Suitable for a blog header
- High quality, visually appealing
- Relevant to the topic"""
        
        image_model = self.project.get_image_model()
        
        try:
            # Choose provider based on model
            if self._is_pollinations_model(image_model):
                # Use Pollinations for pollinations/* models
                pollinations_model = self._get_pollinations_model_name(image_model)
                logger.info(f"Using Pollinations for image generation with model: {pollinations_model}")
                
                pollinations = PollinationsService()
                result = pollinations.generate_image(
                    prompt=prompt,
                    model=pollinations_model,
                    width=1920,
                    height=1080,
                    nologo=True,
                    enhance=True,
                )
                
                image_data_url = result.image_data_url
                model_used = image_model
                cost = result.cost
            else:
                # Use OpenRouter for openai/* models (DALL-E 3, etc.)
                logger.info(f"Using OpenRouter for image generation with model: {image_model}")
                
                result = self.openrouter.generate_image(
                    prompt=prompt,
                    model=image_model,
                )
                
                image_data_url = result.image_data_url
                model_used = result.model
                cost = result.cost
            
            # Save artifact
            PostArtifact.objects.create(
                post=self.post,
                step=PostArtifact.Step.IMAGE,
                input_prompt=prompt,
                system_prompt="Image generation",
                model_used=model_used,
                provider_response={"truncated": True},  # Don't store full base64
                parsed_output={"image_generated": True, "provider": "pollinations" if self._is_pollinations_model(image_model) else "openrouter"},
                cost=cost,
                is_active=True,
            ).deactivate_previous()
            
            # Update post
            self.post.image_generation_cost += cost
            self.post.step_state["image"] = "completed"
            self.post.save()
            
            return image_data_url
            
        except (PollinationsError, Exception) as e:
            self.post.step_state["image"] = "failed"
            self.post.save()
            logger.error(f"Image agent failed for {self.post.id}: {e}")
            raise


def run_full_pipeline(
    post: Post,
    openrouter: OpenRouterService,
    generate_image: bool = True,
) -> Post:
    """
    Run the full content generation pipeline.
    
    Args:
        post: Post instance to populate
        openrouter: Configured OpenRouter service
        generate_image: Whether to generate featured image
    
    Returns:
        Updated Post instance
    """
    logger.info(f"Starting pipeline for post {post.id}: {post.keyword}")
    
    try:
        # Step 1: Research
        research_agent = ResearchAgent(openrouter, post)
        research_data = research_agent.run()
        
        # Step 2: Strategy
        strategy_agent = StrategyAgent(openrouter, post)
        strategy_data = strategy_agent.run(research_data)
        
        # Step 3: Article
        article_agent = ArticleAgent(openrouter, post)
        article_agent.run(research_data, strategy_data)
        
        # Step 4: Image (optional - failure is non-fatal)
        if generate_image:
            try:
                image_agent = ImageAgent(openrouter, post)
                image_data_url = image_agent.run(post.title)
                # Image upload happens in the task
            except Exception as e:
                logger.warning(f"Image generation failed for post {post.id}, continuing without image: {e}")
        
        # Update total cost
        post.update_total_cost()
        
        # Update status
        post.status = Post.Status.PENDING_REVIEW
        post.save()
        
        logger.info(f"Pipeline completed for post {post.id}")
        return post
        
    except Exception as e:
        post.status = Post.Status.FAILED
        post.save()
        logger.error(f"Pipeline failed for post {post.id}: {e}")
        raise
