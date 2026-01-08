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
from apps.automation.models import Post, PostArtifact

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for AI agents."""
    
    def __init__(self, openrouter: OpenRouterService, post: Post):
        self.openrouter = openrouter
        self.post = post
        self.project = post.project
    
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
    """
    
    SYSTEM_PROMPT = """You are an expert content researcher. Your task is to gather relevant information about a topic for creating a comprehensive blog article.

Return your research as VALID JSON ONLY (no markdown, no commentary) with this exact structure:
{
    "statistics": ["stat1", "stat2", "stat3"],
    "trends": ["trend1", "trend2"],
    "questions": ["question1", "question2", "question3"]
}

Requirements:
- statistics: At least 3 relevant statistics or data points
- trends: At least 2 current trends related to the topic
- questions: At least 3 questions that readers commonly ask about this topic

Focus on accurate, relevant, and recent information."""
    
    def run(self) -> dict:
        """Execute research and return parsed data."""
        input_prompt = f"""Research the following topic for a blog article:

Keyword: {self.post.keyword}
Target Tone: {self.project.tone}
Industry Context: Blog content for a professional website

Provide comprehensive research data in JSON format."""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": input_prompt},
        ]
        
        try:
            parsed, result = self.openrouter.generate_with_schema(
                messages=messages,
                schema_class=ResearchSchema,
                model=self.project.get_text_model(),
            )
            
            output_dict = parsed.model_dump()
            
            # Save artifact
            self.save_artifact(
                step=PostArtifact.Step.RESEARCH,
                input_prompt=input_prompt,
                system_prompt=self.SYSTEM_PROMPT,
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
    
    SYSTEM_PROMPT = """You are an expert SEO strategist and content planner. Your task is to create an optimized structure for a blog article.

Return your strategy as VALID JSON ONLY (no markdown, no commentary) with this exact structure:
{
    "title": "SEO-optimized title (max 60 chars)",
    "meta_description": "Compelling meta description (max 160 chars)",
    "h2_sections": ["Section 1", "Section 2", "Section 3", "Section 4", "Section 5"]
}

Requirements:
- title: Catchy, SEO-friendly, includes main keyword
- meta_description: Compelling, includes keyword, encourages clicks
- h2_sections: 5-8 logical sections for the article

Focus on SEO best practices and reader engagement."""
    
    def run(self, research_data: dict) -> dict:
        """Execute strategy planning and return parsed data."""
        input_prompt = f"""Create an SEO strategy for this blog article:

Keyword: {self.post.keyword}
Target Tone: {self.project.tone}

Research Data:
- Statistics: {research_data.get('statistics', [])}
- Trends: {research_data.get('trends', [])}
- Questions: {research_data.get('questions', [])}

Create an optimized article structure in JSON format."""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
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
                system_prompt=self.SYSTEM_PROMPT,
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
    
    SYSTEM_PROMPT = """You are an expert blog writer. Write a comprehensive, engaging article based on the provided structure.

Requirements:
- Write in HTML format (NO markdown)
- DO NOT include <h1> tags (title is added separately)
- Use <h2> for section headings
- Use <p> for paragraphs
- Use <ul>/<li> for lists where appropriate
- Use <strong> and <em> for emphasis
- Write 1200-1800 words
- Include all provided sections
- Incorporate statistics and answer reader questions naturally
- DO NOT include <script> tags or any JavaScript
- DO NOT include <style> tags

Return ONLY the HTML content, no commentary or explanation."""
    
    def run(self, research_data: dict, strategy_data: dict) -> str:
        """Execute article writing and return HTML content."""
        tone_instructions = {
            "formal": "Use professional, formal language appropriate for business contexts.",
            "casual": "Use friendly, conversational language that's easy to read.",
            "technical": "Use precise technical language with proper terminology.",
        }
        
        input_prompt = f"""Write a complete blog article with this structure:

Title: {strategy_data.get('title', self.post.keyword)}
Sections to cover:
{chr(10).join(f'- {section}' for section in strategy_data.get('h2_sections', []))}

Research to incorporate:
- Key Statistics: {research_data.get('statistics', [])}
- Industry Trends: {research_data.get('trends', [])}
- Questions to Answer: {research_data.get('questions', [])}

Tone: {tone_instructions.get(self.project.tone, tone_instructions['casual'])}

Write the article in clean HTML format."""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
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
            system_prompt=self.SYSTEM_PROMPT,
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
    """
    
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
        
        try:
            result = self.openrouter.generate_image(
                prompt=prompt,
                model=self.project.get_image_model(),
            )
            
            # Save artifact
            PostArtifact.objects.create(
                post=self.post,
                step=PostArtifact.Step.IMAGE,
                input_prompt=prompt,
                system_prompt="Image generation",
                model_used=result.model,
                provider_response={"truncated": True},  # Don't store full base64
                parsed_output={"image_generated": True},
                cost=result.cost,
                is_active=True,
            ).deactivate_previous()
            
            # Update post
            self.post.image_generation_cost += result.cost
            self.post.step_state["image"] = "completed"
            self.post.save()
            
            return result.image_data_url
            
        except Exception as e:
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
        
        # Step 4: Image (optional)
        if generate_image:
            image_agent = ImageAgent(openrouter, post)
            image_data_url = image_agent.run(post.title)
            # Image upload to Supabase happens in the task
        
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
