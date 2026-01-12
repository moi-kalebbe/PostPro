import base64
import uuid
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class SupabaseStorageService:
    @staticmethod
    def _get_headers(content_type="image/jpeg"):
        return {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": content_type,
            "x-upsert": "true"
        }

    @staticmethod
    def _get_upload_endpoint(bucket, filename):
        return f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{filename}"

    @staticmethod
    def _get_public_url(bucket, filename):
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{filename}"

    @classmethod
    def upload_base64_image(cls, base64_data: str, filename: str, bucket: str = "post-images") -> str:
        """
        Uploads a base64 string image to Supabase and returns the public URL.
        """
        try:
            logger.info("Processing base64 image data for upload")
            
            # Handle data URI scheme if present
            if "," in base64_data:
                header, encoded = base64_data.split(",", 1)
            else:
                header = ""
                encoded = base64_data
                
            image_content = base64.b64decode(encoded)
            
            # Determine extension from header or default to jpg
            ext = "png" if "png" in header else "jpg"
            if not filename.endswith(f".{ext}"):
                filename = f"{filename}.{ext}"
                
            # Upload
            endpoint = cls._get_upload_endpoint(bucket, filename)
            headers = cls._get_headers(f"image/{ext}")
            
            response = requests.post(
                endpoint,
                data=image_content,
                headers=headers,
                timeout=30
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Supabase Upload Failed: {response.status_code} - {response.text}")
                raise Exception(f"Supabase upload failed: {response.text}")
                
            public_url = cls._get_public_url(bucket, filename)
            logger.info(f"Successfully uploaded base64 to Supabase: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload base64 image: {e}")
            raise

    @classmethod
    def upload_from_url(cls, source_url: str, filename: str, bucket: str = "post-images") -> str:
        """
        Downloads image from source_url and uploads to Supabase.
        """
        try:
            logger.info(f"Downloading image from {source_url[:100]}...")
            
            # Use browser-like headers to bypass hotlink protection
            download_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/png,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
                "Referer": source_url,  # Some sites check referer
            }
            
            response = requests.get(source_url, headers=download_headers, timeout=30, allow_redirects=True)
            if response.status_code != 200:
                raise Exception(f"Failed to download source image: HTTP {response.status_code}")
                
            image_content = response.content
            
            # Validate it's actually an image
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image') and len(image_content) < 1000:
                raise Exception(f"Response doesn't appear to be an image: {content_type}")
            
            # Determine extension
            ext = "png" if "png" in source_url.lower() else "jpg"
            if not filename.endswith(f".{ext}"):
                filename = f"{filename}.{ext}"
                
            # Upload
            endpoint = cls._get_upload_endpoint(bucket, filename)
            headers = cls._get_headers(f"image/{ext}")
            
            response = requests.post(
                endpoint,
                data=image_content,
                headers=headers,
                timeout=30
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Supabase Upload Failed: {response.status_code} - {response.text}")
                raise Exception(f"Supabase upload failed: {response.text}")
                
            public_url = cls._get_public_url(bucket, filename)
            logger.info(f"Successfully bridged image to Supabase: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to bridge image: {e}")
            raise
