
# functions/appointment-booking/src/multi_channel.py
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from connector_factory import create_connector_registry

logger = logging.getLogger(__name__)

class MultiChannelHandler:
    """
    Handler for multi-channel messaging in the AIppointment system.
    Manages interactions across different messaging platforms including WhatsApp.
    """
    
    def __init__(self, config_file_path: Optional[str] = None, config_items: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the multi-channel handler with a registry of connectors.
        
        Args:
            config_file_path: Optional path to a JSON config file with connector configurations
            config_items: Optional list of connector configurations (used if config_file_path is None)
        """
        self.registry = None
        
        if config_file_path:
            self._load_config_from_file(config_file_path)
        elif config_items:
            self._initialize_registry(config_items)
        else:
            logger.warning("No configuration provided. Registry will be empty.")
            self._initialize_registry([])
    
    def _load_config_from_file(self, config_file_path: str) -> None:
        """
        Load connector configurations from a JSON file.
        
        Args:
            config_file_path: Path to the JSON config file
        """
        try:
            with open(config_file_path, 'r') as f:
                config_items = json.load(f)
            
            if not isinstance(config_items, list):
                raise ValueError("Config file must contain a list of connector configurations")
            
            self._initialize_registry(config_items)
            
        except Exception as e:
            logger.error(f"Error loading config from {config_file_path}: {str(e)}")
            # Initialize with empty config to avoid None registry
            self._initialize_registry([])
    
    def _initialize_registry(self, config_items: List[Dict[str, Any]]) -> None:
        """
        Initialize the connector registry with the given configurations.
        
        Args:
            config_items: List of connector configurations
        """
        try:
            self.registry = create_connector_registry(config_items)
            logger.info(f"Initialized connector registry with {len(config_items)} connectors")
        except Exception as e:
            logger.error(f"Error initializing connector registry: {str(e)}")
            raise
    
    def process_incoming_message(self, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message from a specific channel.
        
        Args:
            channel: The channel type (e.g., "WHATSAPP", "SLACK", "HTTP")
            payload: The message payload from the channel
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing incoming message from {channel}")
        
        try:
            if channel == "WHATSAPP":
                return self._process_whatsapp_message(payload)
            elif channel == "SLACK":
                return self._process_slack_message(payload)
            elif channel == "HTTP":
                return self._process_http_message(payload)
            else:
                logger.error(f"Unsupported channel: {channel}")
                return {
                    "success": False,
                    "error": f"Unsupported channel: {channel}"
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _process_whatsapp_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message from WhatsApp.
        
        Args:
            payload: The webhook payload from WhatsApp
            
        Returns:
            Dictionary with extracted message details
        """
        # Extract metadata from the payload to identify the connector instance
        metadata = self._extract_whatsapp_metadata(payload)
        
        if not metadata:
            return {
                "success": False,
                "error": "Could not extract metadata from WhatsApp payload"
            }
        
        # Process the webhook using the appropriate connector
        result = self.registry.execute_action(
            "WHATSAPP",
            metadata,
            "process_webhook",
            {"payload": payload}
        )
        
        if not result.get("success", False):
            return result
        
        # Extract normalized messages
        normalized_messages = []
        
        for message in result.get("messages", []):
            normalized = self._normalize_whatsapp_message(message)
            if normalized:
                normalized_messages.append(normalized)
        
        return {
            "success": True,
            "channel": "WHATSAPP",
            "messages": normalized_messages
        }
    
    def _extract_whatsapp_metadata(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract WhatsApp metadata from a webhook payload.
        
        Args:
            payload: The webhook payload from WhatsApp
            
        Returns:
            Dictionary with metadata or None if extraction fails
        """
        try:
            # Check if this is a WhatsApp Business webhook
            if payload.get("object") != "whatsapp_business_account":
                return None
            
            business_account_id = None
            phone_number_id = None
            
            # Extract business account ID and phone number ID
            for entry in payload.get("entry", []):
                business_account_id = entry.get("id")
                
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        metadata = value.get("metadata", {})
                        phone_number_id = metadata.get("phone_number_id")
                        
                        if phone_number_id:
                            break
                
                if phone_number_id:
                    break
            
            if not business_account_id or not phone_number_id:
                return None
            
            return {
                "business_account_id": business_account_id,
                "phone_number_id": phone_number_id
            }
            
        except Exception as e:
            logger.error(f"Error extracting WhatsApp metadata: {str(e)}")
            return None
    
    def _normalize_whatsapp_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize a WhatsApp message to a standard format used across channels.
        
        Args:
            message: The WhatsApp message to normalize
            
        Returns:
            Dictionary with normalized message or None if normalization fails
        """
        try:
            message_type = message.get("type")
            
            if message_type == "text":
                return {
                    "channel": "WHATSAPP",
                    "message_id": message.get("message_id"),
                    "sender_id": message.get("phone_number"),
                    "timestamp": message.get("timestamp"),
                    "content_type": "text",
                    "content": message.get("text"),
                    "raw_message": message
                }
            
            elif message_type in ["image", "audio", "document", "video"]:
                return {
                    "channel": "WHATSAPP",
                    "message_id": message.get("message_id"),
                    "sender_id": message.get("phone_number"),
                    "timestamp": message.get("timestamp"),
                    "content_type": message_type,
                    "content": message.get(message_type, {}),
                    "raw_message": message
                }
            
            elif message_type == "button":
                return {
                    "channel": "WHATSAPP",
                    "message_id": message.get("message_id"),
                    "sender_id": message.get("phone_number"),
                    "timestamp": message.get("timestamp"),
                    "content_type": "button",
                    "content": {
                        "text": message.get("button", {}).get("text"),
                        "payload": message.get("button", {}).get("payload")
                    },
                    "raw_message": message
                }
            
            # Handle other message types if needed
            
            return None
            
        except Exception as e:
            logger.error(f"Error normalizing WhatsApp message: {str(e)}")
            return None
    
    def _process_slack_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message from Slack.
        
        Args:
            payload: The webhook payload from Slack
            
        Returns:
            Dictionary with extracted message details
        """
        # This is a placeholder for Slack message processing
        # Would be implemented similarly to WhatsApp processing
        logger.warning("Slack message processing not implemented yet")
        return {
            "success": False,
            "error": "Slack message processing not implemented yet"
        }
    
    def _process_http_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message from HTTP.
        
        Args:
            payload: The HTTP request payload
            
        Returns:
            Dictionary with extracted message details
        """
        # This is a placeholder for HTTP message processing
        # Would be implemented similarly to WhatsApp processing
        logger.warning("HTTP message processing not implemented yet")
        return {
            "success": False,
            "error": "HTTP message processing not implemented yet"
        }
    
    def send_message(
        self, 
        channel: str, 
        recipient_id: str, 
        message_type: str, 
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a specific channel and recipient.
        
        Args:
            channel: The channel to send to (e.g., "WHATSAPP", "SLACK", "HTTP")
            recipient_id: The recipient ID (e.g., phone number for WhatsApp)
            message_type: The type of message (e.g., "text", "template")
            content: The message content
            metadata: Additional metadata for the connector instance
            
        Returns:
            Dictionary with sending results
        """
        logger.info(f"Sending {message_type} message to {recipient_id} via {channel}")
        
        try:
            if channel == "WHATSAPP":
                return self._send_whatsapp_message(recipient_id, message_type, content, metadata)
            elif channel == "SLACK":
                return self._send_slack_message(recipient_id, message_type, content, metadata)
            elif channel == "HTTP":
                return self._send_http_message(recipient_id, message_type, content, metadata)
            else:
                logger.error(f"Unsupported channel: {channel}")
                return {
                    "success": False,
                    "error": f"Unsupported channel: {channel}"
                }
                
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _send_whatsapp_message(
        self, 
        recipient_phone: str,
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to WhatsApp.
        
        Args:
            recipient_phone: The recipient's phone number
            message_type: The type of message ("text" or "template")
            content: The message content
            metadata: Metadata for the connector instance
            
        Returns:
            Dictionary with sending results
        """
        if not metadata:
            logger.error("Metadata is required for WhatsApp messages")
            return {
                "success": False,
                "error": "Metadata is required for WhatsApp messages"
            }
        
        try:
            if message_type == "text":
                # Send a text message
                return self.registry.execute_action(
                    "WHATSAPP",
                    metadata,
                    "send_text_message",
                    {
                        "recipient_phone": recipient_phone,
                        "message_text": content
                    }
                )
                
            elif message_type == "template":
                # Send a template message
                template_name = content.get("template_name")
                language_code = content.get("language_code", "en_US")
                components = content.get("components", [])
                
                return self.registry.execute_action(
                    "WHATSAPP",
                    metadata,
                    "send_template_message",
                    {
                        "recipient_phone": recipient_phone,
                        "template_name": template_name,
                        "language_code": language_code,
                        "components": components
                    }
                )
                
            else:
                logger.error(f"Unsupported WhatsApp message type: {message_type}")
                return {
                    "success": False,
                    "error": f"Unsupported WhatsApp message type: {message_type}"
                }
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _send_slack_message(
        self, 
        recipient_id: str,
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Slack.
        
        Args:
            recipient_id: The recipient ID (channel or user)
            message_type: The type of message
            content: The message content
            metadata: Metadata for the connector instance
            
        Returns:
            Dictionary with sending results
        """
        # This is a placeholder for Slack message sending
        logger.warning("Slack message sending not implemented yet")
        return {
            "success": False,
            "error": "Slack message sending not implemented yet"
        }
    
    def _send_http_message(
        self, 
        recipient_id: str,
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message via HTTP.
        
        Args:
            recipient_id: The recipient ID (endpoint or identifier)
            message_type: The type of message
            content: The message content
            metadata: Metadata for the connector instance
            
        Returns:
            Dictionary with sending results
        """
        # This is a placeholder for HTTP message sending
        logger.warning("HTTP message sending not implemented yet")
        return {
            "success": False,
            "error": "HTTP message sending not implemented yet"
        }
    
    def handle_webhook_verification(self, channel: str, params: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle webhook verification for a specific channel.
        Used for initial setup of webhook endpoints.
        
        Args:
            channel: The channel type (e.g., "WHATSAPP")
            params: Verification parameters
            metadata: Metadata for the connector instance
            
        Returns:
            Dictionary with verification results
        """
        logger.info(f"Handling webhook verification for {channel}")
        
        try:
            if channel == "WHATSAPP":
                return self.registry.execute_action(
                    "WHATSAPP",
                    metadata,
                    "verify_webhook",
                    params
                )
            else:
                logger.error(f"Webhook verification not implemented for channel: {channel}")
                return {
                    "success": False,
                    "error": f"Webhook verification not implemented for channel: {channel}"
                }
                
        except Exception as e:
            logger.error(f"Error during webhook verification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
