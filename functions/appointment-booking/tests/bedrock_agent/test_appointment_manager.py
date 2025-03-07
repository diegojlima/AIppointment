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
from bedrock_agent.appointment_manager import AppointmentManager, lambda_handler

@pytest.fixture
def mock_dynamodb_table():
    with mock_aws():
        # Create a DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        
        # Create the table
        table = dynamodb.create_table(
            TableName='Appointments',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Add test data
        table.put_item(
            Item={
                'id': 'test-appointment-1',
                'userId': '+1234567890',
                'date': '2023-09-18',
                'startTime': '14:00',
                'endTime': '15:00',
                'purpose': 'Test appointment',
                'status': 'confirmed',
                'createdAt': datetime.utcnow().isoformat()
            }
        )
        
        # Add future appointment to ensure it passes with date filtering
        future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        table.put_item(
            Item={
                'id': 'test-appointment-2',
                'userId': '+1234567890',
                'date': future_date,
                'startTime': '10:00',
                'endTime': '11:00',
                'purpose': 'Future appointment',
                'status': 'confirmed',
                'createdAt': datetime.utcnow().isoformat()
            }
        )
        
        yield table

@mock_aws
def test_get_appointments(mock_dynamodb_table):
    # Create an instance of AppointmentManager
    manager = AppointmentManager()
    
    # Test the get_appointments method
    result = manager.get_appointments('+1234567890')
    
    # Verify the result
    assert result['success'] is True
    assert 'appointments' in result
    assert result['userId'] == '+1234567890'
    assert result['count'] > 0

@mock_aws
def test_reschedule_appointment(mock_dynamodb_table):
    # Create an instance of AppointmentManager
    manager = AppointmentManager()
    
    # Test the reschedule_appointment method
    appointment_id = 'test-appointment-1'
    new_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    new_time = "15:00"
    
    result = manager.reschedule_appointment(appointment_id, new_date, new_time)
    
    # Verify the result
    assert result['success'] is True
    assert result['appointmentId'] == appointment_id
    assert 'oldDate' in result
    assert result['newDate'] == new_date
    assert result['newTime'] == new_time
    assert 'updatedAppointment' in result

@mock_aws
def test_cancel_appointment(mock_dynamodb_table):
    # Create an instance of AppointmentManager
    manager = AppointmentManager()
    
    # Test the cancel_appointment method
    appointment_id = 'test-appointment-1'
    
    result = manager.cancel_appointment(appointment_id)
    
    # Verify the result
    assert result['success'] is True
    assert result['appointmentId'] == appointment_id
    assert result['status'] == 'cancelled'

@mock_aws
def test_send_reminder(mock_dynamodb_table):
    # Create an instance of AppointmentManager
    manager = AppointmentManager()
    
    # Test the send_reminder method
    appointment_id = 'test-appointment-1'
    
    result = manager.send_reminder(appointment_id)
    
    # Verify the result
    assert result['success'] is True
    assert result['appointmentId'] == appointment_id
    assert result['userId'] == '+1234567890'
    assert 'reminderMessage' in result

@mock_aws
def test_lambda_handler():
    # Mock the AppointmentManager.get_appointments method
    with patch('bedrock_agent.appointment_manager.AppointmentManager.get_appointments') as mock_get:
        # Set up the mock return value
        mock_get.return_value = {
            'userId': '+1234567890',
            'appointments': [
                {
                    'id': 'test-appointment-1',
                    'date': '2023-09-18',
                    'startTime': '14:00',
                    'purpose': 'Test appointment'
                }
            ],
            'count': 1,
            'success': True
        }
        
        # Test the lambda_handler function with a get_appointments action
        event = {
            'actionGroup': {'actionName': 'get_appointments'},
            'parameters': {'user_id': '+1234567890'}
        }
        
        result = lambda_handler(event, {})
        
        # Verify the mock was called
        mock_get.assert_called_once_with('+1234567890', None, None)
        
        # Verify the result
        assert result['userId'] == '+1234567890'
        assert 'appointments' in result
        assert result['count'] == 1
        assert result['success'] is True
