import pytest
import os
from unittest.mock import patch
import sys
import os as os_module

# Add the path to the src directory
sys.path.insert(0, os_module.path.abspath(os_module.path.join(os_module.path.dirname(__file__), '../../src')))

# Import the module to test
from utils.google_credentials import get_google_credentials

@pytest.fixture
def setup_env_vars():
    """Setup test environment variables"""
    # Save original environment
    original_env = os_module.environ.copy()
    
    # Set up test environment variables
    os_module.environ['GOOGLE_CALENDAR_TYPE'] = 'service_account'
    os_module.environ['GOOGLE_CALENDAR_PROJECT_ID'] = 'test-project'
    os_module.environ['GOOGLE_CALENDAR_PRIVATE_KEY_ID'] = 'test-key-id'
    os_module.environ['GOOGLE_CALENDAR_PRIVATE_KEY'] = '-----BEGIN PRIVATE KEY-----\\nTEST_KEY\\n-----END PRIVATE KEY-----\\n'
    os_module.environ['GOOGLE_CALENDAR_CLIENT_EMAIL'] = 'test@test-project.iam.gserviceaccount.com'
    os_module.environ['GOOGLE_CALENDAR_CLIENT_ID'] = '123456789'
    os_module.environ['GOOGLE_CALENDAR_AUTH_URI'] = 'https://accounts.google.com/o/oauth2/auth'
    os_module.environ['GOOGLE_CALENDAR_TOKEN_URI'] = 'https://oauth2.googleapis.com/token'
    os_module.environ['GOOGLE_CALENDAR_AUTH_PROVIDER_X509_CERT_URL'] = 'https://www.googleapis.com/oauth2/v1/certs'
    os_module.environ['GOOGLE_CALENDAR_CLIENT_X509_CERT_URL'] = 'https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com'
    os_module.environ['GOOGLE_CALENDAR_UNIVERSE_DOMAIN'] = 'googleapis.com'
    
    yield
    
    # Restore original environment
    os_module.environ.clear()
    os_module.environ.update(original_env)

def test_get_google_credentials(setup_env_vars):
    """Test that credentials are correctly loaded from environment variables"""
    # Get credentials
    credentials = get_google_credentials()
    
    # Verify credentials structure
    assert credentials['type'] == 'service_account'
    assert credentials['project_id'] == 'test-project'
    assert credentials['private_key_id'] == 'test-key-id'
    assert credentials['private_key'] == '-----BEGIN PRIVATE KEY-----\nTEST_KEY\n-----END PRIVATE KEY-----\n'
    assert credentials['client_email'] == 'test@test-project.iam.gserviceaccount.com'
    assert credentials['client_id'] == '123456789'
    assert credentials['auth_uri'] == 'https://accounts.google.com/o/oauth2/auth'
    assert credentials['token_uri'] == 'https://oauth2.googleapis.com/token'
    assert credentials['auth_provider_x509_cert_url'] == 'https://www.googleapis.com/oauth2/v1/certs'
    assert credentials['client_x509_cert_url'] == 'https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com'
    assert credentials['universe_domain'] == 'googleapis.com'
    
    # Verify that newlines are properly formatted
    assert '\n' in credentials['private_key']
    assert '\\n' not in credentials['private_key']

@pytest.mark.parametrize("missing_key", [
    'GOOGLE_CALENDAR_TYPE',
    'GOOGLE_CALENDAR_PROJECT_ID',
    'GOOGLE_CALENDAR_PRIVATE_KEY_ID',
    'GOOGLE_CALENDAR_PRIVATE_KEY',
    'GOOGLE_CALENDAR_CLIENT_EMAIL',
    'GOOGLE_CALENDAR_CLIENT_ID'
])
def test_missing_required_env_vars(setup_env_vars, missing_key):
    """Test that an error is raised when required variables are missing"""
    # Remove one required environment variable
    del os_module.environ[missing_key]
    
    # Expect a ValueError when getting credentials
    with pytest.raises(ValueError) as excinfo:
        get_google_credentials()
    
    # Verify the error message mentions the missing key
    assert missing_key in str(excinfo.value)
