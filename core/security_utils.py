"""
Security utilities for OWASP hardening.

Provides functions for:
- File upload validation
- Input sanitization
- Security decorators
"""

import os
import mimetypes
from django.core.exceptions import ValidationError
from django.conf import settings
import logging

logger = logging.getLogger('django.security')


def validate_file_upload(file_obj):
    """
    OWASP #5: Security Misconfiguration & #10: SSRF Prevention
    Validate file uploads for safety.
    
    Args:
        file_obj: Django UploadedFile object
        
    Raises:
        ValidationError: If file is invalid
    """
    if not file_obj:
        raise ValidationError('No file provided.')
    
    # Check file size
    if file_obj.size > settings.MAX_FILE_SIZE:
        raise ValidationError(
            f'File size exceeds maximum limit of '
            f'{settings.MAX_FILE_SIZE // (1024 * 1024)}MB.'
        )
    
    # Check file extension
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        allowed = ', '.join(settings.ALLOWED_FILE_EXTENSIONS)
        raise ValidationError(
            f'File type {ext} not allowed. Allowed types: {allowed}'
        )
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(file_obj.name)
    allowed_mimes = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
    ]
    
    if mime_type and mime_type not in allowed_mimes:
        raise ValidationError(
            f'MIME type {mime_type} not allowed.'
        )
    
    # Log file upload attempt
    logger.info(
        f'File upload validation passed: {file_obj.name} '
        f'({file_obj.size} bytes)'
    )
    
    return file_obj


def sanitize_string(value):
    """
    OWASP #3: Injection Prevention
    Basic sanitization of user input strings.
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return value
    
    # Remove control characters
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
    
    # Strip leading/trailing whitespace
    value = value.strip()
    
    return value


def validate_pagination_input(page, page_size=20):
    """
    OWASP #1: Broken Access Control Prevention
    Validate pagination parameters to prevent abuse.
    
    Args:
        page: Page number
        page_size: Items per page
        
    Returns:
        Tuple of (valid_page, valid_page_size)
    """
    max_page_size = 100
    
    try:
        page = int(page) if page else 1
        page = max(1, page)  # Ensure positive
    except (ValueError, TypeError):
        page = 1
    
    try:
        page_size = int(page_size) if page_size else 20
        page_size = min(page_size, max_page_size)  # Cap page size
        page_size = max(1, page_size)  # Ensure at least 1
    except (ValueError, TypeError):
        page_size = 20
    
    return page, page_size


class RateLimitMixin:
    """
    OWASP #7: Authentication Failure Prevention
    Mixin for rate limiting on views.
    """
    ratelimit_key = 'ip'
    ratelimit_rate = '10/h'  # 10 requests per hour
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SQLInjectionPrevention:
    """
    OWASP #3: Injection Prevention
    Helper class for SQL injection prevention.
    Always use Django ORM queryset methods instead of raw SQL.
    """
    
    @staticmethod
    def safe_filter(**kwargs):
        """
        Use this pattern for safe database queries:
        
        Example:
            from django.contrib.auth.models import User
            User.objects.filter(username='safe_value')
        """
        return kwargs


# Example of safe query patterns
"""
SAFE PATTERNS:
1. ORM Queries (Recommended):
   User.objects.filter(username=username)
   
2. Parameterized Queries (If raw SQL needed):
   User.objects.raw('SELECT * FROM auth_user WHERE username = %s', [username])
   
UNSAFE PATTERNS TO AVOID:
1. String formatting:
   User.objects.raw(f'SELECT * FROM auth_user WHERE username = {username}')
   
2. String concatenation:
   query = 'SELECT * FROM auth_user WHERE username = ' + username
"""
