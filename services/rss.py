"""
RSS Feed Service for PostPro.
Handles fetching, parsing, and deduplication of RSS feed items.
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import feedparser
import requests

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_TIMEOUT = 30
MAX_ITEMS_PER_FETCH = 50


@dataclass
class RSSFeedItem:
    """Parsed RSS item data."""
    url: str
    title: str
    description: str
    image_url: str
    published_at: Optional[datetime]
    author: str
    source_name: str
    content_hash: str


class RSSServiceError(Exception):
    """Base RSS service error."""
    pass


class FeedFetchError(RSSServiceError):
    """Error fetching RSS feed."""
    pass


class FeedParseError(RSSServiceError):
    """Error parsing RSS feed."""
    pass


class RSSService:
    """
    Service for fetching and parsing RSS feeds.
    Supports any standard RSS 2.0 or Atom feed.
    """
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
    
    def fetch_feed(self, feed_url: str) -> list[RSSFeedItem]:
        """
        Fetch and parse an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
        
        Returns:
            List of RSSFeedItem objects
        
        Raises:
            FeedFetchError: If feed cannot be fetched
            FeedParseError: If feed cannot be parsed
        """
        logger.info(f"Fetching RSS feed: {feed_url}")
        
        try:
            # Fetch feed
            response = requests.get(
                feed_url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "PostPro RSS Reader/1.0",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*"
                }
            )
            response.raise_for_status()
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch feed {feed_url}: {e}")
            raise FeedFetchError(f"Failed to fetch feed: {e}")
        
        # Parse feed
        try:
            feed = feedparser.parse(response.content)
            
            if feed.bozo and not feed.entries:
                raise FeedParseError(f"Invalid feed format: {feed.bozo_exception}")
            
        except Exception as e:
            logger.error(f"Failed to parse feed {feed_url}: {e}")
            raise FeedParseError(f"Failed to parse feed: {e}")
        
        # Extract source name from feed
        source_name = self._extract_source_name(feed, feed_url)
        
        # Parse items
        items = []
        for entry in feed.entries[:MAX_ITEMS_PER_FETCH]:
            try:
                item = self._parse_entry(entry, source_name)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse entry: {e}")
                continue
        
        logger.info(f"Parsed {len(items)} items from feed")
        return items
    
    def _extract_source_name(self, feed, feed_url: str) -> str:
        """Extract source name from feed metadata or URL."""
        # Try feed title
        if hasattr(feed, 'feed') and hasattr(feed.feed, 'title'):
            return feed.feed.title
        
        # Fallback to domain name
        parsed = urlparse(feed_url)
        domain = parsed.netloc.replace('www.', '')
        return domain.split('.')[0].title()
    
    def _parse_entry(self, entry: dict, source_name: str) -> Optional[RSSFeedItem]:
        """Parse a single RSS entry into RSSFeedItem."""
        # Required: URL and title
        url = entry.get('link', '')
        title = entry.get('title', '')
        
        if not url or not title:
            return None
        
        # Description (try multiple fields)
        description = ''
        if hasattr(entry, 'summary'):
            description = entry.summary
        elif hasattr(entry, 'description'):
            description = entry.description
        elif hasattr(entry, 'content') and entry.content:
            description = entry.content[0].get('value', '')
        
        # Clean HTML from description
        description = self._clean_html(description)
        
        # Image URL (try multiple sources)
        image_url = self._extract_image_url(entry)
        
        # Published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except:
                pass
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                published_at = datetime(*entry.updated_parsed[:6])
            except:
                pass
        
        # Author
        author = ''
        if hasattr(entry, 'author'):
            author = entry.author
        elif hasattr(entry, 'author_detail') and hasattr(entry.author_detail, 'name'):
            author = entry.author_detail.name
        
        # Generate content hash for deduplication
        content_hash = self._calculate_hash(url, title)
        
        return RSSFeedItem(
            url=url,
            title=title,
            description=description[:5000],  # Limit description length
            image_url=image_url,
            published_at=published_at,
            author=author,
            source_name=source_name,
            content_hash=content_hash,
        )
    
    def _extract_image_url(self, entry: dict) -> str:
        """Extract image URL from RSS entry."""
        # Try media:content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if media.get('type', '').startswith('image'):
                    return media.get('url', '')
        
        # Try media:thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0].get('url', '')
        
        # Try enclosure
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image'):
                    return enclosure.get('href', '') or enclosure.get('url', '')
        
        # Try og:image in content
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].get('value', '')
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        
        return ''
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags and clean text."""
        if not html:
            return ''
        
        # Remove scripts and styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove all HTML tags
        html = re.sub(r'<[^>]+>', ' ', html)
        
        # Clean whitespace
        html = re.sub(r'\s+', ' ', html).strip()
        
        # Decode common entities
        html = html.replace('&nbsp;', ' ')
        html = html.replace('&amp;', '&')
        html = html.replace('&lt;', '<')
        html = html.replace('&gt;', '>')
        html = html.replace('&quot;', '"')
        
        return html
    
    def _calculate_hash(self, url: str, title: str) -> str:
        """Calculate SHA256 hash for deduplication."""
        content = f"{url}|{title}".lower()
        return hashlib.sha256(content.encode()).hexdigest()
    
    def matches_keywords(
        self,
        title: str,
        description: str,
        required_keywords: list[str],
        blocked_keywords: list[str],
    ) -> tuple[bool, str]:
        """
        Check if content matches keyword filters.
        
        Args:
            title: Item title
            description: Item description
            required_keywords: At least one must be present (empty = no filter)
            blocked_keywords: None can be present
        
        Returns:
            Tuple of (matches, reason)
        """
        content = f"{title} {description}".lower()
        
        # Check blocked keywords first
        for keyword in blocked_keywords:
            if keyword.lower() in content:
                return False, f"Blocked keyword: {keyword}"
        
        # Check required keywords (if any)
        if required_keywords:
            for keyword in required_keywords:
                if keyword.lower() in content:
                    return True, f"Matched keyword: {keyword}"
            return False, "No required keywords matched"
        
        return True, "No filters applied"
    
    def validate_feed_url(self, feed_url: str) -> tuple[bool, str]:
        """
        Validate that a URL is a valid RSS feed.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            items = self.fetch_feed(feed_url)
            return True, f"Valid feed with {len(items)} items"
        except FeedFetchError as e:
            return False, f"Cannot fetch: {e}"
        except FeedParseError as e:
            return False, f"Invalid format: {e}"
        except Exception as e:
            return False, f"Error: {e}"


def create_rss_items_from_feed(project, rss_service: RSSService = None, feed_url: str = None) -> int:
    """
    Fetch RSS feed for a project and create RSSItem entries.
    
    Args:
        project: Project instance with rss_settings
        rss_service: Optional RSSService instance
        feed_url: Optional specific URL to fetch (overrides settings.feed_url)
    
    Returns:
        Number of new items created
    """
    from apps.automation.models import RSSItem
    from apps.projects.models import ProjectRSSSettings
    from django.db import IntegrityError
    from django.utils import timezone
    
    # Get or create RSS settings
    try:
        settings = project.rss_settings
    except ProjectRSSSettings.DoesNotExist:
        logger.info(f"No RSS settings for project {project.id}")
        return 0
    
    if not settings.is_active:
        logger.info(f"RSS not active for project {project.id}")
        return 0
        
    target_url = feed_url or settings.feed_url
    if not target_url:
        logger.info(f"No RSS URL provided for project {project.id}")
        return 0
    
    # Initialize service
    if rss_service is None:
        rss_service = RSSService()
    
    # Fetch feed
    try:
        items = rss_service.fetch_feed(target_url)
    except RSSServiceError as e:
        logger.error(f"Failed to fetch RSS for project {project.id}: {e}")
        return 0
    
    # Process items
    created_count = 0
    for item in items:
        # Check keywords filter
        matches, reason = rss_service.matches_keywords(
            item.title,
            item.description,
            settings.required_keywords or [],
            settings.blocked_keywords or [],
        )
        
        if not matches:
            logger.debug(f"Skipping item: {reason}")
            continue
        
        # Create RSSItem (skip if already exists)
        try:
            rss_item = RSSItem.objects.create(
                project=project,
                source_url=item.url,
                source_title=item.title,
                source_description=item.description,
                source_image_url=item.image_url,
                source_published_at=item.published_at,
                source_author=item.author,
                source_hash=item.content_hash,
                status=RSSItem.Status.PENDING,
            )
            created_count += 1
            logger.info(f"Created RSSItem: {item.title[:50]}")
            
        except IntegrityError:
            # Already exists (duplicate URL)
            logger.debug(f"RSSItem already exists: {item.url}")
            continue
    
    # Update last checked timestamp only if using settings URL (legacy mode)
    if not feed_url:
        settings.last_checked_at = timezone.now()
        settings.save(update_fields=['last_checked_at'])
    
    logger.info(f"Created {created_count} new RSS items for project {project.id}")
    return created_count
