"""
Site Profile Service.
Handles synchronization and analysis of WordPress site content.
"""

import logging
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
