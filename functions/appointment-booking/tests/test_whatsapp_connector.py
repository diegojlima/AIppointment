
# functions/appointment-booking/tests/test_whatsapp_connector.py
import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from whatsapp_connector import WhatsAppConnector

class TestWhatsAppConnector:
    """Test suite for the WhatsApp Business API connector."""
    
    def test_connector_initialization(self):
        """Test that the connector initializes with proper parameters."""
        # Define test parameters
        metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        connection_params = {
            "access_token": "test_access_token",
            "webhook_verify_token": "test_verify_token",
            "api_version": "v17.0"
        }
        
        # Initialize connector
        connector = WhatsAppConnector(metadata, connection_params)
        
        # Verify initialization
        assert connector.phone_number_id == "123456789"
        assert connector.business_account_id == "987654321"
        assert connector.access_token == "test_access_token"
        assert connector.webhook_verify_token == "test_verify_token"
        assert connector.api_version == "v17.0"
        assert connector.base_url == f"https://graph.facebook.com/{connection_params['api_version']}"
    
    def test_validate_connector_metadata(self):
        """Test metadata validation."""
        valid_metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        
        # Should not raise an exception
        WhatsAppConnector.validate_connector_metadata(valid_metadata)
        
        # Test with missing phone_number_id
        invalid_metadata = {
            "business_account_id": "987654321"
        }
        with pytest.raises(ValueError) as excinfo:
            WhatsAppConnector.validate_connector_metadata(invalid_metadata)
        assert "phone_number_id" in str(excinfo.value)
        
        # Test with missing business_account_id
        invalid_metadata = {
            "phone_number_id": "123456789"
        }
        with pytest.raises(ValueError) as excinfo:
            WhatsAppConnector.validate_connector_metadata(invalid_metadata)
        assert "business_account_id" in str(excinfo.value)
    
    def test_get_full_instance_mapping_path(self):
        """Test instance mapping path generation."""
        metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        
        path = WhatsAppConnector.get_full_instance_mapping_path(metadata)
        assert path == "whatsapp_123456789"
    
    @patch('requests.post')
    def test_send_text_message(self, mock_post):
        """Test sending a text message."""
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"wa_id": "1234567890"}],
            "messages": [{"id": "wamid.123"}]
        }
        mock_post.return_value = mock_response
        
        # Set up connector
        metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        connection_params = {
            "access_token": "test_access_token",
            "webhook_verify_token": "test_verify_token",
            "api_version": "v17.0"
        }
        connector = WhatsAppConnector(metadata, connection_params)
        
        # Test sending a message
        result = connector.execute_action(
            "send_text_message", 
            {
                "recipient_phone": "1234567890",
                "message_text": "Hello from the test!"
            }
        )
        
        # Verify requests.post was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        assert call_args[0][0] == f"https://graph.facebook.com/v17.0/123456789/messages"
        
        # Check headers
        headers = call_args[1]['headers']
        assert headers['Authorization'] == "Bearer test_access_token"
        assert headers['Content-Type'] == "application/json"
        
        # Check payload
        payload = json.loads(call_args[1]['data'])
        assert payload['messaging_product'] == "whatsapp"
        assert payload['recipient_type'] == "individual"
        assert payload['to'] == "1234567890"
        assert payload['type'] == "text"
        assert payload['text']['body'] == "Hello from the test!"
        
        # Check result
        assert result['success'] is True
        assert "message_id" in result
        assert result['message_id'] == "wamid.123"
    
    @patch('requests.post')
    def test_send_template_message(self, mock_post):
        """Test sending a template message."""
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"wa_id": "1234567890"}],
            "messages": [{"id": "wamid.456"}]
        }
        mock_post.return_value = mock_response
        
        # Set up connector
        metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        connection_params = {
            "access_token": "test_access_token",
            "webhook_verify_token": "test_verify_token",
            "api_version": "v17.0"
        }
        connector = WhatsAppConnector(metadata, connection_params)
        
        # Test sending a template message
        result = connector.execute_action(
            "send_template_message", 
            {
                "recipient_phone": "1234567890",
                "template_name": "appointment_confirmation",
                "language_code": "en_US",
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": "2023-09-20"
                            },
                            {
                                "type": "text",
                                "text": "14:00"
                            },
                            {
                                "type": "text",
                                "text": "dental checkup"
                            }
                        ]
                    }
                ]
            }
        )
        
        # Verify requests.post was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        assert call_args[0][0] == f"https://graph.facebook.com/v17.0/123456789/messages"
        
        # Check headers
        headers = call_args[1]['headers']
        assert headers['Authorization'] == "Bearer test_access_token"
        assert headers['Content-Type'] == "application/json"
        
        # Check payload
        payload = json.loads(call_args[1]['data'])
        assert payload['messaging_product'] == "whatsapp"
        assert payload['recipient_type'] == "individual"
        assert payload['to'] == "1234567890"
        assert payload['type'] == "template"
        assert payload['template']['name'] == "appointment_confirmation"
        assert payload['template']['language']['code'] == "en_US"
        assert len(payload['template']['components']) == 1
        assert payload['template']['components'][0]['type'] == "body"
        assert len(payload['template']['components'][0]['parameters']) == 3
        
        # Check result
        assert result['success'] is True
        assert "message_id" in result
        assert result['message_id'] == "wamid.456"
    
    def test_webhook_verification(self):
        """Test webhook verification endpoint handling."""
        # Set up connector
        metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        connection_params = {
            "access_token": "test_access_token",
            "webhook_verify_token": "test_verify_token",
            "api_version": "v17.0"
        }
        connector = WhatsAppConnector(metadata, connection_params)
        
        # Test verification with valid token
        result = connector.execute_action(
            "verify_webhook", 
            {
                "mode": "subscribe",
                "verify_token": "test_verify_token",
                "challenge": "test_challenge"
            }
        )
        
        assert result['success'] is True
        assert result['hub.challenge'] == "test_challenge"
        
        # Test verification with invalid token
        result = connector.execute_action(
            "verify_webhook", 
            {
                "mode": "subscribe",
                "verify_token": "wrong_token",
                "challenge": "test_challenge"
            }
        )
        
        assert result['success'] is False
        assert "error" in result
    
    def test_process_webhook_message(self):
        """Test processing incoming webhook message."""
        # Set up connector
        metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        connection_params = {
            "access_token": "test_access_token",
            "webhook_verify_token": "test_verify_token",
            "api_version": "v17.0"
        }
        connector = WhatsAppConnector(metadata, connection_params)
        
        # Example webhook payload for a text message
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "987654321",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "+1234567890",
                                    "phone_number_id": "123456789"
                                },
                                "contacts": [
                                    {
                                        "profile": {
                                            "name": "Test User"
                                        },
                                        "wa_id": "9876543210"
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "9876543210",
                                        "id": "wamid.123",
                                        "timestamp": "1631234567",
                                        "text": {
                                            "body": "Hello, I need an appointment for tomorrow at 2pm"
                                        },
                                        "type": "text"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        # Process the webhook
        result = connector.execute_action("process_webhook", {"payload": webhook_payload})
        
        # Verify processing
        assert result['success'] is True
        assert "messages" in result
        assert len(result['messages']) == 1
        message = result['messages'][0]
        assert message['type'] == "text"
        assert message['phone_number'] == "9876543210"
        assert message['text'] == "Hello, I need an appointment for tomorrow at 2pm"
        assert message['message_id'] == "wamid.123"
