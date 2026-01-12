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

# ============================================================================
# Fallback Configuration (Priority Waterfall)
# ============================================================================
# Attempts to use these models in order if the primary model fails.
FALLBACK_TEXT_MODELS = [
    "openai/gpt-4o",                 # Premium Standard
    "anthropic/claude-3.5-sonnet",   # High Intelligence
    "deepseek/deepseek-r1",          # Strong Reasoning (User requested)
    "openai/gpt-4o-mini",            # Reliable/Fast Backup
]

FALLBACK_IMAGE_MODELS = [
    "stabilityai/stable-diffusion-xl-base-1.0", # Reliable Standard
    "openai/dall-e-3",                          # High Quality Fallback
]

class BaseAgent:
    """Base class for AI agents with fallback support."""
    
    def __init__(self, openrouter: OpenRouterService, post: Post):
        self.openrouter = openrouter
        self.post = post
        self.project = post.project
        self._site_profile = None
        self._content_settings = None
    
    def _run_with_fallback(self, operation_name: str, func, **kwargs) -> any:
        """
        Execute a function with automatic model fallback.
        
        Args:
            operation_name: Name for logging (e.g. "Strategy Generation")
            func: The function to call (e.g. self.openrouter.completion)
            **kwargs: Arguments for the function. 'model' must be in kwargs.
        """
        primary_model = kwargs.get('model')
        
        # 1. Try Primary Model
        try:
            return func(**kwargs)
        except Exception as e:
            logger.warning(f"{operation_name} failed with primary model {primary_model}: {e}. Starting fallback chain.")
            
            # Determine which fallback list to use
            is_image = "generate_image" in func.__name__ or "image" in operation_name.lower()
            fallback_list = FALLBACK_IMAGE_MODELS if is_image else FALLBACK_TEXT_MODELS
            
            # 2. Iterate Fallbacks
            for fallback_model in fallback_list:
                if fallback_model == primary_model:
                    continue # Skip if it was the primary one
                    
                logger.info(f"Retrying {operation_name} with fallback model: {fallback_model}")
                kwargs['model'] = fallback_model
                try:
                    return func(**kwargs)
                except Exception as fallback_error:
                    logger.warning(f"Fallback model {fallback_model} failed: {fallback_error}")
                    continue
            
            # 3. If all fail, raise the last error
            logger.error(f"All models failed for {operation_name}")
            raise e
    
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
            # Wrap API call with fallback
            parsed, result = self._run_with_fallback(
                "Research Generation",
                self.openrouter.generate_with_schema,
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
        
        return f"""You are an expert SEO strategist and content planner. Your task is to create an optimized structure for a blog article that will score 75+ on Rank Math SEO.

IMPORTANT: All output must be in {self.language}.

Return your strategy as VALID JSON ONLY (no markdown, no commentary) with this exact structure:
{{
    "title": "SEO-optimized title (max 60 chars)",
    "meta_description": "Compelling meta description (max 160 chars)",
    "slug": "url-friendly-slug",
    "h2_sections": ["Section 1", "Section 2", "Section 3", "Section 4", "Section 5"],
    "image_alt_text": "Descriptive alt text for featured image"
}}

CRITICAL SEO Requirements:
- title: MUST start with or contain the main keyword in the FIRST 50 characters. Max 60 chars total. In {self.language}.
- meta_description: MUST include the main keyword. Keep 130-150 chars. Encourage clicks. In {self.language}.
- slug: URL-friendly version of the keyword (lowercase, hyphens, no special chars). Example: "beach-tennis-tournament-rules"
- h2_sections: {min_h2}-{max_h2} sections. At least 2 sections MUST include the keyword or a close variation.
- image_alt_text: Describe the image topic, include keyword naturally. Example: "Jogadores de beach tennis em torneio"

Focus on SEO best practices for Rank Math 75+ score."""
    
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
            # Wrap API call with fallback
            parsed, result = self._run_with_fallback(
                "Strategy Generation",
                self.openrouter.generate_with_schema,
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
        
        return f"""You are an expert blog writer optimizing for Rank Math SEO 75+ score. Write a comprehensive, engaging article based on the provided structure.

CRITICAL: Write the ENTIRE article in {self.language}. Do NOT write in any other language.

HTML Format Requirements:
- Write in HTML format (NO markdown)
- DO NOT include <h1> tags (title is added separately)
- Use <h2> for section headings
- Use <p> for paragraphs
- Use <ul>/<li> for lists where appropriate
- Use <strong> and <em> for emphasis
- DO NOT include <script> or <style> tags

SEO CRITICAL Requirements (for Rank Math 75+ score):
- The main KEYWORD must appear in the FIRST paragraph (first 10% of content)
- The KEYWORD must appear in at least 2-3 H2 headings
- Keyword density: Use keyword 1-1.5% throughout (naturally, not forced)
- Include 2-3 external links to authoritative sources (use <a href="URL" target="_blank" rel="noopener">text</a>)
- Write {min_words}-{max_words} words minimum
- Include all provided sections
- Incorporate statistics naturally

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
        
        # Wrap API call with fallback
        result = self._run_with_fallback(
            "Article Generation",
            self.openrouter.generate_text,
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
        
        # Fallback Logic Implementation
        model_used = image_model
        cost = Decimal("0.0")
        image_data_url = None

        try:
            # 1. Pollinations Primary Handling
            if self._is_pollinations_model(image_model):
                try:
                    pollinations_model = self._get_pollinations_model_name(image_model)
                    logger.info(f"Using Pollinations (primary): {pollinations_model}")
                    
                    pollinations = PollinationsService()
                    result = pollinations.generate_image(
                        prompt=prompt,
                        model=pollinations_model,
                        width=1920, height=1080, nologo=True, enhance=True
                    )
                    
                    # Direct return for Pollinations success
                    self._save_image_artifact(prompt, image_model, result.cost, result)
                    self._update_post_image(result.cost)
                    return result.image_url if hasattr(result, 'image_url') else result.image_data_url
                    
                except Exception as p_error:
                    logger.warning(f"Pollinations primary model {image_model} failed: {p_error}. Switching to OpenRouter fallback.")
                    # Switch to first OpenRouter fallback
                    image_model = FALLBACK_IMAGE_MODELS[0]

            # 2. OpenRouter Handling (Primary OR Fallback from Pollinations)
            logger.info(f"Using OpenRouter (or fallback): {image_model}")
            
            result = self._run_with_fallback(
                "Image Generation",
                self.openrouter.generate_image,
                prompt=prompt,
                model=image_model,
            )
            
            image_data_url = result.image_data_url
            model_used = result.model
            cost = result.cost
            
            self._save_image_artifact(prompt, model_used, cost, result)
            self._update_post_image(cost)
            
            return image_data_url

        except Exception as e:
            # 3. Ultimate Safety Net: Pollinations Flux (Free)
            # Only try if we generally trust Pollinations and haven't exhausted it exclusively
            if not self._is_pollinations_model(image_model):
                 try:
                     logger.warning(f"All standard image methods failed. Attempting Pollinations/Flux fallback as last resort. Error was: {e}")
                     pollinations = PollinationsService()
                     result = pollinations.generate_image(prompt=prompt, model="flux", width=1920, height=1080, nologo=True, enhance=True)
                     
                     self._save_image_artifact(prompt, "pollinations/flux-fallback", result.cost, result)
                     self._update_post_image(result.cost)
                     return result.image_url
                 except:
                     pass

            self.post.step_state["image"] = "failed"
            self.post.save()
            logger.error(f"Image agent completely failed for {self.post.id}: {e}")
            raise

    def _save_image_artifact(self, prompt, model, cost, result):
        """Helper to save image artifact."""
        is_polli = model.startswith("pollinations") or hasattr(result, 'image_url')
        provider = "pollinations" if is_polli else "openrouter"
        
        PostArtifact.objects.create(
            post=self.post,
            step=PostArtifact.Step.IMAGE,
            input_prompt=prompt,
            system_prompt="Image generation",
            model_used=model,
            provider_response={"truncated": True},
            parsed_output={"image_generated": True, "provider": provider},
            cost=cost,
            is_active=True,
        ).deactivate_previous()

    def _update_post_image(self, cost):
        """Helper to update post cost and status."""
        self.post.image_generation_cost += cost
        self.post.step_state["image"] = "completed"
        self.post.save()


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
                image_result = image_agent.run(post.title)
                
                # Save image URL to post
                if image_result:
                    final_url = image_result
                    
                    # If result is Base64 (starts with data:), upload to Supabase immediately
                    if image_result.startswith("data:"):
                        try:
                            from services.storage import SupabaseStorageService
                            import uuid
                            filename = f"{post.id}_{uuid.uuid4().hex[:8]}"
                            final_url = SupabaseStorageService.upload_base64_image(image_result, filename)
                            logger.info(f"Uploaded generated base64 image to {final_url}")
                        except Exception as upload_err:
                            logger.error(f"Failed to upload base64 image: {upload_err}")
                            # Don't save base64 if upload fails, to avoid DB crash
                            final_url = None
                    
                    if final_url:
                        post.featured_image_url = final_url
                        post.save()
                        logger.info(f"Saved featured image for post {post.id}")
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


# ============================================================================
# News Rewrite Agent (for RSS Feed Posts)
# ============================================================================

class NewsRewriteAgent(BaseAgent):
    """
    Agent for rewriting news articles from RSS feeds.
    
    Unlike the standard pipeline, this agent:
    - Does NOT use ResearchAgent (content already exists)
    - Rewrites in journalistic style
    - Uses NewsArticle schema (not BlogPosting)
    - Includes source attribution
    """
    
    def _get_system_prompt(self) -> str:
        """Build system prompt for news rewriting."""
        return f"""Você é um editor de notícias profissional. Sua tarefa é reescrever uma notícia de outro portal para o blog do cliente, mantendo a precisão das informações mas usando suas próprias palavras.

IDIOMA: Escreva TODA a resposta em {self.language}.

REGRAS CRÍTICAS:
1. REESCREVA completamente - NÃO copie o texto original
2. Mantenha TODOS os fatos e dados precisos
3. Use tom jornalístico profissional
4. NÃO invente informações que não estão na notícia original
5. Estruture como notícia: Lead (quem, o quê, quando, onde) → Detalhes → Contexto
6. Inclua citações se houver na original (entre aspas)
7. Comprimento: 400-800 palavras

FORMATO DE SAÍDA (HTML):
- Use <p> para parágrafos
- Use <h2> para subtítulos se necessário
- Use <strong> para destaques
- Use <blockquote> para citações
- NÃO use <h1> (título é separado)
- NÃO inclua scripts ou estilos

Retorne APENAS o conteúdo HTML reescrito, sem explicações."""
    
    def run(
        self,
        original_title: str,
        original_content: str,
        source_url: str,
        source_name: str,
    ) -> dict:
        """
        Rewrite a news article.
        
        Args:
            original_title: Original article title
            original_content: Original article content/description
            source_url: URL of the original article
            source_name: Name of the source portal
        
        Returns:
            dict with 'title', 'content', 'meta_description', 'slug'
        """
        system_prompt = self._get_system_prompt()
        
        input_prompt = f"""Reescreva a seguinte notícia para o blog:

TÍTULO ORIGINAL: {original_title}

CONTEÚDO ORIGINAL:
{original_content}

FONTE: {source_name} ({source_url})

---

Crie:
1. Um NOVO título SEO-otimizado (máximo 60 caracteres)
2. Uma meta descrição (máximo 160 caracteres)
3. Um slug URL-friendly
4. O conteúdo reescrito em HTML

Formate sua resposta EXATAMENTE assim:
TÍTULO: [seu novo título]
META: [sua meta descrição]
SLUG: [seu-slug-aqui]
CONTEÚDO:
[seu HTML aqui]"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_prompt},
        ]
        
        # Generate rewritten content
        result = self._run_with_fallback(
            "News Rewrite",
            self.openrouter.generate_text,
            messages=messages,
            model=self.project.get_text_model(),
            max_tokens=4096,
        )
        
        # Parse response
        content = result.content
        parsed = self._parse_response(content)
        
        # Add source attribution at the end
        # NOTE: include_source_attribution exists on ProjectRSSSettings, not ProjectContentSettings
        rss_settings = getattr(self.project, 'rss_settings', None)
        should_include_attribution = getattr(rss_settings, 'include_source_attribution', True) if rss_settings else True
        if should_include_attribution:
            attribution = f'''
<p class="news-source-attribution" style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; font-size: 0.9em; color: #666;">
    <em>Notícia originalmente publicada em <a href="{source_url}" rel="nofollow noopener" target="_blank">{source_name}</a>.</em>
</p>'''
            parsed['content'] += attribution
        
        # Sanitize HTML
        parsed['content'] = self._sanitize_html(parsed['content'])
        
        # Save artifact
        PostArtifact.objects.create(
            post=self.post,
            step=PostArtifact.Step.ARTICLE,
            input_prompt=input_prompt,
            system_prompt=system_prompt,
            model_used=result.model,
            provider_response=result.raw,
            parsed_output=parsed,
            tokens_used=result.usage.get("total_tokens", 0),
            cost=result.cost,
            is_active=True,
        ).deactivate_previous()
        
        # Update post
        self.post.title = parsed['title']
        self.post.content = parsed['content']
        self.post.meta_description = parsed['meta_description']
        self.post.text_generation_cost += result.cost
        self.post.tokens_total += result.usage.get("total_tokens", 0)
        self.post.step_state["article"] = "completed"
        self.post.save()
        
        return parsed
    
    def _parse_response(self, content: str) -> dict:
        """Parse structured response from AI."""
        import re
        
        result = {
            'title': '',
            'meta_description': '',
            'slug': '',
            'content': '',
        }
        
        # Extract title
        title_match = re.search(r'TÍTULO:\s*(.+?)(?:\n|META:)', content, re.DOTALL)
        if title_match:
            result['title'] = title_match.group(1).strip()
        
        # Extract meta
        meta_match = re.search(r'META:\s*(.+?)(?:\n|SLUG:)', content, re.DOTALL)
        if meta_match:
            result['meta_description'] = meta_match.group(1).strip()[:160]
        
        # Extract slug
        slug_match = re.search(r'SLUG:\s*(.+?)(?:\n|CONTEÚDO:)', content, re.DOTALL)
        if slug_match:
            result['slug'] = slug_match.group(1).strip().lower()
        
        # Extract content (everything after CONTEÚDO:)
        content_match = re.search(r'CONTEÚDO:\s*(.+)', content, re.DOTALL)
        if content_match:
            result['content'] = content_match.group(1).strip()
        
        # Fallback: if parsing failed, use entire content
        if not result['content']:
            result['content'] = content
        if not result['title']:
            result['title'] = self.post.keyword[:60]
        
        return result
    
    def _sanitize_html(self, html: str) -> str:
        """Remove potentially dangerous elements from HTML."""
        import re
        # Remove script tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove style tags
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove on* event handlers
        html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        # Remove h1 tags
        html = re.sub(r'<h1[^>]*>.*?</h1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        return html.strip()


def run_news_pipeline(
    post: Post,
    openrouter: OpenRouterService,
    rss_item,  # RSSItem instance
    generate_image: bool = True,
    download_source_image: bool = True,
) -> Post:
    """
    Run the news rewrite pipeline for an RSS item.
    
    Args:
        post: Post instance to populate
        openrouter: Configured OpenRouter service
        rss_item: RSSItem with source data
        generate_image: Whether to generate featured image
        download_source_image: Try to use source image first
    
    Returns:
        Updated Post instance
    """
    from apps.automation.models import RSSItem
    
    logger.info(f"Starting news pipeline for post {post.id}: {rss_item.source_title[:50]}")
    
    try:
        # Mark RSS item as processing
        rss_item.mark_processing()
        
        # Step 1: Rewrite Article
        news_agent = NewsRewriteAgent(openrouter, post)
        result = news_agent.run(
            original_title=rss_item.source_title,
            original_content=rss_item.source_description,
            source_url=rss_item.source_url,
            source_name=post.source_name,
        )
        
        # Update SEO data for NewsArticle schema
        post.seo_data = {
            'keyword': post.keyword,
            'seo_title': post.title,
            'seo_description': post.meta_description,
            'slug': result.get('slug', ''),
            'article_type': 'NewsArticle',
            'article_schema': {
                'headline': post.title,
                'description': post.meta_description,
                'keywords': post.keyword,
            },
        }
        post.save()
        
        # Step 2: Handle Image
        if generate_image:
            image_url = None
            
            # Try source image first
            if download_source_image and rss_item.source_image_url:
                try:
                    from services.storage import SupabaseStorageService
                    import uuid
                    
                    # Download and upload to Supabase
                    image_url = SupabaseStorageService.upload_from_url(
                        rss_item.source_image_url,
                        f"news_{post.id}_{uuid.uuid4().hex[:8]}"
                    )
                    logger.info(f"Downloaded source image to: {image_url}")
                except Exception as e:
                    logger.warning(f"Failed to download source image: {e}")
            
            # Fallback to AI-generated image
            if not image_url:
                try:
                    image_agent = ImageAgent(openrouter, post)
                    image_result = image_agent.run(post.title)
                    
                    if image_result:
                        # Handle base64 or URL
                        if image_result.startswith("data:"):
                            from services.storage import SupabaseStorageService
                            import uuid
                            image_url = SupabaseStorageService.upload_base64_image(
                                image_result,
                                f"news_{post.id}_{uuid.uuid4().hex[:8]}"
                            )
                        else:
                            image_url = image_result
                except Exception as e:
                    logger.warning(f"Image generation failed: {e}")
            
            if image_url:
                post.featured_image_url = image_url
                post.save()
        
        # Update total cost
        post.update_total_cost()
        
        # Update status
        post.status = Post.Status.PENDING_REVIEW
        post.article_type = Post.ArticleType.NEWS
        post.save()
        
        # Mark RSS item as completed
        rss_item.mark_completed(post)
        
        logger.info(f"News pipeline completed for post {post.id}")
        return post
        
    except Exception as e:
        post.status = Post.Status.FAILED
        post.save()
        rss_item.mark_failed(str(e))
        logger.error(f"News pipeline failed for post {post.id}: {e}")
        raise
