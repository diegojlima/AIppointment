import pytest
import boto3
import json
from moto import mock_aws
from datetime import datetime, timedelta
from unittest.mock import patch

# Add the path to the src directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import the components to test
from bedrock_agent.appointment_creator import AppointmentCreator
from bedrock_agent.appointment_manager import AppointmentManager

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
def test_create_and_retrieve_appointment(mock_dynamodb_table):
    """Test creating an appointment and then retrieving it"""
    
    # Create instances of the action groups
    creator = AppointmentCreator(dynamodb_client=mock_dynamodb_table)
    manager = AppointmentManager(dynamodb_client=mock_dynamodb_table)
    
    # Test parameters
    user_id = "+1234567890"
    # Use tomorrow's date to avoid the 'date in the past' validation
    date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    time = "14:00"
    purpose = "Test appointment"
    
    # Step 1: Create an appointment
    create_result = creator.create_appointment(user_id, date, time, purpose)
    
    # Verify the appointment was created successfully
    assert create_result['success'] is True
    assert 'appointmentId' in create_result
    appointment_id = create_result['appointmentId']
    
    # Step 2: Retrieve appointments for the user
    get_result = manager.get_appointments(user_id)
    
    # Verify the appointments were retrieved successfully
    assert get_result['success'] is True
    assert 'appointments' in get_result
    assert len(get_result['appointments']) > 0
    
    # Verify the created appointment is in the list
    found_appointment = False
    for appointment in get_result['appointments']:
        if appointment.get('id') == appointment_id:
            found_appointment = True
            assert appointment.get('date') == date
            assert appointment.get('startTime') == time
            assert appointment.get('purpose') == purpose
            assert appointment.get('status') == "confirmed"
            break
    
    assert found_appointment, "Created appointment not found in retrieved appointments"

@mock_aws
def test_create_and_cancel_appointment(mock_dynamodb_table):
    """Test creating an appointment and then canceling it"""
    
    # Create instances of the action groups
    creator = AppointmentCreator(dynamodb_client=mock_dynamodb_table)
    manager = AppointmentManager(dynamodb_client=mock_dynamodb_table)
    
    # Test parameters
    user_id = "+1234567890"
    date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    time = "14:00"
    purpose = "Test appointment"
    
    # Step 1: Create an appointment
    create_result = creator.create_appointment(user_id, date, time, purpose)
    assert create_result['success'] is True
    appointment_id = create_result['appointmentId']
    
    # Step 2: Cancel the appointment
    cancel_result = manager.cancel_appointment(appointment_id)
    
    # Verify the cancellation was successful
    assert cancel_result['success'] is True
    assert cancel_result['appointmentId'] == appointment_id
    assert cancel_result['status'] == "cancelled"
    
    # Step 3: Verify the appointment is marked as cancelled in the database
    get_result = manager.get_appointments(user_id)
    assert get_result['success'] is True
    
    # Find the appointment and check its status
    found_appointment = False
    for appointment in get_result['appointments']:
        if appointment.get('id') == appointment_id:
            found_appointment = True
            assert appointment.get('status') == "cancelled"
            break
    
    assert found_appointment, "Cancelled appointment not found in retrieved appointments"

@mock_aws
def test_create_and_reschedule_appointment(mock_dynamodb_table):
    """Test creating an appointment and then rescheduling it"""
    
    # Create instances of the action groups
    creator = AppointmentCreator(dynamodb_client=mock_dynamodb_table)
    manager = AppointmentManager(dynamodb_client=mock_dynamodb_table)
    
    # Test parameters
    user_id = "+1234567890"
    original_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    original_time = "14:00"
    purpose = "Test appointment"
    
    new_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    new_time = "15:00"
    
    # Step 1: Create an appointment
    create_result = creator.create_appointment(user_id, original_date, original_time, purpose)
    assert create_result['success'] is True
    appointment_id = create_result['appointmentId']
    
    # Step 2: Reschedule the appointment
    reschedule_result = manager.reschedule_appointment(appointment_id, new_date, new_time)
    
    # Verify the rescheduling was successful
    assert reschedule_result['success'] is True
    assert reschedule_result['appointmentId'] == appointment_id
    assert reschedule_result['oldDate'] == original_date
    assert reschedule_result['oldTime'] == original_time
    assert reschedule_result['newDate'] == new_date
    assert reschedule_result['newTime'] == new_time
    
    # Step 3: Verify the appointment has the new date and time
    get_result = manager.get_appointments(user_id)
    assert get_result['success'] is True
    
    # Find the appointment and check its updated schedule
    found_appointment = False
    for appointment in get_result['appointments']:
        if appointment.get('id') == appointment_id:
            found_appointment = True
            assert appointment.get('date') == new_date
            assert appointment.get('startTime') == new_time
            break
    
    assert found_appointment, "Rescheduled appointment not found in retrieved appointments"

@mock_aws
def test_appointment_confirmation_flow(mock_dynamodb_table):
    """Test creating an appointment and generating a confirmation message"""
    
    # Create instances of the action groups
    creator = AppointmentCreator(dynamodb_client=mock_dynamodb_table)
    
    # Test parameters
    user_id = "+1234567890"
    date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    time = "14:00"
    purpose = "Test appointment"
    
    # Step 1: Create an appointment
    create_result = creator.create_appointment(user_id, date, time, purpose)
    assert create_result['success'] is True
    appointment_id = create_result['appointmentId']
    
    # Step 2: Generate a confirmation message
    confirmation_result = creator.generate_confirmation(appointment_id)
    
    # Verify the confirmation generation was successful
    assert confirmation_result['success'] is True
    assert confirmation_result['appointmentId'] == appointment_id
    assert 'confirmationMessage' in confirmation_result
    assert 'appointmentDetails' in confirmation_result
    
    # Check that the confirmation message contains the essential information
    confirmation_message = confirmation_result['confirmationMessage']
    assert purpose in confirmation_message
    assert time in confirmation_message
