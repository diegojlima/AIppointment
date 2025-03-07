
# functions/appointment-booking/tests/test_multi_channel.py
import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_channel import MultiChannelHandler

class TestMultiChannelHandler:
    """Test suite for the MultiChannelHandler."""
    
    @patch('multi_channel.create_connector_registry')
    def test_initialization_with_config_items(self, mock_registry_class):
        """Test initialization with config items."""
        # Create a mock registry instance
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        
        # Config items
        config_items = [
            {
                "connectorType": "WHATSAPP",
                "connectorMetadata": {
                    "phone_number_id": "123456789",
                    "business_account_id": "987654321"
                },
                "connectorConnectionParams": {
                    "access_token": "test_access_token",
                    "webhook_verify_token": "test_verify_token",
                    "api_version": "v17.0"
                }
            }
        ]
        
        # Initialize the handler
        handler = MultiChannelHandler(config_items=config_items)
        
        # Verify the registry was initialized with the config items
        mock_registry_class.assert_called_once_with(config_items)
        assert handler.registry == mock_registry
    
    @patch('multi_channel.create_connector_registry')
    @patch('builtins.open', new_callable=MagicMock)
    def test_initialization_with_config_file(self, mock_open, mock_registry_class):
        """Test initialization with a config file."""
        # Create a mock registry instance
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        
        # Config items to be loaded from file
        config_items = [
            {
                "connectorType": "WHATSAPP",
                "connectorMetadata": {
                    "phone_number_id": "123456789",
                    "business_account_id": "987654321"
                },
                "connectorConnectionParams": {
                    "access_token": "test_access_token",
                    "webhook_verify_token": "test_verify_token",
                    "api_version": "v17.0"
                }
            }
        ]
        
        # Mock the file open and json.load
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        with patch('json.load', return_value=config_items):
            # Initialize the handler with a config file
            handler = MultiChannelHandler(config_file_path="test_config.json")
        
        # Verify the registry was initialized with the config items from the file
        mock_open.assert_called_once_with("test_config.json", 'r')
        mock_registry_class.assert_called_once_with(config_items)
        assert handler.registry == mock_registry
    
    @patch('multi_channel.create_connector_registry')
    def test_process_whatsapp_message(self, mock_registry_class):
        """Test processing a WhatsApp message."""
        # Create a mock registry instance
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        
        # Mock execute_action response
        mock_registry.execute_action.return_value = {
            "success": True,
            "messages": [
                {
                    "message_id": "wamid.123",
                    "phone_number": "1234567890",
                    "timestamp": "1631234567",
                    "type": "text",
                    "text": "Hello, I need an appointment"
                }
            ]
        }
        
        # Initialize the handler
        handler = MultiChannelHandler(config_items=[])
        
        # Example webhook payload
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
                                        "wa_id": "1234567890"
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "wamid.123",
                                        "timestamp": "1631234567",
                                        "text": {
                                            "body": "Hello, I need an appointment"
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
        
        # Process the message
        result = handler.process_incoming_message("WHATSAPP", webhook_payload)
        
        # Verify the registry's execute_action was called correctly
        mock_registry.execute_action.assert_called_once_with(
            "WHATSAPP",
            {
                "business_account_id": "987654321",
                "phone_number_id": "123456789"
            },
            "process_webhook",
            {"payload": webhook_payload}
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["channel"] == "WHATSAPP"
        assert len(result["messages"]) == 1
        assert result["messages"][0]["channel"] == "WHATSAPP"
        assert result["messages"][0]["content_type"] == "text"
        assert result["messages"][0]["content"] == "Hello, I need an appointment"
    
    @patch('multi_channel.create_connector_registry')
    def test_send_whatsapp_text_message(self, mock_registry_class):
        """Test sending a WhatsApp text message."""
        # Create a mock registry instance
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        
        # Mock execute_action response
        mock_registry.execute_action.return_value = {
            "success": True,
            "message_id": "wamid.456"
        }
        
        # Initialize the handler
        handler = MultiChannelHandler(config_items=[])
        
        # Metadata for the connector instance
        metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        
        # Send a text message
        result = handler.send_message(
            channel="WHATSAPP",
            recipient_id="1234567890",
            message_type="text",
            content="Hello, your appointment is confirmed!",
            metadata=metadata
        )
        
        # Verify the registry's execute_action was called correctly
        mock_registry.execute_action.assert_called_once_with(
            "WHATSAPP",
            metadata,
            "send_text_message",
            {
                "recipient_phone": "1234567890",
                "message_text": "Hello, your appointment is confirmed!"
            }
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["message_id"] == "wamid.456"
    
    @patch('multi_channel.create_connector_registry')
    def test_send_whatsapp_template_message(self, mock_registry_class):
        """Test sending a WhatsApp template message."""
        # Create a mock registry instance
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        
        # Mock execute_action response
        mock_registry.execute_action.return_value = {
            "success": True,
            "message_id": "wamid.789"
        }
        
        # Initialize the handler
        handler = MultiChannelHandler(config_items=[])
        
        # Metadata for the connector instance
        metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        
        # Template content
        template_content = {
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
        
        # Send a template message
        result = handler.send_message(
            channel="WHATSAPP",
            recipient_id="1234567890",
            message_type="template",
            content=template_content,
            metadata=metadata
        )
        
        # Verify the registry's execute_action was called correctly
        mock_registry.execute_action.assert_called_once_with(
            "WHATSAPP",
            metadata,
            "send_template_message",
            {
                "recipient_phone": "1234567890",
                "template_name": "appointment_confirmation",
                "language_code": "en_US",
                "components": template_content["components"]
            }
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["message_id"] == "wamid.789"
    
    @patch('multi_channel.create_connector_registry')
    def test_handle_webhook_verification(self, mock_registry_class):
        """Test handling webhook verification."""
        # Create a mock registry instance
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        
        # Mock execute_action response
        mock_registry.execute_action.return_value = {
            "success": True,
            "hub.challenge": "test_challenge"
        }
        
        # Initialize the handler
        handler = MultiChannelHandler(config_items=[])
        
        # Metadata for the connector instance
        metadata = {
            "phone_number_id": "123456789",
            "business_account_id": "987654321"
        }
        
        # Verification parameters
        params = {
            "mode": "subscribe",
            "verify_token": "test_verify_token",
            "challenge": "test_challenge"
        }
        
        # Handle webhook verification
        result = handler.handle_webhook_verification("WHATSAPP", params, metadata)
        
        # Verify the registry's execute_action was called correctly
        mock_registry.execute_action.assert_called_once_with(
            "WHATSAPP",
            metadata,
            "verify_webhook",
            params
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["hub.challenge"] == "test_challenge"
    
    @patch('multi_channel.create_connector_registry')
    def test_normalize_whatsapp_message(self, mock_registry_class):
        """Test normalizing WhatsApp messages."""
        # Initialize the handler
        handler = MultiChannelHandler(config_items=[])
        
        # Test text message normalization
        text_message = {
            "message_id": "wamid.123",
            "phone_number": "1234567890",
            "timestamp": "1631234567",
            "type": "text",
            "text": "Hello, I need an appointment"
        }
        
        normalized = handler._normalize_whatsapp_message(text_message)
        
        assert normalized["channel"] == "WHATSAPP"
        assert normalized["message_id"] == "wamid.123"
        assert normalized["sender_id"] == "1234567890"
        assert normalized["timestamp"] == "1631234567"
        assert normalized["content_type"] == "text"
        assert normalized["content"] == "Hello, I need an appointment"
        
        # Test image message normalization
        image_message = {
            "message_id": "wamid.456",
            "phone_number": "1234567890",
            "timestamp": "1631234567",
            "type": "image",
            "image": {
                "id": "image.123",
                "mime_type": "image/jpeg"
            }
        }
        
        normalized = handler._normalize_whatsapp_message(image_message)
        
        assert normalized["channel"] == "WHATSAPP"
        assert normalized["message_id"] == "wamid.456"
        assert normalized["sender_id"] == "1234567890"
        assert normalized["timestamp"] == "1631234567"
        assert normalized["content_type"] == "image"
        assert normalized["content"]["id"] == "image.123"
        assert normalized["content"]["mime_type"] == "image/jpeg"
