"""
WhatsApp integration module using AWS End User Messaging

This module handles:
- Integration with WhatsApp Business API through AWS End User Messaging
- Sending and receiving messages 
- Formatting rich WhatsApp messages (templates, buttons, lists)
"""
import json
import logging
import boto3
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class WhatsAppMessaging:
    """
    Handles messaging through WhatsApp Business API via AWS End User Messaging
    """
    
    def __init__(self, messaging_client=None):
        """
        Initialize WhatsApp messaging service
        
        Args:
            messaging_client: Optional End User Messaging client
        """
        # Initialize AWS End User Messaging client
        if messaging_client:
            self.messaging = messaging_client
        else:
            self.messaging = boto3.client('connectmessagingservice')
        
        # Get the WhatsApp phone number ID from environment variables
        self.phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
        
        # If no phone number ID is provided, log a warning
        if not self.phone_number_id:
            logger.warning("WHATSAPP_PHONE_NUMBER_ID environment variable not set")
            self.phone_number_id = "default_phone_number_id"
        
        logger.info(f"WhatsApp messaging service initialized with phone number ID: {self.phone_number_id}")
    
    def send_text_message(self, recipient_id: str, message: str) -> Dict[str, Any]:
        """
        Send a simple text message to a WhatsApp user
        
        Args:
            recipient_id: The recipient's phone number
            message: The message text to send
            
        Returns:
            Response from the WhatsApp API
        """
        logger.info(f"Sending text message to {recipient_id}")
        
        try:
            response = self.messaging.send_message(
                DestinationPhoneNumber=recipient_id,
                OriginationIdentity=self.phone_number_id,
                MessageType='TEXT',
                Content={
                    'TextMessage': {
                        'Message': message
                    }
                }
            )
            
            logger.info(f"Message sent successfully to {recipient_id}")
            return {
                'success': True,
                'message_id': response.get('MessageId'),
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"Error sending text message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_template_message(
        self, 
        recipient_id: str, 
        template_name: str,
        language_code: str = 'en_US',
        components: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a template message to a WhatsApp user
        
        Args:
            recipient_id: The recipient's phone number
            template_name: The WhatsApp template name
            language_code: The language code for the template
            components: Template components (header, body, buttons)
            
        Returns:
            Response from the WhatsApp API
        """
        logger.info(f"Sending template message {template_name} to {recipient_id}")
        
        try:
            # Build the template content
            template_content = {
                'WhatsAppTemplate': {
                    'Name': template_name,
                    'LanguageCode': language_code
                }
            }
            
            # Add components if provided
            if components:
                template_content['WhatsAppTemplate']['Components'] = components
            
            # Send the message
            response = self.messaging.send_message(
                DestinationPhoneNumber=recipient_id,
                OriginationIdentity=self.phone_number_id,
                MessageType='TEMPLATE',
                Content=template_content
            )
            
            logger.info(f"Template message sent successfully to {recipient_id}")
            return {
                'success': True,
                'message_id': response.get('MessageId'),
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"Error sending template message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_appointment_confirmation(
        self, 
        recipient_id: str, 
        date: str, 
        time: str, 
        purpose: str
    ) -> Dict[str, Any]:
        """
        Send an appointment confirmation message
        
        Args:
            recipient_id: The recipient's phone number
            date: The appointment date
            time: The appointment time
            purpose: The appointment purpose
            
        Returns:
            Response from the WhatsApp API
        """
        logger.info(f"Sending appointment confirmation to {recipient_id}")
        
        try:
            # Format the date for display
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            
            # Create the message content
            message = (
                f"✅ *Appointment Confirmed*\n\n"
                f"📅 Date: {formatted_date}\n"
                f"⏰ Time: {time}\n"
                f"🔍 Purpose: {purpose}\n\n"
                f"Please arrive 10 minutes early. Reply 'CANCEL' if you need to cancel."
            )
            
            # Send the message
            return self.send_text_message(recipient_id, message)
            
        except Exception as e:
            logger.error(f"Error sending appointment confirmation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_appointment_reminder(
        self, 
        recipient_id: str, 
        date: str, 
        time: str, 
        purpose: str
    ) -> Dict[str, Any]:
        """
        Send an appointment reminder message
        
        Args:
            recipient_id: The recipient's phone number
            date: The appointment date
            time: The appointment time
            purpose: The appointment purpose
            
        Returns:
            Response from the WhatsApp API
        """
        logger.info(f"Sending appointment reminder to {recipient_id}")
        
        try:
            # Format the date for display
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            
            # Create the message content
            message = (
                f"🔔 *Appointment Reminder*\n\n"
                f"📅 Date: {formatted_date}\n"
                f"⏰ Time: {time}\n"
                f"🔍 Purpose: {purpose}\n\n"
                f"We look forward to seeing you soon! Reply 'RESCHEDULE' if you need to change your appointment."
            )
            
            # Send the message
            return self.send_text_message(recipient_id, message)
            
        except Exception as e:
            logger.error(f"Error sending appointment reminder: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_webhook_event(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a WhatsApp webhook event
        
        Args:
            body: The webhook request body
            
        Returns:
            Normalized message data
        """
        logger.info("Processing WhatsApp webhook event")
        
        try:
            # Extract the message details
            normalized_input = {
                'channel': 'whatsapp',
                'phone_number': None,
                'message': None,
                'session_id': None
            }
            
            # Check if this is a WhatsApp message
            if 'object' in body and body['object'] == 'whatsapp_business_account':
                for entry in body.get('entry', []):
                    for change in entry.get('changes', []):
                        if change.get('field') == 'messages':
                            value = change.get('value', {})
                            
                            for message in value.get('messages', []):
                                # Extract the phone number
                                normalized_input['phone_number'] = message.get('from')
                                
                                # Extract the message text
                                if message.get('type') == 'text':
                                    normalized_input['message'] = message.get('text', {}).get('body')
                                
                                # Extract message ID for session tracking
                                normalized_input['session_id'] = message.get('id')
                                
                                # Process only the first message for simplicity
                                break
            
            logger.info(f"Normalized webhook event: {normalized_input}")
            return normalized_input
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}")
            return {
                'channel': 'whatsapp',
                'error': str(e)
            }
