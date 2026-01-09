"""
Site Profile Service for PostPro.
Analyzes WordPress sites via REST API and creates/updates SiteProfile instances.
"""

import logging
import requests
from typing import Optional
from datetime import datetime
from apps.automation.models import SiteProfile
from apps.projects.models import Project

logger = logging.getLogger(__name__)


class SiteProfileService:
    """
    Analyze WordPress sites and create/update SiteProfile instances.
    """
    
    def __init__(self, project: Project):
        self.project = project
        self.base_url = project.wordpress_url.rstrip('/')
        self.wp_rest_api = f"{self.base_url}/wp-json/wp/v2"
    
    def get_or_create_profile(self, force_refresh: bool = False) -> SiteProfile:
        """
        Get existing profile or create new one.
        
        Args:
            force_refresh: If True, re-analyze even if profile exists
        
        Returns:
            SiteProfile instance
        """
        # Check for existing profile
        profile = SiteProfile.objects.filter(project=self.project).first()
        
        if profile and not force_refresh:
            logger.info(f"Using existing profile for {self.project.name}")
            return profile
        
        # Create or update profile
        if profile:
            logger.info(f"Refreshing profile for {self.project.name}")
        else:
            logger.info(f"Creating new profile for {self.project.name}")
            profile = SiteProfile(project=self.project)
        
        # Analyze site
        self._analyze_site(profile)
        
        # Save profile
        profile.save()
        
        return profile
    
    def _analyze_site(self, profile: SiteProfile) -> None:
        """
        Analyze WordPress site and populate profile.
        
        Args:
            profile: SiteProfile instance to populate
        """
        try:
            # Get site metadata
            self._fetch_site_metadata(profile)
            
            # Get categories
            self._fetch_categories(profile)
            
            # Get tags
            self._fetch_tags(profile)
            
            # Get recent posts
            self._fetch_recent_posts(profile)
            
            # Get main pages
            self._fetch_main_pages(profile)
            
            # Try to get sitemap
            self._fetch_sitemap_url(profile)
            
            logger.info(f"Site analysis complete for {self.project.name}")
            
        except Exception as e:
            logger.error(f"Error analyzing site {self.project.name}: {e}")
            raise
    
    def _fetch_site_metadata(self, profile: SiteProfile) -> None:
        """Fetch basic site metadata."""
        try:
            response = requests.get(f"{self.base_url}/wp-json", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                profile.home_url = data.get('home', self.base_url)
                profile.site_name = data.get('name', '')
                profile.site_description = data.get('description', '')
                
                logger.info(f"Fetched metadata: {profile.site_name}")
            else:
                logger.warning(f"Failed to fetch site metadata: {response.status_code}")
                profile.home_url = self.base_url
                
        except Exception as e:
            logger.error(f"Error fetching site metadata: {e}")
            profile.home_url = self.base_url
    
    def _fetch_categories(self, profile: SiteProfile) -> None:
        """Fetch WordPress categories."""
        try:
            response = requests.get(
                f"{self.wp_rest_api}/categories",
                params={'per_page': 100, 'hide_empty': True},
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                
                profile.categories = [
                    {
                        'id': cat['id'],
                        'name': cat['name'],
                        'slug': cat['slug'],
                        'count': cat['count']
                    }
                    for cat in categories
                ]
                
                logger.info(f"Fetched {len(profile.categories)} categories")
            else:
                logger.warning(f"Failed to fetch categories: {response.status_code}")
                profile.categories = []
                
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            profile.categories = []
    
    def _fetch_tags(self, profile: SiteProfile) -> None:
        """Fetch WordPress tags."""
        try:
            response = requests.get(
                f"{self.wp_rest_api}/tags",
                params={'per_page': 100, 'hide_empty': True},
                timeout=10
            )
            
            if response.status_code == 200:
                tags = response.json()
                
                profile.tags = [
                    {
                        'id': tag['id'],
                        'name': tag['name'],
                        'slug': tag['slug'],
                        'count': tag['count']
                    }
                    for tag in tags
                ]
                
                logger.info(f"Fetched {len(profile.tags)} tags")
            else:
                logger.warning(f"Failed to fetch tags: {response.status_code}")
                profile.tags = []
                
        except Exception as e:
            logger.error(f"Error fetching tags: {e}")
            profile.tags = []
    
    def _fetch_recent_posts(self, profile: SiteProfile) -> None:
        """Fetch recent posts for content analysis."""
        try:
            response = requests.get(
                f"{self.wp_rest_api}/posts",
                params={'per_page': 20, 'status': 'publish', '_fields': 'id,title,excerpt,categories,tags'},
                timeout=10
            )
            
            if response.status_code == 200:
                posts = response.json()
                
                profile.recent_posts = [
                    {
                        'id': post['id'],
                        'title': post['title']['rendered'],
                        'excerpt': post['excerpt']['rendered'][:200],
                        'categories': post.get('categories', []),
                        'tags': post.get('tags', [])
                    }
                    for post in posts
                ]
                
                logger.info(f"Fetched {len(profile.recent_posts)} recent posts")
            else:
                logger.warning(f"Failed to fetch posts: {response.status_code}")
                profile.recent_posts = []
                
        except Exception as e:
            logger.error(f"Error fetching recent posts: {e}")
            profile.recent_posts = []
    
    def _fetch_main_pages(self, profile: SiteProfile) -> None:
        """Fetch main pages."""
        try:
            response = requests.get(
                f"{self.wp_rest_api}/pages",
                params={'per_page': 10, 'status': 'publish', '_fields': 'id,title,slug'},
                timeout=10
            )
            
            if response.status_code == 200:
                pages = response.json()
                
                profile.main_pages = [
                    {
                        'id': page['id'],
                        'title': page['title']['rendered'],
                        'slug': page['slug']
                    }
                    for page in pages
                ]
                
                logger.info(f"Fetched {len(profile.main_pages)} main pages")
            else:
                logger.warning(f"Failed to fetch pages: {response.status_code}")
                profile.main_pages = []
                
        except Exception as e:
            logger.error(f"Error fetching pages: {e}")
            profile.main_pages = []
    
    def _fetch_sitemap_url(self, profile: SiteProfile) -> None:
        """Try to detect sitemap URL."""
        common_sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/wp-sitemap.xml",
        ]
        
        for url in common_sitemap_urls:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200:
                    profile.sitemap_url = url
                    logger.info(f"Found sitemap: {url}")
                    return
            except:
                continue
        
        logger.info("No sitemap found")
        profile.sitemap_url = ""
    
    def analyze_content_themes(self, profile: SiteProfile) -> list[str]:
        """
        Analyze content and extract main themes using AI.
        
        Args:
            profile: SiteProfile instance
        
        Returns:
            List of content themes
        """
        # Extract all category and tag names
        themes = set()
        
        # Add categories
        for cat in profile.categories:
            themes.add(cat['name'])
        
        # Add top tags (by count)
        sorted_tags = sorted(profile.tags, key=lambda x: x['count'], reverse=True)
        for tag in sorted_tags[:20]:  # Top 20 tags
            themes.add(tag['name'])
        
        return list(themes)
    
    def get_existing_titles(self, profile: SiteProfile) -> list[str]:
        """
        Get list of existing post titles for anti-cannibalization.
        
        Args:
            profile: SiteProfile instance
        
        Returns:
            List of post titles
        """
        return [post['title'] for post in profile.recent_posts]
    
    def get_existing_keywords(self, profile: SiteProfile) -> set[str]:
        """
        Extract keywords from existing content.
        
        Args:
            profile: SiteProfile instance
        
        Returns:
            Set of keywords (lowercase)
        """
        keywords = set()
        
        # Add category names
        for cat in profile.categories:
            keywords.add(cat['name'].lower())
        
        # Add tag names
        for tag in profile.tags:
            keywords.add(tag['name'].lower())
        
        return keywords
