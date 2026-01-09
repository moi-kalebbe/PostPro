"""
WordPress API Service for PostPro.
Handles post creation and media upload.
"""

import logging
import requests
from typing import Optional
from base64 import b64encode

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


class WordPressError(Exception):
    """Base WordPress error."""
    pass


class AuthenticationError(WordPressError):
    """WordPress authentication failed."""
    pass


class PublishError(WordPressError):
    """Failed to publish post."""
    pass


class WordPressService:
    """
    Service for interacting with WordPress REST API.
    """
    
    def __init__(self, site_url: str, username: str, app_password: str):
        """
        Initialize WordPress service.
        
        Args:
            site_url: Base WordPress URL (without trailing slash)
            username: WordPress username
            app_password: WordPress application password
        """
        self.site_url = site_url.rstrip('/')
        self.username = username
        self.app_password = app_password
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
    
    def _get_auth_header(self) -> dict:
        """Build Basic Auth header."""
        credentials = f"{self.username}:{self.app_password}"
        encoded = b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }
    
    def test_connection(self) -> tuple[bool, str]:
        """Test WordPress connection and authentication."""
        try:
            # Try to get current user
            response = requests.get(
                f"{self.site_url}/wp-json/wp/v2/users/me",
                headers=self._get_auth_header(),
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Connected as {user_data.get('name', 'Unknown')}"
            elif response.status_code == 401:
                return False, "Authentication failed. Check username and app password."
            elif response.status_code == 404:
                return False, "WordPress REST API not found. Is it enabled?"
            else:
                return False, f"Error: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"Connection failed: {str(e)}"
    
    def upload_media(
        self,
        image_data: bytes,
        filename: str,
        mime_type: str = "image/jpeg"
    ) -> dict:
        """
        Upload media to WordPress.
        
        Args:
            image_data: Raw image bytes
            filename: Filename for the upload
            mime_type: MIME type of the image
        
        Returns:
            dict with 'id' and 'source_url'
        """
        headers = {
            "Authorization": self._get_auth_header()["Authorization"],
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": mime_type,
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/media",
                headers=headers,
                data=image_data,
                timeout=60  # Longer timeout for upload
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "id": data["id"],
                    "source_url": data.get("source_url", ""),
                }
            else:
                logger.error(f"Media upload failed: {response.status_code} - {response.text}")
                raise PublishError(f"Media upload failed: {response.status_code}")
                
        except requests.RequestException as e:
            raise WordPressError(f"Media upload request failed: {e}")
    
    def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        meta_description: str = "",
        featured_image_id: Optional[int] = None,
        categories: Optional[list[int]] = None,
        tags: Optional[list[int]] = None,
    ) -> dict:
        """
        Create a WordPress post.
        
        Args:
            title: Post title
            content: Post content (HTML)
            status: 'draft' or 'publish'
            meta_description: SEO meta description (for Yoast/RankMath)
            featured_image_id: Media attachment ID for featured image
            categories: List of category IDs
            tags: List of tag IDs
        
        Returns:
            dict with 'id', 'link', 'edit_link'
        """
        payload = {
            "title": title,
            "content": content,
            "status": status,
        }
        
        if featured_image_id:
            payload["featured_media"] = featured_image_id
        
        if categories:
            payload["categories"] = categories
        
        if tags:
            payload["tags"] = tags
        
        # Add meta description for SEO plugins
        if meta_description:
            payload["meta"] = {
                "_yoast_wpseo_metadesc": meta_description,
                "rank_math_description": meta_description,
            }
        
        try:
            response = requests.post(
                f"{self.api_base}/posts",
                headers=self._get_auth_header(),
                json=payload,
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "id": data["id"],
                    "link": data.get("link", ""),
                    "edit_link": f"{self.site_url}/wp-admin/post.php?post={data['id']}&action=edit",
                }
            elif response.status_code == 401:
                raise AuthenticationError("Authentication failed")
            else:
                logger.error(f"Post creation failed: {response.status_code} - {response.text}")
                raise PublishError(f"Post creation failed: {response.status_code}")
                
        except requests.RequestException as e:
            raise WordPressError(f"Post creation request failed: {e}")
    
    def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        featured_image_id: Optional[int] = None,
    ) -> dict:
        """
        Update an existing WordPress post.
        
        Returns:
            dict with 'id', 'link', 'edit_link'
        """
        payload = {}
        
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if status is not None:
            payload["status"] = status
        if featured_image_id is not None:
            payload["featured_media"] = featured_image_id
        
        try:
            response = requests.post(
                f"{self.api_base}/posts/{post_id}",
                headers=self._get_auth_header(),
                json=payload,
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "id": data["id"],
                    "link": data.get("link", ""),
                    "edit_link": f"{self.site_url}/wp-admin/post.php?post={data['id']}&action=edit",
                }
            else:
                raise PublishError(f"Post update failed: {response.status_code}")
                
        except requests.RequestException as e:
            raise WordPressError(f"Post update request failed: {e}")
    
    def get_post(self, post_id: int) -> Optional[dict]:
        """Get a post by ID."""
        try:
            response = requests.get(
                f"{self.api_base}/posts/{post_id}",
                headers=self._get_auth_header(),
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except requests.RequestException:
            return None
    
    def delete_post(self, post_id: int, force: bool = False) -> dict:
        """
        Delete a WordPress post.
        
        Args:
            post_id: WordPress post ID
            force: If True, permanently delete. If False, move to trash.
        
        Returns:
            dict with 'success', 'message', and optionally 'deleted_post'
        """
        try:
            # WordPress REST API delete endpoint
            # ?force=true permanently deletes, otherwise moves to trash
            url = f"{self.api_base}/posts/{post_id}"
            if force:
                url += "?force=true"
            
            response = requests.delete(
                url,
                headers=self._get_auth_header(),
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message": "Post deleted" if force else "Post moved to trash",
                    "deleted_post": data,
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "message": "Post not found in WordPress",
                }
            elif response.status_code == 401:
                raise AuthenticationError("Authentication failed")
            else:
                logger.error(f"Post deletion failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Deletion failed: {response.status_code}",
                }
                
        except requests.RequestException as e:
            logger.error(f"Post deletion request failed: {e}")
            return {
                "success": False,
                "message": f"Connection error: {str(e)}",
            }

    def get_categories(self) -> list[dict]:
        """
        Get all categories.
        """
        try:
            items = []
            page = 1
            while True:
                response = requests.get(
                    f"{self.api_base}/categories",
                    headers=self._get_auth_header(),
                    params={"per_page": 100, "page": page, "hide_empty": False},
                    timeout=DEFAULT_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if not data:
                        break
                    items.extend(data)
                    if len(data) < 100:
                        break
                    page += 1
                else:
                    break
            
            return items
        except requests.RequestException as e:
            logger.error(f"Failed to fetch categories: {e}")
            return []

    def get_tags(self) -> list[dict]:
        """
        Get all tags (limit to first 1000).
        """
        try:
            items = []
            page = 1
            while page <= 10:
                response = requests.get(
                    f"{self.api_base}/tags",
                    headers=self._get_auth_header(),
                    params={"per_page": 100, "page": page, "hide_empty": False},
                    timeout=DEFAULT_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if not data:
                        break
                    items.extend(data)
                    if len(data) < 100:
                        break
                    page += 1
                else:
                    break
            
            return items
        except requests.RequestException as e:
            logger.error(f"Failed to fetch tags: {e}")
            return []

    def get_recent_posts(self, limit: int = 20) -> list[dict]:
        """
        Get recent posts for context.
        """
        try:
            response = requests.get(
                f"{self.api_base}/posts",
                headers=self._get_auth_header(),
                params={"per_page": limit, "status": "publish"},
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch recent posts: {e}")
            return []

    def get_site_info(self) -> dict:
        """
        Get site basic info.
        """
        try:
            response = requests.get(
                f"{self.site_url}/wp-json",
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
        except requests.RequestException as e:
            logger.error(f"Failed to fetch site info: {e}")
            return {}


def send_to_postpro_plugin(
    site_url: str,
    license_key: str,
    post_data: dict,
    idempotency_key: str,
) -> dict:
    """
    Send post to WordPress via PostPro plugin webhook.
    
    Args:
        site_url: WordPress site URL
        license_key: PostPro license key
        post_data: Post data dict with title, content, meta_description, featured_image_url
        idempotency_key: Unique key to prevent duplicates
    
    Returns:
        dict with 'success', 'post_id', 'edit_url'
    """
    endpoint = f"{site_url.rstrip('/')}/wp-json/postpro/v1/receive-post"
    
    headers = {
        "Content-Type": "application/json",
        "X-License-Key": str(license_key),
        "X-Idempotency-Key": idempotency_key,
    }
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=post_data,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "post_id": data.get("post_id"),
                "edit_url": data.get("edit_url", ""),
            }
        else:
            logger.error(f"PostPro plugin error: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e),
        }
