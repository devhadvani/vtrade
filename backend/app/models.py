# models.py
from django.db import models
from django.utils import timezone
import datetime
import logging

logger = logging.getLogger(__name__)

class FyersToken(models.Model):
    """
    Model to store a single Fyers API token for the entire application
    """
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fyers_token'
    
    @classmethod
    def get_valid_token(cls):
        """
        Get a valid token or None if no valid token exists
        """
        now = timezone.now()
        # Add a 5-minute buffer to avoid edge cases
        buffer_time = now + datetime.timedelta(minutes=5)
        
        try:
            # Try to get a valid token
            token = cls.objects.filter(
                expires_at__gt=buffer_time
            ).order_by('-created_at').first()
            
            if token:
                return token.access_token
            return None
        except Exception as e:
            logger.exception(f"Error getting valid token: {e}")
            return None