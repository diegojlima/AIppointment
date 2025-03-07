import pytest
import json
import boto3
from unittest.mock import MagicMock, patch
from moto import mock_aws
from datetime import datetime, timedelta

# Add the path to the src directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import the module to test
from bedrock_agent.calendar_integrator import CalendarIntegrator, lambda_handler

@pytest.fixture
def mock_calendar_integration():
    # Mock the calendar_integration module
    with patch('bedrock_agent.calendar_integrator.CalendarIntegration') as mock_integration:
        # Set up the mock instance
        mock_instance = MagicMock()
        mock_integration.return_value = mock_instance
        
        # Set up mock return values
        mock_instance.check_availability.return_value = [
            {"start": "2023-09-18T09:00:00", "end": "2023-09-18T10:00:00"},
            {"start": "2023-09-18T10:00:00", "end": "2023-09-18T11:00:00"}
        ]
        
        mock_instance.get_next_available_slot.return_value = {
            "start": "2023-09-18T09:00:00", 
            "end": "2023-09-18T10:00:00"
        }
        
        mock_instance.book_appointment.return_value = {
            "success": True, 
            "appointment_id": "test-calendar-event-1",
            "appointment_details": {"htmlLink": "https://calendar.google.com/event?id=123"}
        }
        
        yield mock_instance

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
        
        # Test the lambda_handler function with a check_availability action
        event = {
            'actionGroup': {'actionName': 'check_availability'},
            'parameters': {
                'date': '2023-09-18', 
                'calendar_provider': 'GOOGLE'
            }
        }
        
        result = lambda_handler(event, {})
        
        # Verify the mock was called
        mock_check.assert_called_once_with('2023-09-18', '09:00', '17:00')
        
        # Verify the result
        assert result['date'] == '2023-09-18'
        assert 'availableSlots' in result
        assert result['success'] is True
