import pytest
import json
import logging
from unittest.mock import MagicMock, patch
import sys
import os

# Add the path to the src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import the module to test
from bedrock_agent.calendar_integrator import lambda_handler

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_calendar_integrator():
    with patch('bedrock_agent.calendar_integrator.CalendarIntegrator') as mock_integrator:
        # Create mock instance with check_availability method
        mock_instance = MagicMock()
        mock_instance.check_availability.return_value = {
            'date': '2023-09-18',
            'availableSlots': [
                {'startTime': '09:00', 'endTime': '10:00', 'duration': 60},
            ],
            'success': True
        }
        
        # Make the mock return our mock instance
        mock_integrator.return_value = mock_instance
        
        yield mock_integrator

def test_lambda_handler_with_string_event(mock_calendar_integrator):
    """Test lambda_handler with a string event that is valid JSON"""
    
    # Create a valid JSON string event
    event_dict = {
        'actionGroup': {'actionName': 'check_availability'},
        'parameters': {
            'date': '2023-09-18', 
            'calendar_provider': 'GOOGLE'
        }
    }
    event_string = json.dumps(event_dict)
    
    # Call the lambda handler with the string event
    result = lambda_handler(event_string, {})
    
    # Verify the mock was called
    mock_instance = mock_calendar_integrator.return_value
    mock_instance.check_availability.assert_called_once_with('2023-09-18', '09:00', '17:00')
    
    # Verify the result
    assert result['date'] == '2023-09-18'
    assert 'availableSlots' in result
    assert result['success'] is True

def test_lambda_handler_with_invalid_string_event(mock_calendar_integrator):
    """Test lambda_handler with a string event that is NOT valid JSON"""
    
    # Create an invalid JSON string event
    event_string = "this is not valid JSON"
    
    # Call the lambda handler with the invalid string event
    result = lambda_handler(event_string, {})
    
    # Verify error response
    assert result['success'] is False
    assert 'error' in result
    assert 'Invalid event format' in result['error']

def test_lambda_handler_with_string_event_missing_actiongroup(mock_calendar_integrator):
    """Test lambda_handler with a string event missing the actionGroup"""
    
    # Create a valid JSON string event but without actionGroup
    event_dict = {
        'parameters': {
            'date': '2023-09-18', 
            'calendar_provider': 'GOOGLE'
        }
    }
    event_string = json.dumps(event_dict)
    
    # Call the lambda handler with the string event
    result = lambda_handler(event_string, {})
    
    # Verify error response
    assert result['success'] is False
    assert 'error' in result
    assert 'Unknown action: None' in result['error']

def test_lambda_handler_raw_string_no_dict(mock_calendar_integrator):
    """Test lambda_handler with a string that's not even attempting to be JSON"""
    
    # Non-JSON string directly passed to lambda
    event_string = "2025-03-15T01:38:35.956Z"
    
    # Call the lambda handler with the string event
    result = lambda_handler(event_string, {})
    
    # Verify error response
    assert result['success'] is False
    assert 'error' in result
    assert 'Invalid event format' in result['error']
