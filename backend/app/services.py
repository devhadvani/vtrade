# services.py
from django.utils import timezone
from django.conf import settings
import datetime
import logging
from fyers_apiv3 import fyersModel
from .models import FyersToken

logger = logging.getLogger(__name__)

class FyersTokenService:
    """
    Service for managing Fyers API tokens
    """
    
    @classmethod
    def initialize_token(cls, auth_code):
        """
        Initialize a token using the authorization code
        """
        try:
            client_id = settings.FYERS_CLIENT_ID
            secret_key = settings.FYERS_SECRET_KEY
            redirect_uri = settings.FYERS_REDIRECT_URI
            
            session = fyersModel.SessionModel(
                client_id=client_id,
                secret_key=secret_key,
                redirect_uri=redirect_uri,
                response_type="code",
                grant_type="authorization_code"
            )
            
            session.set_token(auth_code)
            response = session.generate_token()

            print("in the init",response)
            
            if response.get('s') == 'ok':
                # token_data = response.get('data', {})
                access_token = response.get('access_token')
                refresh_token = response.get('refresh_token')
                
                # Calculate token expiry (typically 24 hours from now)
                expires_in = response.get('expires_in', 86400)  # Default to 24 hours
                expires_at = timezone.now() + datetime.timedelta(seconds=expires_in)
                
                # Create new token record
                token = FyersToken.objects.create(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at
                )
                
                logger.info(f"Successfully initialized token, expires at {expires_at}")
                return token.access_token
            else:
                logger.error(f"Failed to initialize token: {response}")
                return None
        except Exception as e:
            logger.exception(f"Error initializing token: {e}")
            return None
    
    @classmethod
    def refresh_token(cls, refresh_token):
        """
        Refresh an access token using a refresh token
        """
        try:
            client_id = settings.FYERS_CLIENT_ID
            
            session = fyersModel.SessionModel(
                client_id=client_id,
                refresh_token=refresh_token
            )
            
            response = session.refresh_token()
            
            if response.get('s') == 'ok':
                token_data = response.get('data', {})
                access_token = token_data.get('access_token')
                new_refresh_token = token_data.get('refresh_token', refresh_token)
                
                # Calculate token expiry (typically 24 hours from now)
                expires_in = token_data.get('expires_in', 86400)  # Default to 24 hours
                expires_at = timezone.now() + datetime.timedelta(seconds=expires_in)
                
                # Create new token record
                token = FyersToken.objects.create(
                    access_token=access_token,
                    refresh_token=new_refresh_token,
                    expires_at=expires_at
                )
                
                logger.info(f"Successfully refreshed token, expires at {expires_at}")
                return token.access_token
            else:
                logger.error(f"Failed to refresh token: {response}")
                return None
        except Exception as e:
            logger.exception(f"Error refreshing token: {e}")
            return None
    
    @classmethod
    def get_access_token(cls):
        """
        Get a valid access token, refreshing if necessary
        """
        # Try to get an existing valid token
        token = FyersToken.get_valid_token()
        if token:
            return token
        
        # No valid token, try to refresh using the most recent refresh token
        try:
            latest_token = FyersToken.objects.order_by('-created_at').first()
            if latest_token and latest_token.refresh_token:
                new_token = cls.refresh_token(latest_token.refresh_token)
                if new_token:
                    return new_token
        except Exception as e:
            logger.exception(f"Error in get_access_token: {e}")
        
        # If we get here, we need manual reauthorization
        logger.error("No valid token available and refresh failed")
        return None