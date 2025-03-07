import pytest
import json
import boto3
from unittest.mock import MagicMock, patch
from moto import mock_aws
from datetime import datetime

# Add the path to the src directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the module to test
from main import lambda_handler, handle_whatsapp_message, invoke_bedrock_agent

@pytest.fixture
def mock_dynamodb_tables():
    with mock_aws():
        # Create a DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        
        # Create the tables
        conversation_table = dynamodb.create_table(
            TableName='ConversationHistory',
            KeySchema=[
                {'AttributeName': 'conversationId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'conversationId', 'AttributeType': 'S'},
                {'AttributeName': 'senderId', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'SenderIdIndex',
                    'KeySchema': [
                        {'AttributeName': 'senderId', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        messages_table = dynamodb.create_table(
            TableName='ConversationHistoryMessages',
            KeySchema=[
                {'AttributeName': 'messageId', 'KeyType': 'HASH'},
                {'AttributeName': 'conversationId', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'messageId', 'AttributeType': 'S'},
                {'AttributeName': 'conversationId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield (conversation_table, messages_table)

@pytest.fixture
def mock_environment(monkeypatch):
    monkeypatch.setenv('BEDROCK_AGENT_ID', 'test-agent-id')
    monkeypatch.setenv('BEDROCK_AGENT_ALIAS_ID', 'test-agent-alias-id')
    monkeypatch.setenv('WHATSAPP_PHONE_NUMBER_ID', 'test-phone-number-id')
    monkeypatch.setenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'test-verify-token')

@mock_aws
def test_handle_whatsapp_message(mock_dynamodb_tables, mock_environment):
    # Mock the necessary functions
    with patch('main.invoke_bedrock_agent') as mock_invoke, \
         patch('main.WhatsAppMessaging') as mock_whatsapp:
        # Set up mock return values
        mock_invoke.return_value = {'completion': 'This is a test response'}
        
        mock_whatsapp_instance = MagicMock()
        mock_whatsapp.return_value = mock_whatsapp_instance
        mock_whatsapp_instance.send_text_message.return_value = {'success': True, 'message_id': 'test-message-id'}
        
        # Test input
        normalized_input = {
            'phone_number': '+1234567890',
            'message': 'I need an appointment',
            'channel': 'whatsapp',
            'session_id': 'test-session-id'
        }
        
        # Run the function
        result = handle_whatsapp_message(normalized_input)
        
        # Verify the result
        assert result['statusCode'] == 200
        assert 'conversation_id' in json.loads(result['body'])
        assert 'whatsapp_response' in json.loads(result['body'])
        
        # Verify the mocks were called
        mock_invoke.assert_called_once()
        mock_whatsapp_instance.send_text_message.assert_called_once_with(
            recipient_id='+1234567890', 
            message='This is a test response'
        )

@mock_aws
def test_webhook_verification(mock_environment):
    # Test a webhook verification request
    with patch('main.WhatsAppMessaging') as mock_whatsapp:
        event = {
            'queryStringParameters': {
                'hub.mode': 'subscribe',
                'hub.verify_token': 'test-verify-token',
                'hub.challenge': 'test-challenge'
            }
        }
        
        # Run the function
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result['statusCode'] == 200
        assert result['body'] == 'test-challenge'

@mock_aws
def test_webhook_verification_failure(mock_environment):
    # Test a webhook verification request with wrong token
    with patch('main.WhatsAppMessaging') as mock_whatsapp:
        event = {
            'queryStringParameters': {
                'hub.mode': 'subscribe',
                'hub.verify_token': 'wrong-token',
                'hub.challenge': 'test-challenge'
            }
        }
        
        # Run the function
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result['statusCode'] == 403
        assert 'error' in json.loads(result['body'])

@mock_aws
def test_lambda_handler_success(mock_dynamodb_tables, mock_environment):
    # Mock the handle_whatsapp_message function
    with patch('main.handle_whatsapp_message') as mock_handle:
        # Set up mock return value
        mock_handle.return_value = {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processed successfully'})
        }
        
        # Test event
        event = {
            'body': json.dumps({
                'phone_number': '+1234567890',
                'message': 'I need an appointment',
                'channel': 'whatsapp'
            })
        }
        
        # Run the function
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result['statusCode'] == 200
        assert 'message' in json.loads(result['body'])
        
        # Verify the mock was called
        mock_handle.assert_called_once()

@mock_aws
def test_lambda_handler_unsupported_channel(mock_dynamodb_tables, mock_environment):
    # Test event with unsupported channel
    event = {
        'body': json.dumps({
            'phone_number': '+1234567890',
            'message': 'I need an appointment',
            'channel': 'sms'  # Not supported
        })
    }
    
    # Run the function
    result = lambda_handler(event, {})
    
    # Verify the result
    assert result['statusCode'] == 400
    assert 'error' in json.loads(result['body'])
    assert 'Unsupported channel' in json.loads(result['body'])['error']
