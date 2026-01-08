"""
User model for PostPro.
Extends AbstractUser with multi-tenant role support.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    
    Roles:
    - super_admin: Platform administrator (sees all)
    - agency_owner: Agency owner (sees own agency data)
    - agency_member: Agency team member (limited access)
    """
    
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        AGENCY_OWNER = 'agency_owner', 'Agency Owner'
        AGENCY_MEMBER = 'agency_member', 'Agency Member'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AGENCY_MEMBER
    )
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN
    
    @property
    def is_agency_owner(self):
        return self.role == self.Role.AGENCY_OWNER
    
    @property
    def is_agency_member(self):
        return self.role == self.Role.AGENCY_MEMBER
    
    def can_access_agency(self, agency):
        """Check if user can access a specific agency."""
        if self.is_super_admin:
            return True
        return self.agency_id == agency.id
    
    def can_manage_agency(self, agency):
        """Check if user can manage (edit) a specific agency."""
        if self.is_super_admin:
            return True
        return self.is_agency_owner and self.agency_id == agency.id
