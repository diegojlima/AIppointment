import pytest
import json
import boto3
import os
from unittest.mock import MagicMock, patch
# Removed moto import as it's not being used
from datetime import datetime, timedelta

# Add the path to the src directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import the module to test
from bedrock_agent.calendar_integrator import CalendarIntegrator, lambda_handler

@pytest.fixture
def mock_calendar_integration():
    # Mock the import_calendar_integration function
    with patch('bedrock_agent.calendar_integrator.import_calendar_integration') as mock_import:
        # Create mock classes for CalendarIntegration and CalendarProvider
        mock_calendar_integration = MagicMock()
        mock_calendar_provider = MagicMock()
        
        # Configure the mock provider
        mock_provider_instance = MagicMock()
        mock_provider_instance.value = 'GOOGLE'
        mock_calendar_provider.return_value = mock_provider_instance
        
        # Configure the mock calendar integration instance
        mock_calendar_instance = MagicMock()
        mock_calendar_integration.return_value = mock_calendar_instance
        
        # Set up mock return values
        mock_calendar_instance.check_availability.return_value = [
            {"start": "2023-09-18T09:00:00", "end": "2023-09-18T10:00:00"},
            {"start": "2023-09-18T10:00:00", "end": "2023-09-18T11:00:00"}
        ]
        
        mock_calendar_instance.get_next_available_slot.return_value = {
            "start": "2023-09-18T09:00:00", 
            "end": "2023-09-18T10:00:00"
        }
        
        mock_calendar_instance.book_appointment.return_value = {
            "success": True, 
            "appointment_id": "test-calendar-event-1",
            "appointment_details": {"htmlLink": "https://calendar.google.com/event?id=123"}
        }
        
        # Configure the import_calendar_integration to return our mocks
        mock_import.return_value = (mock_calendar_integration, mock_calendar_provider, True)
        
        yield mock_calendar_instance

def test_check_availability(mock_calendar_integration):
    # Create an instance of CalendarIntegrator
    integrator = CalendarIntegrator("GOOGLE")
    
    # Test the check_availability method
    date = "2023-09-18"
    result = integrator.check_availability(date)
    
    # Verify the result
    assert result['date'] == date
    assert 'availableSlots' in result
    assert result['success'] is True
    assert len(result['availableSlots']) > 0

def test_get_next_available_slot(mock_calendar_integration):
    # Create an instance of CalendarIntegrator
    integrator = CalendarIntegrator("GOOGLE")
    
    # Test the get_next_available_slot method
    date = "2023-09-18"
    result = integrator.get_next_available_slot(date)
    
    # Verify the result
    assert result['date'] == date
    assert 'startTime' in result
    assert 'endTime' in result
    assert 'duration' in result
    assert result['success'] is True

def test_sync_appointment(mock_calendar_integration):
    # Create an instance of CalendarIntegrator
    integrator = CalendarIntegrator("GOOGLE")
    
    # Test the sync_appointment method
    appointment_id = "test-appointment-1"
    summary = "Test appointment"
    date = "2023-09-18"
    start_time = "14:00"
    
    result = integrator.sync_appointment(appointment_id, summary, date, start_time)
    
    # Verify the result
    assert result['success'] is True
    assert result['appointmentId'] == appointment_id
    assert 'calendarEventId' in result
    assert 'calendarLink' in result

@pytest.fixture
def setup_env_vars():
    """Setup test environment variables"""
    # Save original environment
    original_env = os.environ.copy()
    
    # Set up test environment variables
    os.environ['GOOGLE_CALENDAR_TYPE'] = 'service_account'
    os.environ['GOOGLE_CALENDAR_PROJECT_ID'] = 'test-project'
    os.environ['GOOGLE_CALENDAR_PRIVATE_KEY_ID'] = 'test-key-id'
    os.environ['GOOGLE_CALENDAR_PRIVATE_KEY'] = '-----BEGIN PRIVATE KEY-----\\nTEST_KEY\\n-----END PRIVATE KEY-----\\n'
    os.environ['GOOGLE_CALENDAR_CLIENT_EMAIL'] = 'test@test-project.iam.gserviceaccount.com'
    os.environ['GOOGLE_CALENDAR_CLIENT_ID'] = '123456789'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

def test_calendar_integrator_env_vars(setup_env_vars):
    """Test that CalendarIntegrator correctly uses environment variables"""
    # Mock import_calendar_integration to avoid real imports
    with patch('bedrock_agent.calendar_integrator.import_calendar_integration') as mock_import:
        # Set up mock returns
        CalendarIntegration_mock = MagicMock()
        CalendarProvider_mock = MagicMock()
        provider_instance = MagicMock()
        provider_instance.value = 'google'
        CalendarProvider_mock.return_value = provider_instance
        
        # Configure the import to return our mocks
        mock_import.return_value = (CalendarIntegration_mock, CalendarProvider_mock, True)
        
        # Create the integrator with environment-based configuration
        integrator = CalendarIntegrator()
        
        # Verify the provider was initialized from DEFAULT_CALENDAR_PROVIDER
        CalendarProvider_mock.assert_called_once()
        assert integrator.provider == provider_instance
        
        # Verify the calendar integration was initialized
        CalendarIntegration_mock.assert_called_once()
        assert integrator.calendar_integration == CalendarIntegration_mock.return_value

def test_lambda_handler():
    # Mock the CalendarIntegrator.check_availability method
    with patch('bedrock_agent.calendar_integrator.CalendarIntegrator.check_availability') as mock_check:
        # Set up the mock return value
        mock_check.return_value = {
            'date': '2023-09-18',
            'availableSlots': [
                {'startTime': '09:00', 'endTime': '10:00', 'duration': 60},
                {'startTime': '10:00', 'endTime': '11:00', 'duration': 60}
            ],
            'success': True
        }
        
        # Test the lambda_handler function with a check_availability action using AWS Bedrock Agent format
        event = {
            'messageVersion': '1.0',
            'agent': {
                'name': 'appointment-system-agent-dev',
                'version': 'DRAFT',
                'id': 'W22HXGKJMX',
                'alias': 'TSTALIASID'
            },
            'sessionId': '12345',
            'actionGroup': 'CalendarIntegrator',
            'apiPath': '/calendar/availability',
            'httpMethod': 'GET',
            'parameters': [
                {
                    'name': 'date',
                    'type': 'string',
                    'value': '2023-09-18'
                },
                {
                    'name': 'startTime',
                    'type': 'string',
                    'value': '09:00'
                }
            ],
            'inputText': 'I want to check availability for September 18th at 9 AM'
        }
        
        result = lambda_handler(event, {})
        
        # Verify the mock was called
        mock_check.assert_called_once_with('2023-09-18', '09:00', '17:00')
        
        # Verify the result has the Bedrock Agent expected format
        assert result['messageVersion'] == '1.0'
        assert 'response' in result
        assert 'output' in result['response']
        assert result['response']['output']['date'] == '2023-09-18'
        assert 'availableSlots' in result['response']['output']
        assert result['response']['output']['success'] is True

def test_string_event_handling():
    """Test that the lambda handler properly handles a string input event."""
    # Arrange - this is how Bedrock Agents would pass the event, but as a string
    string_event = json.dumps({
        "messageVersion": "1.0",
        "agent": {
            "name": "appointment-system-agent-dev",
            "version": "DRAFT",
            "id": "W22HXGKJMX",
            "alias": "TSTALIASID"
        },
        "sessionId": "774305583312847",
        "actionGroup": "CalendarIntegrator",
        "sessionAttributes": {},
        "promptSessionAttributes": {},
        "httpMethod": "GET",
        "apiPath": "/calendar/availability",
        "inputText": "25/03/2025 around 12:00"
        # Intentionally missing 'date' parameter
    })
    
    # Act
    response = lambda_handler(string_event, {})
    
    # Assert
    assert response is not None
    assert 'messageVersion' in response
    assert 'response' in response
    assert 'output' in response['response']
    assert 'error' in response['response']['output']
    assert 'Missing required parameter: date' in response['response']['output']['error']

def test_missing_action_name():
    """Test that the lambda handler properly handles a missing actionName."""
    # Arrange
    missing_action_event = {
        "messageVersion": "1.0",
        "agent": {
            "name": "appointment-booking-agent",
            "id": "agent-id-123"
        },
        "actionGroup": {
            "name": "CalendarIntegrator"
            # Missing actionName
        }
    }
    
    # Act
    response = lambda_handler(missing_action_event, {})
    
    # Assert
    assert response is not None
    assert 'messageVersion' in response
    assert 'response' in response
    assert 'output' in response['response']
    assert 'error' in response['response']['output']
    assert 'Missing action name' in response['response']['output']['error']

def test_attribute_error_handling():
    """Test that AttributeError is handled correctly."""
    # This test simulates the error in the original issue
    # where event.get('actionGroup') is called on a string object
    
    # Arrange - create an event object that will cause AttributeError
    # when accessing nested properties
    with patch('bedrock_agent.calendar_integrator.isinstance') as mock_isinstance:
        # Force the code to think this is not a string, but it actually is
        mock_isinstance.return_value = False
        
        # This would normally cause: AttributeError: 'str' object has no attribute 'get'
        event = "not_a_dictionary"
        
        # Act
        response = lambda_handler(event, {})
        
        # Assert
        assert response is not None
        assert 'messageVersion' in response
        assert 'response' in response
        assert 'output' in response['response']
        assert 'error' in response['response']['output']
        assert 'Invalid event format' in response['response']['output']['error']
