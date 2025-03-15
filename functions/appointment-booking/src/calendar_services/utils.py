# Fallback utils module for calendar_services
import os
import logging

logger = logging.getLogger(__name__)

def get_google_credentials():
    """
    Reconstruct Google service account credentials from environment variables.
    Fallback version directly in calendar_services directory.
    
    Returns:
        Dict: A dictionary with the service account credentials structure
    """
    logger.info("Using fallback get_google_credentials from calendar_services.utils")
    
    # Check if all required environment variables are present
    required_keys = [
        "GOOGLE_CALENDAR_TYPE",
        "GOOGLE_CALENDAR_PROJECT_ID",
        "GOOGLE_CALENDAR_PRIVATE_KEY_ID",
        "GOOGLE_CALENDAR_PRIVATE_KEY",
        "GOOGLE_CALENDAR_CLIENT_EMAIL",
        "GOOGLE_CALENDAR_CLIENT_ID",
    ]
    
    # If any required variables are missing, log and raise an exception
    missing_keys = [key for key in required_keys if not os.environ.get(key)]
    if missing_keys:
        error_msg = f"Missing required Google Calendar environment variables: {', '.join(missing_keys)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Reconstruct service account JSON
    credentials = {
        "type": os.environ.get("GOOGLE_CALENDAR_TYPE"),
        "project_id": os.environ.get("GOOGLE_CALENDAR_PROJECT_ID"),
        "private_key_id": os.environ.get("GOOGLE_CALENDAR_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("GOOGLE_CALENDAR_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.environ.get("GOOGLE_CALENDAR_CLIENT_EMAIL"),
        "client_id": os.environ.get("GOOGLE_CALENDAR_CLIENT_ID"),
        "auth_uri": os.environ.get("GOOGLE_CALENDAR_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": os.environ.get("GOOGLE_CALENDAR_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": os.environ.get(
            "GOOGLE_CALENDAR_AUTH_PROVIDER_X509_CERT_URL", 
            "https://www.googleapis.com/oauth2/v1/certs"
        ),
        "client_x509_cert_url": os.environ.get("GOOGLE_CALENDAR_CLIENT_X509_CERT_URL"),
        "universe_domain": os.environ.get("GOOGLE_CALENDAR_UNIVERSE_DOMAIN", "googleapis.com"),
    }
    
    logger.debug("Successfully loaded Google Calendar credentials from environment variables")
    return credentials
