# ./functions/appointment-booking/tests/test_main.py
import pytest
import boto3
from moto import mock_aws
import json
import sys
import os
from unittest.mock import patch

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.main import lambda_handler

@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    # Setup environment variable for the DynamoDB table name
    monkeypatch.setenv("DYNAMODB_TABLE", "test-table-name")

@pytest.fixture
def dynamodb_table():
    # Use context manager to initialize moto
    with mock_aws():
        # Create a DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        # Create the table
        table = dynamodb.create_table(
            TableName='test-table-name',
            KeySchema=[
                {'AttributeName': 'PhoneNumber', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PhoneNumber', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        yield table

@pytest.fixture
def valid_event():
    return {
        'body': json.dumps({
            'phone_number': '+1234567890',
            'message': 'I need an appointment on Monday at 2pm for a checkup.'
        })
    }

@mock_aws
def test_lambda_handler_success(valid_event, dynamodb_table):
    # Also patch the get_dynamodb_client function
    with patch('src.main.get_bedrock_client') as mock_bedrock, \
         patch('src.main.process_message') as mock_process_message, \
         patch('src.main.get_dynamodb_client') as mock_dynamodb_client:
        mock_process_message.return_value = {
            "date": "2023-09-18",
            "time": "14:00",
            "purpose": "checkup"
        }
        
        # Set up the mock DynamoDB client
        mock_dynamodb = boto3.client('dynamodb', region_name='us-west-2')
        mock_dynamodb_client.return_value = mock_dynamodb
        
        response = lambda_handler(valid_event, {})
        
        assert response['statusCode'] == 200
        assert 'Appointment request processed successfully' in json.loads(response['body'])['message']

@mock_aws
@patch('src.main.get_dynamodb_client')
def test_lambda_handler_missing_fields(mock_dynamodb_client, dynamodb_table):
    # Set up the mock DynamoDB client
    mock_dynamodb = boto3.client('dynamodb', region_name='us-west-2')
    mock_dynamodb_client.return_value = mock_dynamodb
    event = {'body': json.dumps({})}
    response = lambda_handler(event, {})
    
    assert response['statusCode'] == 400
    assert 'Phone number and message are required' in json.loads(response['body'])['error']

@mock_aws
@patch('src.main.get_dynamodb_client')
@patch('src.main.process_message')
def test_lambda_handler_bedrock_error(mock_process_message, mock_dynamodb_client, dynamodb_table):
    mock_process_message.side_effect = Exception("Bedrock error")
    
    # Set up the mock DynamoDB client
    mock_dynamodb = boto3.client('dynamodb', region_name='us-west-2')
    mock_dynamodb_client.return_value = mock_dynamodb
    event = {
        'body': json.dumps({
            'phone_number': '+1234567890',
            'message': 'Test message'
        })
    }
    response = lambda_handler(event, {})
    
    assert response['statusCode'] == 500
    assert 'Internal server error' in json.loads(response['body'])['error']

@mock_aws
@patch('src.main.get_dynamodb_client')
@patch('src.main.process_message')
def test_lambda_handler_invalid_appointment(mock_process_message, mock_dynamodb_client, dynamodb_table):
    mock_process_message.return_value = {
        "date": "2023-01-01",  # Past date
        "time": "14:00",
        "purpose": "checkup"
    }
    
    # Set up the mock DynamoDB client
    mock_dynamodb = boto3.client('dynamodb', region_name='us-west-2')
    mock_dynamodb_client.return_value = mock_dynamodb
    event = {
        'body': json.dumps({
            'phone_number': '+1234567890',
            'message': 'I need an appointment on January 1st at 2pm for a checkup.'
        })
    }
    response = lambda_handler(event, {})
    
    assert response['statusCode'] == 200
    response_body = json.loads(response['body'])
    assert 'Appointment request processed successfully' in response_body['message']
    assert 'but the requested date/time is not valid' in response_body['message']
    assert not response_body['is_valid']