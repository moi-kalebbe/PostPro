"""
Site Profile Service.
Handles synchronization and analysis of WordPress site content.
"""

import logging
import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from apps.projects.models import Project
from apps.automation.models import SiteProfile
from .wordpress import WordPressService

logger = logging.getLogger(__name__)


class SiteProfileService:
    """
    Service for managing site profiles (content analysis, categories, tags).
    """
    
    def __init__(self, project: Project):
        self.project = project
        self.wp_service = None
        
        # Initialize WordPress service if credentials exist
        password = project.get_wordpress_password()
        if password and project.wordpress_username:
            self.wp_service = WordPressService(
                site_url=project.wordpress_url,
                username=project.wordpress_username,
                app_password=password
            )
    
    def get_or_create_profile(self) -> SiteProfile:
        """
        Get existing profile or create a new empty one.
        """
        profile, created = SiteProfile.objects.get_or_create(
            project=self.project,
            defaults={
                'site_name': self.project.name,
                'home_url': self.project.wordpress_url,
            }
        )
        return profile
    
    def sync_profile(self) -> SiteProfile:
        """
        Fetch data from WordPress and update the profile.
        """
        if not self.wp_service:
            logger.warning(f"Cannot sync profile for project {self.project.id}: No credentials")
            return self.get_or_create_profile()
        
        profile = self.get_or_create_profile()
        
        try:
            # Fetch data
            logger.info(f"Syncing profile for project {self.project.id}...")
            
            site_info = self.wp_service.get_site_info()
            categories = self.wp_service.get_categories()
            tags = self.wp_service.get_tags()
            recent_posts = self.wp_service.get_recent_posts(limit=20)
            
            # Update metadata
            if site_info:
                profile.site_name = site_info.get('name', profile.site_name)
                profile.site_description = site_info.get('description', '')
                profile.home_url = site_info.get('url', profile.home_url)
            
            # Process categories (simplify structure)
            profile.categories = [
                {
                    'id': c['id'],
                    'name': c['name'],
                    'slug': c['slug'],
                    'count': c['count'],
                    'description': c.get('description', '')
                }
                for c in categories
            ]
            
            # Process tags
            profile.tags = [
                {
                    'id': t['id'],
                    'name': t['name'],
                    'slug': t['slug'],
                    'count': t['count']
                }
                for t in tags
            ]
            
            # Process recent posts (summary)
            profile.recent_posts = [
                {
                    'id': p['id'],
                    'title': p['title']['rendered'],
                    'date': p['date'],
                    'link': p['link'],
                    'categories': p['categories'],
                    'tags': p['tags']
                }
                for p in recent_posts
            ]
            
            profile.last_synced_at = timezone.now()
            profile.save()
            
            logger.info(f"Profile synced for {self.project.name}")
            return profile
            
        except Exception as e:
            logger.error(f"Error syncing profile: {e}")
            raise
    
    def parse_sitemap(self, sitemap_url: str = None) -> list[dict]:
        """
        Parse sitemap.xml to collect all post URLs and titles.
        Returns list of {'url': ..., 'title': ...} for anti-cannibalization.
        """
        if not sitemap_url:
            # Try common sitemap locations
            base_url = self.project.wordpress_url.rstrip('/')
            sitemap_urls = [
                f"{base_url}/sitemap.xml",
                f"{base_url}/sitemap_index.xml",
                f"{base_url}/post-sitemap.xml",
                f"{base_url}/wp-sitemap.xml",
                f"{base_url}/wp-sitemap-posts-post-1.xml",
            ]
        else:
            sitemap_urls = [sitemap_url]
        
        all_posts = []
        
        for url in sitemap_urls:
            try:
                response = requests.get(url, timeout=15)
                if response.status_code != 200:
                    continue
                    
                root = ET.fromstring(response.content)
                
                # Handle sitemap index (contains links to other sitemaps)
                ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                # Check for sitemap index
                sitemaps = root.findall('.//sm:sitemap/sm:loc', ns)
                if sitemaps:
                    for sm in sitemaps:
                        if 'post' in sm.text.lower():
                            all_posts.extend(self.parse_sitemap(sm.text))
                    continue
                
                # Parse regular sitemap
                urls = root.findall('.//sm:url/sm:loc', ns)
                for url_elem in urls:
                    post_url = url_elem.text
                    if post_url and '/page/' not in post_url:  # Skip paginated
                        all_posts.append({
                            'url': post_url,
                            'title': ''  # Will be fetched separately if needed
                        })
                
                if all_posts:
                    logger.info(f"Parsed {len(all_posts)} URLs from sitemap: {url}")
                    break  # Found posts, no need to try other URLs
                    
            except Exception as e:
                logger.debug(f"Error parsing sitemap {url}: {e}")
                continue
        
        return all_posts
    
    def get_all_post_titles(self) -> list[str]:
        """
        Get all post titles from the site for anti-cannibalization.
        Combines sitemap URLs with API-fetched recent posts.
        """
        titles = []
        
        # Get from sitemap
        sitemap_posts = self.parse_sitemap()
        
        # For each sitemap URL, try to get title from WP API
        if sitemap_posts and self.wp_service:
            # Batch fetch titles from WP API (more efficient)
            try:
                # Get all posts up to 100 (higher limit than default 20)
                all_posts = self.wp_service.get_recent_posts(limit=100)
                titles = [p['title']['rendered'] for p in all_posts if p.get('title')]
                logger.info(f"Fetched {len(titles)} post titles from WP API")
            except Exception as e:
                logger.warning(f"Error fetching all posts: {e}")
        
        # If still not enough, extract from sitemap URLs
        if len(titles) < 50 and sitemap_posts:
            for post in sitemap_posts:
                # Extract title from URL slug
                url = post['url'].rstrip('/')
                slug = url.split('/')[-1]
                if slug:
                    title = slug.replace('-', ' ').title()
                    titles.append(title)
        
        return list(set(titles))  # Remove duplicates
