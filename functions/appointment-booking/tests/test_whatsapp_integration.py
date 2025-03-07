import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add the path to the src directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the module to test
from whatsapp_integration import WhatsAppMessaging

@pytest.fixture
def mock_environment(monkeypatch):
    monkeypatch.setenv('WHATSAPP_PHONE_NUMBER_ID', 'test-phone-number-id')

@pytest.fixture
def mock_messaging_client():
    mock_client = MagicMock()
    mock_client.send_message.return_value = {'MessageId': 'test-message-id'}
    return mock_client

def test_init_with_environment(mock_environment):
    # Test initialization with environment variable
    with patch('boto3.client') as mock_boto3_client:
        mock_messaging = MagicMock()
        mock_boto3_client.return_value = mock_messaging
        whatsapp = WhatsAppMessaging()
    
    # Verify the phone number ID was set from the environment
    assert whatsapp.phone_number_id == 'test-phone-number-id'

def test_init_with_default():
    # Test initialization without environment variable
    with patch('boto3.client') as mock_boto3_client:
        mock_messaging = MagicMock()
        mock_boto3_client.return_value = mock_messaging
        whatsapp = WhatsAppMessaging()
    
    # Verify a default was used
    assert whatsapp.phone_number_id == 'default_phone_number_id'

def test_send_text_message(mock_messaging_client, mock_environment):
    # Create an instance with the mock client
    whatsapp = WhatsAppMessaging(messaging_client=mock_messaging_client)
    
    # Test sending a text message
    result = whatsapp.send_text_message('+1234567890', 'Test message')
    
    # Verify the result
    assert result['success'] is True
    assert result['message_id'] == 'test-message-id'
    
    # Verify the mock was called
    mock_messaging_client.send_message.assert_called_once_with(
        DestinationPhoneNumber='+1234567890',
        OriginationIdentity='test-phone-number-id',
        MessageType='TEXT',
        Content={
            'TextMessage': {
                'Message': 'Test message'
            }
        }
    )

def test_send_template_message(mock_messaging_client, mock_environment):
    # Create an instance with the mock client
    whatsapp = WhatsAppMessaging(messaging_client=mock_messaging_client)
    
    # Test sending a template message
    result = whatsapp.send_template_message(
        '+1234567890', 
        'appointment_confirmation',
        'en_US',
        [{'type': 'body', 'parameters': [{'type': 'text', 'text': 'Test'}]}]
    )
    
    # Verify the result
    assert result['success'] is True
    assert result['message_id'] == 'test-message-id'
    
    # Verify the mock was called
    mock_messaging_client.send_message.assert_called_once_with(
        DestinationPhoneNumber='+1234567890',
        OriginationIdentity='test-phone-number-id',
        MessageType='TEMPLATE',
        Content={
            'WhatsAppTemplate': {
                'Name': 'appointment_confirmation',
                'LanguageCode': 'en_US',
                'Components': [{'type': 'body', 'parameters': [{'type': 'text', 'text': 'Test'}]}]
            }
        }
    )

def test_send_appointment_confirmation(mock_messaging_client, mock_environment):
    # Create an instance with the mock client
    whatsapp = WhatsAppMessaging(messaging_client=mock_messaging_client)
    
    # Test sending an appointment confirmation
    result = whatsapp.send_appointment_confirmation(
        '+1234567890',
        '2023-09-18',
        '14:00',
        'Test appointment'
    )
    
    # Verify the result
    assert result['success'] is True
    assert result['message_id'] == 'test-message-id'
    
    # Verify the mock was called
    mock_messaging_client.send_message.assert_called_once()
    
    # Extract the message text from the call arguments
    call_args = mock_messaging_client.send_message.call_args[1]
    message_text = call_args['Content']['TextMessage']['Message']
    
    # Verify the message content
    assert 'Appointment Confirmed' in message_text
    assert 'Monday, September 18, 2023' in message_text
    assert '14:00' in message_text
    assert 'Test appointment' in message_text

def test_send_appointment_reminder(mock_messaging_client, mock_environment):
    # Create an instance with the mock client
    whatsapp = WhatsAppMessaging(messaging_client=mock_messaging_client)
    
    # Test sending an appointment reminder
    result = whatsapp.send_appointment_reminder(
        '+1234567890',
        '2023-09-18',
        '14:00',
        'Test appointment'
    )
    
    # Verify the result
    assert result['success'] is True
    assert result['message_id'] == 'test-message-id'
    
    # Verify the mock was called
    mock_messaging_client.send_message.assert_called_once()
    
    # Extract the message text from the call arguments
    call_args = mock_messaging_client.send_message.call_args[1]
    message_text = call_args['Content']['TextMessage']['Message']
    
    # Verify the message content
    assert 'Appointment Reminder' in message_text
    assert 'Monday, September 18, 2023' in message_text
    assert '14:00' in message_text
    assert 'Test appointment' in message_text

def test_process_webhook_event():
    # Create an instance
    with patch('boto3.client') as mock_boto3_client:
        mock_messaging = MagicMock()
        mock_boto3_client.return_value = mock_messaging
        whatsapp = WhatsAppMessaging()
    
    # Test webhook event
    body = {
        'object': 'whatsapp_business_account',
        'entry': [
            {
                'id': 'business-account-id',
                'changes': [
                    {
                        'field': 'messages',
                        'value': {
                            'messages': [
                                {
                                    'from': '+1234567890',
                                    'id': 'message-id',
                                    'type': 'text',
                                    'text': {
                                        'body': 'I need an appointment'
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    # Process the webhook event
    result = whatsapp.process_webhook_event(body)
    
    # Verify the result
    assert result['channel'] == 'whatsapp'
    assert result['phone_number'] == '+1234567890'
    assert result['message'] == 'I need an appointment'
    assert result['session_id'] == 'message-id'
