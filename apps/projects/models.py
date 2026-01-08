"""
Project model for PostPro.
Represents a WordPress site connected to the platform.
"""

import uuid
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken


class Project(models.Model):
    """
    WordPress project connected to PostPro.
    Each project represents a WordPress site with its own settings.
    """
    
    class Tone(models.TextChoices):
        FORMAL = 'formal', 'Formal'
        CASUAL = 'casual', 'Casual'
        TECHNICAL = 'technical', 'Technical'
    
    class ImageStyle(models.TextChoices):
        PHOTOGRAPHIC = 'photographic', 'Photographic'
        ILLUSTRATION = 'illustration', 'Illustration'
        MINIMALIST = 'minimalist', 'Minimalist'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.CASCADE,
        related_name='projects'
    )
    
    # Basic info
    name = models.CharField(max_length=255)
    wordpress_url = models.URLField(max_length=500)
    license_key = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    
    # AI model overrides (use agency defaults if empty)
    text_model = models.CharField(max_length=100, blank=True, null=True)
    image_model = models.CharField(max_length=100, blank=True, null=True)
    
    # Content settings
    tone = models.CharField(
        max_length=20,
        choices=Tone.choices,
        default=Tone.CASUAL
    )
    image_style = models.CharField(
        max_length=20,
        choices=ImageStyle.choices,
        default=ImageStyle.PHOTOGRAPHIC
    )
    
    # WordPress credentials (encrypted)
    wordpress_username = models.CharField(max_length=100, blank=True)
    wordpress_app_password_encrypted = models.TextField(blank=True, null=True)
    
    # Stats
    total_posts_generated = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.wordpress_url})"
    
    def _get_fernet(self):
        """Get Fernet instance for encryption."""
        key = settings.ENCRYPTION_KEY.encode() if settings.ENCRYPTION_KEY else Fernet.generate_key()
        return Fernet(key)
    
    def set_wordpress_password(self, password: str):
        """Encrypt and store WordPress app password."""
        if password:
            fernet = self._get_fernet()
            self.wordpress_app_password_encrypted = fernet.encrypt(password.encode()).decode()
        else:
            self.wordpress_app_password_encrypted = None
    
    def get_wordpress_password(self) -> str | None:
        """Decrypt and return WordPress app password."""
        if not self.wordpress_app_password_encrypted:
            return None
        try:
            fernet = self._get_fernet()
            return fernet.decrypt(self.wordpress_app_password_encrypted.encode()).decode()
        except InvalidToken:
            return None
    
    def get_text_model(self) -> str:
        """Get text model (project override or agency default)."""
        return self.text_model or self.agency.default_text_model
    
    def get_image_model(self) -> str:
        """Get image model (project override or agency default)."""
        return self.image_model or self.agency.default_image_model
    
    def regenerate_license_key(self):
        """Generate a new license key."""
        self.license_key = uuid.uuid4()
        self.save(update_fields=['license_key'])
    
    def increment_posts(self, count: int = 1):
        """Increment post counter."""
        self.total_posts_generated += count
        self.save(update_fields=['total_posts_generated'])
