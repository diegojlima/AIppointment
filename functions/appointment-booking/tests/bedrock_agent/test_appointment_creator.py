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
from bedrock_agent.appointment_creator import AppointmentCreator, lambda_handler

@pytest.fixture
def mock_dynamodb_table():
    with mock_aws():
        # Create a DynamoDB resource
        dynamodb_resource = boto3.resource('dynamodb')
        
        # Create the table
        table = dynamodb_resource.create_table(
            TableName='Appointments',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Also create a DynamoDB client
        dynamodb_client = boto3.client('dynamodb')
        
        yield dynamodb_client

@mock_aws
def test_check_availability(mock_dynamodb_table):
    # Create an instance of AppointmentCreator with the mock DynamoDB client
    creator = AppointmentCreator(dynamodb_client=mock_dynamodb_table)
    
    # Test the check_availability method
    date = datetime.now().strftime("%Y-%m-%d")
    result = creator.check_availability(date)
    
    # Verify the result
    assert result['date'] == date
    assert 'availableSlots' in result
    assert result['success'] is True
    assert len(result['availableSlots']) > 0

@mock_aws
def test_create_appointment(mock_dynamodb_table):
    # Create an instance of AppointmentCreator with the mock DynamoDB client
    creator = AppointmentCreator(dynamodb_client=mock_dynamodb_table)
    
    # Test parameters
    user_id = "+1234567890"
    # Use tomorrow's date to avoid the 'date in the past' validation
    date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    time = "14:00"
    purpose = "Test appointment"
    
    # Test the create_appointment method
    result = creator.create_appointment(user_id, date, time, purpose)
    
    # Print the result for debugging
    print(f"\nResult: {result}")
    
    # Verify the result
    assert result['success'] is True
    assert 'appointmentId' in result
    assert result['date'] == date
    assert result['startTime'] == time
    assert result['purpose'] == purpose
    assert result['status'] == "confirmed"

@mock_aws
def test_generate_confirmation(mock_dynamodb_table):
    # Create an instance of AppointmentCreator with the mock DynamoDB client
    creator = AppointmentCreator(dynamodb_client=mock_dynamodb_table)
    
    # First, create an appointment to test confirmation generation
    user_id = "+1234567890"
    date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    time = "14:00"
    purpose = "Test appointment"
    
    # Create the appointment
    appointment_result = creator.create_appointment(user_id, date, time, purpose)
    assert appointment_result['success'] is True
    appointment_id = appointment_result['appointmentId']
    
    # Now test the generate_confirmation method
    result = creator.generate_confirmation(appointment_id)
    
    # Verify the result
    assert result['success'] is True
    assert result['appointmentId'] == appointment_id
    assert 'confirmationMessage' in result
    assert 'appointmentDetails' in result
    
    # Check that the confirmation message contains the appointment details
    confirmation_message = result['confirmationMessage']
    assert purpose in confirmation_message
    assert time in confirmation_message

@mock_aws
def test_lambda_handler():
    # Mock the AppointmentCreator.check_availability method
    with patch('bedrock_agent.appointment_creator.AppointmentCreator.check_availability') as mock_check:
        # Set up the mock return value
        mock_check.return_value = {
            'date': '2023-09-18',
            'availableSlots': [
                {'startTime': '09:00', 'endTime': '10:00', 'available': True},
                {'startTime': '10:00', 'endTime': '11:00', 'available': True}
            ],
            'success': True
        }
        
        # Test the lambda_handler function with a check_availability action
        event = {
            'actionGroup': {'actionName': 'check_availability'},
            'parameters': {'date': '2023-09-18'}
        }
        
        result = lambda_handler(event, {})
        
        # Verify the mock was called
        mock_check.assert_called_once_with('2023-09-18', 60)
        
        # Verify the result
        assert result['date'] == '2023-09-18'
        assert 'availableSlots' in result
        assert result['success'] is True
