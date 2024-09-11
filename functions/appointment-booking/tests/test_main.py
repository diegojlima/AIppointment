import pytest
from moto import mock_dynamodb
import boto3
import json
import os
from unittest.mock import patch
from src.main import lambda_handler

@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    # Setup environment variable for the DynamoDB table name
    monkeypatch.setenv("DYNAMODB_TABLE", "test-table-name")

@pytest.fixture
def dynamodb_table():
    with mock_dynamodb():
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='test-table-name',
            KeySchema=[
                {'AttributeName': 'PhoneNumber', 'KeyType': 'HASH'},
                {'AttributeName': 'CreatedAt', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PhoneNumber', 'AttributeType': 'S'},
                {'AttributeName': 'CreatedAt', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        yield dynamodb

@pytest.fixture
def valid_event():
    return {
        'body': json.dumps({
            'phone_number': '+1234567890',
            'message': 'I need an appointment on Monday at 2pm for a checkup.'
        })
    }

@mock_dynamodb
def test_lambda_handler_success(valid_event, dynamodb_table):
    with patch('src.main.ChatBedrock'), patch('src.main.LLMChain') as mock_chain:
        mock_chain.return_value.run.return_value = json.dumps({
            "date": "2023-09-18",
            "time": "14:00",
            "purpose": "checkup"
        })
        
        response = lambda_handler(valid_event, {})
        
        assert response['statusCode'] == 200
        assert 'Appointment request processed successfully' in json.loads(response['body'])['message']

@mock_dynamodb
def test_lambda_handler_missing_fields(dynamodb_table):
    event = {'body': json.dumps({})}
    response = lambda_handler(event, {})
    
    assert response['statusCode'] == 400
    assert 'Phone number and message are required' in json.loads(response['body'])['error']

@mock_dynamodb
@patch('src.main.process_message')
def test_lambda_handler_bedrock_error(mock_process_message, dynamodb_table):
    mock_process_message.side_effect = Exception("Bedrock error")
    event = {
        'body': json.dumps({
            'phone_number': '+1234567890',
            'message': 'Test message'
        })
    }
    response = lambda_handler(event, {})
    
    assert response['statusCode'] == 500
    assert 'Internal server error' in json.loads(response['body'])['error']

@mock_dynamodb
@patch('src.main.process_message')
def test_lambda_handler_invalid_appointment(mock_process_message, dynamodb_table):
    mock_process_message.return_value = {
        "date": "2023-01-01",  # Past date
        "time": "14:00",
        "purpose": "checkup"
    }
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