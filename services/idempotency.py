"""
Idempotency Service for PostPro.
Prevents duplicate operations using unique keys.
"""

import hashlib
import logging
from typing import Optional
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class IdempotencyError(Exception):
    """Base idempotency error."""
    pass


class KeyAlreadyReservedError(IdempotencyError):
    """Key is already reserved by another process."""
    pass


class KeyAlreadyCompletedError(IdempotencyError):
    """Key has already completed successfully."""
    def __init__(self, message: str, metadata: dict = None):
        super().__init__(message)
        self.metadata = metadata or {}


def make_key(scope: str, *parts) -> str:
    """
    Generate a SHA256 hash key from scope and parts.
    
    Args:
        scope: Category like 'wordpress_publish'
        *parts: Variable parts to include in hash
    
    Returns:
        64-char hex digest
    """
    data = f"{scope}:" + ":".join(str(p) for p in parts)
    return hashlib.sha256(data.encode()).hexdigest()


def reserve_key(
    scope: str,
    key_hash: str,
    project_id,
    post_id=None,
    metadata: dict = None,
):
    """
    Reserve an idempotency key.
    
    Args:
        scope: Key scope ('wordpress_publish', etc.)
        key_hash: The hash key
        project_id: Associated project UUID
        post_id: Optional associated post UUID
        metadata: Optional metadata dict
    
    Returns:
        IdempotencyKey instance
    
    Raises:
        KeyAlreadyReservedError: If key is already reserved
        KeyAlreadyCompletedError: If key already completed
    """
    from apps.automation.models import IdempotencyKey
    
    with transaction.atomic():
        # Check if key exists
        existing = IdempotencyKey.objects.select_for_update().filter(
            key_hash=key_hash
        ).first()
        
        if existing:
            if existing.status == IdempotencyKey.Status.COMPLETED:
                raise KeyAlreadyCompletedError(
                    "Operation already completed",
                    metadata=existing.metadata
                )
            
            if existing.status == IdempotencyKey.Status.RESERVED:
                # Check if it's stale (more than 30 minutes old)
                age = timezone.now() - existing.created_at
                if age.total_seconds() < 1800:  # 30 minutes
                    raise KeyAlreadyReservedError("Key is reserved by another process")
                
                # Stale reservation, take over
                logger.warning(f"Taking over stale idempotency key: {key_hash[:16]}")
                existing.delete()
        
        # Create new reservation
        return IdempotencyKey.objects.create(
            scope=scope,
            key_hash=key_hash,
            project_id=project_id,
            post_id=post_id,
            status=IdempotencyKey.Status.RESERVED,
            metadata=metadata or {},
        )


def complete_key(key_hash: str, metadata: dict = None):
    """
    Mark idempotency key as completed.
    
    Args:
        key_hash: The hash key
        metadata: Optional metadata to store
    """
    from apps.automation.models import IdempotencyKey
    
    IdempotencyKey.objects.filter(key_hash=key_hash).update(
        status=IdempotencyKey.Status.COMPLETED,
        completed_at=timezone.now(),
        metadata=metadata or {},
    )


def fail_key(key_hash: str, error: str = None):
    """
    Mark idempotency key as failed.
    
    Args:
        key_hash: The hash key
        error: Optional error message
    """
    from apps.automation.models import IdempotencyKey
    
    key = IdempotencyKey.objects.filter(key_hash=key_hash).first()
    if key:
        key.fail(error)


def check_key_status(key_hash: str) -> Optional[dict]:
    """
    Check the status of an idempotency key.
    
    Returns:
        Dict with 'status' and 'metadata' if key exists, None otherwise
    """
    from apps.automation.models import IdempotencyKey
    
    key = IdempotencyKey.objects.filter(key_hash=key_hash).first()
    if key:
        return {
            "status": key.status,
            "metadata": key.metadata,
            "created_at": key.created_at,
            "completed_at": key.completed_at,
        }
    return None


def release_key(key_hash: str):
    """
    Delete an idempotency key (for cleanup).
    Use with caution.
    """
    from apps.automation.models import IdempotencyKey
    
    IdempotencyKey.objects.filter(key_hash=key_hash).delete()


class IdempotencyGuard:
    """
    Context manager for idempotent operations.
    
    Usage:
        with IdempotencyGuard('wordpress_publish', project_id, post_id) as guard:
            if guard.already_completed:
                return guard.metadata
            # ... do work ...
            guard.complete({'post_id': 123})
    """
    
    def __init__(self, scope: str, project_id, *key_parts, post_id=None):
        self.scope = scope
        self.project_id = project_id
        self.post_id = post_id
        self.key_hash = make_key(scope, project_id, *key_parts)
        self.key_instance = None
        self.already_completed = False
        self.metadata = {}
    
    def __enter__(self):
        try:
            self.key_instance = reserve_key(
                scope=self.scope,
                key_hash=self.key_hash,
                project_id=self.project_id,
                post_id=self.post_id,
            )
        except KeyAlreadyCompletedError as e:
            self.already_completed = True
            self.metadata = e.metadata
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An exception occurred, mark failed
            if self.key_instance:
                fail_key(self.key_hash, str(exc_val))
        
        return False  # Don't suppress exceptions
    
    def complete(self, metadata: dict = None):
        """Mark operation as complete with metadata."""
        self.metadata = metadata or {}
        complete_key(self.key_hash, self.metadata)
