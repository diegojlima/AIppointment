
# functions/appointment-booking/src/whatsapp_connector.py
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from connector_registry import ConnectorInterface

logger = logging.getLogger(__name__)

class WhatsAppConnector(ConnectorInterface):
    """
    WhatsApp Business API connector for sending messages and processing webhooks.
    Implements the WhatsApp Cloud API from Meta.
    
    This connector supports:
    - Sending text messages
    - Sending template messages
    - Verifying webhooks
    - Processing incoming messages
    
    Documentation references:
    - https://developers.facebook.com/docs/whatsapp/cloud-api/overview
    - https://developers.facebook.com/docs/whatsapp/cloud-api/reference
    """
    
    def __init__(self, metadata: Dict[str, Any], connection_params: Dict[str, Any]):
        """
        Initialize the WhatsApp Business API connector.
        
        Args:
            metadata: Dictionary containing:
                - phone_number_id: WhatsApp Business phone number ID
                - business_account_id: WhatsApp Business Account ID
            connection_params: Dictionary containing:
                - access_token: Token for WhatsApp Business API authentication
                - webhook_verify_token: Token for webhook verification
                - api_version: WhatsApp API version (default: v17.0)
        """
        self.metadata = metadata
        self.connection_params = connection_params
        
        # Extract required metadata
        self.phone_number_id = metadata.get("phone_number_id")
        self.business_account_id = metadata.get("business_account_id")
        
        # Extract connection parameters
        self.access_token = connection_params.get("access_token")
        self.webhook_verify_token = connection_params.get("webhook_verify_token")
        self.api_version = connection_params.get("api_version", "v17.0")
        
        # Build base URL for API requests
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        logger.info(f"WhatsApp connector initialized for phone_number_id: {self.phone_number_id}")
    
    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        """
        Execute a WhatsApp Business API action.
        
        Supported actions:
        - send_text_message: Send a simple text message
        - send_template_message: Send a message with template
        - verify_webhook: Verify webhook URL for subscription
        - process_webhook: Process incoming webhook payload
        
        Args:
            action_name: The name of the action to execute
            params: Parameters for the action
            
        Returns:
            Dictionary with action results
        """
        logger.info(f"Executing WhatsApp action '{action_name}' with params: {params}")
        
        if action_name == "send_text_message":
            return self._send_text_message(
                recipient_phone=params.get("recipient_phone"),
                message_text=params.get("message_text")
            )
        
        elif action_name == "send_template_message":
            return self._send_template_message(
                recipient_phone=params.get("recipient_phone"),
                template_name=params.get("template_name"),
                language_code=params.get("language_code", "en_US"),
                components=params.get("components", [])
            )
        
        elif action_name == "verify_webhook":
            return self._verify_webhook(
                mode=params.get("mode"),
                verify_token=params.get("verify_token"),
                challenge=params.get("challenge")
            )
        
        elif action_name == "process_webhook":
            return self._process_webhook(params.get("payload", {}))
            
        else:
            logger.error(f"Unknown action: {action_name}")
            return {"success": False, "error": f"Unknown action: {action_name}"}
    
    def _send_text_message(self, recipient_phone: str, message_text: str) -> Dict[str, Any]:
        """
        Send a text message to a WhatsApp user.
        
        Args:
            recipient_phone: Recipient's phone number (without +)
            message_text: The text to send
            
        Returns:
            Dictionary with response status and message ID
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "")
            
            logger.info(f"Message sent successfully. Message ID: {message_id}")
            return {
                "success": True,
                "message_id": message_id,
                "raw_response": data
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _send_template_message(
        self, 
        recipient_phone: str, 
        template_name: str,
        language_code: str,
        components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send a template message to a WhatsApp user.
        
        Args:
            recipient_phone: Recipient's phone number (without +)
            template_name: The name of the template to use
            language_code: Language code for the template (e.g., en_US)
            components: List of template components with parameters
            
        Returns:
            Dictionary with response status and message ID
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                },
                "components": components
            }
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "")
            
            logger.info(f"Template message sent successfully. Message ID: {message_id}")
            return {
                "success": True,
                "message_id": message_id,
                "raw_response": data
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending template message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _verify_webhook(self, mode: str, verify_token: str, challenge: str) -> Dict[str, Any]:
        """
        Verify a webhook subscription.
        
        When setting up a webhook, Facebook will send a challenge request to verify ownership.
        This method handles that verification process.
        
        Args:
            mode: Should be 'subscribe'
            verify_token: Token to verify against the configured webhook_verify_token
            challenge: Challenge string to return if verification is successful
            
        Returns:
            Dictionary with verification status and challenge if successful
        """
        logger.info(f"Verifying webhook with mode: {mode}, token: {verify_token}")
        
        if mode == "subscribe" and verify_token == self.webhook_verify_token:
            logger.info("Webhook verified successfully")
            return {
                "success": True,
                "hub.challenge": challenge
            }
        else:
            logger.error("Webhook verification failed - token mismatch")
            return {
                "success": False,
                "error": "Verification failed - token mismatch"
            }
    
    def _process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming webhook payload from WhatsApp.
        
        Extracts messages and relevant metadata from the webhook payload.
        
        Args:
            payload: The webhook payload from WhatsApp
            
        Returns:
            Dictionary with processing results and extracted messages
        """
        logger.info("Processing webhook payload")
        
        try:
            # Verify this is a WhatsApp Business webhook
            if payload.get("object") != "whatsapp_business_account":
                logger.error(f"Invalid object type: {payload.get('object')}")
                return {
                    "success": False,
                    "error": f"Invalid object type: {payload.get('object')}"
                }
            
            # Extract messages from the payload
            processed_messages = []
            
            for entry in payload.get("entry", []):
                # Verify this is for our business account
                if entry.get("id") != self.business_account_id:
                    logger.warning(f"Business account ID mismatch: {entry.get('id')}")
                    continue
                
                for change in entry.get("changes", []):
                    if change.get("field") != "messages":
                        continue
                    
                    value = change.get("value", {})
                    
                    # Check if this is for our phone number ID
                    metadata = value.get("metadata", {})
                    if metadata.get("phone_number_id") != self.phone_number_id:
                        logger.warning(f"Phone number ID mismatch: {metadata.get('phone_number_id')}")
                        continue
                    
                    # Process each message
                    for message in value.get("messages", []):
                        processed_message = self._extract_message_data(message)
                        if processed_message:
                            processed_messages.append(processed_message)
            
            logger.info(f"Processed {len(processed_messages)} messages")
            return {
                "success": True,
                "messages": processed_messages
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _extract_message_data(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract relevant data from a message object.
        
        Args:
            message: Message object from the webhook payload
            
        Returns:
            Dictionary with extracted message data
        """
        try:
            message_type = message.get("type")
            
            result = {
                "message_id": message.get("id"),
                "phone_number": message.get("from"),
                "timestamp": message.get("timestamp"),
                "type": message_type
            }
            
            # Extract content based on message type
            if message_type == "text":
                result["text"] = message.get("text", {}).get("body", "")
            
            elif message_type == "image":
                result["image"] = {
                    "id": message.get("image", {}).get("id"),
                    "mime_type": message.get("image", {}).get("mime_type")
                }
            
            elif message_type == "audio":
                result["audio"] = {
                    "id": message.get("audio", {}).get("id"),
                    "mime_type": message.get("audio", {}).get("mime_type")
                }
            
            elif message_type == "button":
                result["button"] = {
                    "text": message.get("button", {}).get("text"),
                    "payload": message.get("button", {}).get("payload")
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting message data: {str(e)}")
            return None
    
    @classmethod
    def get_full_instance_mapping_path(cls, metadata: Dict[str, Any]) -> str:
        """
        Return a unique key for an instance given its metadata.
        
        Args:
            metadata: Dictionary with metadata
            
        Returns:
            String with the instance mapping path
        """
        return f"whatsapp_{metadata.get('phone_number_id')}"
    
    @classmethod
    def validate_connector_metadata(cls, metadata: Dict[str, Any]) -> None:
        """
        Validate that the metadata meets requirements for this connector.
        
        Args:
            metadata: Dictionary with metadata
            
        Raises:
            ValueError: If metadata is invalid
        """
        if "phone_number_id" not in metadata:
            raise ValueError("WhatsApp connector metadata must include 'phone_number_id'")
        
        if "business_account_id" not in metadata:
            raise ValueError("WhatsApp connector metadata must include 'business_account_id'")
