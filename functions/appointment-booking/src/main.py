"""
Main entry point for the AIppointment application.

This Lambda function serves as the entry point for the application, handling:
- WhatsApp integration via AWS End User Messaging
- Conversation management via AWS Bedrock Agents
- Appointment booking and management
"""
import json
import boto3
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Import the input adapter for normalizing inputs
from input_adapter import normalize_input

# Import calendar integration
from calendar_integration import CalendarIntegration, CalendarProvider

# Import WhatsApp messaging
from whatsapp_integration import WhatsAppMessaging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
dynamodb = boto3.client('dynamodb')

# Environment variables
BEDROCK_AGENT_ID = os.environ.get('BEDROCK_AGENT_ID')
BEDROCK_AGENT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'Appointments')
CONVERSATION_HISTORY_TABLE = os.environ.get('CONVERSATION_HISTORY_TABLE', 'ConversationHistory')
DEFAULT_CALENDAR_PROVIDER = os.environ.get('DEFAULT_CALENDAR_PROVIDER', 'GOOGLE')

def get_or_create_conversation_id(sender_id: str) -> str:
    """
    Get an existing conversation ID or create a new one
    
    Args:
        sender_id: The sender's identifier (e.g., phone number)
        
    Returns:
        A conversation ID
    """
    try:
        # Query the conversation history table
        response = dynamodb.query(
            TableName=CONVERSATION_HISTORY_TABLE,
            IndexName="SenderIdIndex",
            KeyConditionExpression="senderId = :senderId",
            ExpressionAttributeValues={
                ":senderId": {"S": sender_id}
            },
            Limit=1,
            ScanIndexForward=False  # Get the most recent conversation
        )
        
        items = response.get('Items', [])
        
        # If a recent conversation exists (within 24 hours), use it
        if items:
            last_conversation = items[0]
            conversation_id = last_conversation.get('conversationId', {}).get('S')
            last_update = datetime.fromisoformat(last_conversation.get('updatedAt', {}).get('S'))
            now = datetime.utcnow()
            
            # If conversation is less than 24 hours old, use it
            if (now - last_update).total_seconds() < 86400:  # 24 hours in seconds
                logger.info(f"Using existing conversation ID: {conversation_id}")
                
                # Update the last interaction timestamp
                dynamodb.update_item(
                    TableName=CONVERSATION_HISTORY_TABLE,
                    Key={
                        'conversationId': {'S': conversation_id}
                    },
                    UpdateExpression="SET updatedAt = :updatedAt",
                    ExpressionAttributeValues={
                        ':updatedAt': {'S': now.isoformat()}
                    }
                )
                
                return conversation_id
        
        # Create a new conversation ID
        new_conversation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Store in DynamoDB
        dynamodb.put_item(
            TableName=CONVERSATION_HISTORY_TABLE,
            Item={
                'conversationId': {'S': new_conversation_id},
                'senderId': {'S': sender_id},
                'createdAt': {'S': timestamp},
                'updatedAt': {'S': timestamp},
                'messageCount': {'N': '0'}
            }
        )
        
        logger.info(f"Created new conversation ID: {new_conversation_id}")
        return new_conversation_id
        
    except Exception as e:
        logger.error(f"Error managing conversation: {str(e)}")
        # Fallback to a new conversation ID
        return str(uuid.uuid4())

def store_conversation_message(conversation_id: str, sender_id: str, user_message: str, agent_response: str) -> None:
    """
    Store the conversation history in DynamoDB
    
    Args:
        conversation_id: The conversation ID
        sender_id: The sender's identifier
        user_message: The user's message
        agent_response: The agent's response
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        message_id = str(uuid.uuid4())
        
        # Update conversation record
        dynamodb.update_item(
            TableName=CONVERSATION_HISTORY_TABLE,
            Key={
                'conversationId': {'S': conversation_id}
            },
            UpdateExpression="SET updatedAt = :timestamp, messageCount = messageCount + :inc",
            ExpressionAttributeValues={
                ':timestamp': {'S': timestamp},
                ':inc': {'N': '1'}
            }
        )
        
        # Add message to conversation messages table
        dynamodb.put_item(
            TableName=f"{CONVERSATION_HISTORY_TABLE}Messages",
            Item={
                'messageId': {'S': message_id},
                'conversationId': {'S': conversation_id},
                'senderId': {'S': sender_id},
                'userMessage': {'S': user_message},
                'agentResponse': {'S': agent_response},
                'timestamp': {'S': timestamp}
            }
        )
        
        logger.info(f"Stored conversation message {message_id} for conversation {conversation_id}")
        
    except Exception as e:
        logger.error(f"Error storing conversation message: {str(e)}")

def invoke_bedrock_agent(message: str, conversation_id: str, sender_id: str) -> Dict[str, Any]:
    """
    Send a message to AWS Bedrock Agent and get a response
    
    Args:
        message: The user's message
        conversation_id: The conversation ID
        sender_id: The sender's identifier
        
    Returns:
        The agent's response
    """
    try:
        logger.info(f"Invoking Bedrock Agent for conversation {conversation_id}")
        
        # Prepare session state with user context
        session_state = {
            'userId': sender_id
        }
        
        # If calendar integration is needed, add calendar provider
        calendar_provider = DEFAULT_CALENDAR_PROVIDER
        if calendar_provider:
            session_state['calendarProvider'] = calendar_provider
        
        # Invoke the agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId=conversation_id,
            inputText=message,
            sessionState=json.dumps(session_state)
        )
        
        logger.info(f"Bedrock Agent response received for conversation {conversation_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error invoking Bedrock Agent: {str(e)}")
        # Return a fallback response
        return {
            "completion": "I'm sorry, I'm having trouble processing your request right now. Please try again later."
        }

def format_agent_response(agent_response: Dict[str, Any]) -> str:
    """
    Format the agent response for the user
    
    Args:
        agent_response: The raw agent response
        
    Returns:
        Formatted response text
    """
    try:
        # Extract the text response
        completion = agent_response.get('completion', '')
        
        # You could add additional formatting here if needed
        
        return completion
        
    except Exception as e:
        logger.error(f"Error formatting agent response: {str(e)}")
        return "I'm sorry, I couldn't process your request at this time."

def handle_whatsapp_message(normalized_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle an incoming WhatsApp message
    
    Args:
        normalized_input: The normalized input from the adapter
        
    Returns:
        Response to be sent back to the user
    """
    try:
        # Extract message details
        phone_number = normalized_input.get('phone_number')
        message = normalized_input.get('message')
        
        # Get or create a conversation ID
        conversation_id = get_or_create_conversation_id(phone_number)
        
        # Invoke Bedrock Agent
        agent_response = invoke_bedrock_agent(message, conversation_id, phone_number)
        
        # Format the response
        formatted_response = format_agent_response(agent_response)
        
        # Store the conversation
        store_conversation_message(
            conversation_id=conversation_id,
            sender_id=phone_number,
            user_message=message,
            agent_response=formatted_response
        )
        
        # Initialize WhatsApp messaging
        whatsapp = WhatsAppMessaging()
        
        # Send the response back to WhatsApp
        whatsapp_response = whatsapp.send_text_message(
            recipient_id=phone_number,
            message=formatted_response
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Message processed successfully',
                'conversation_id': conversation_id,
                'whatsapp_response': whatsapp_response
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling WhatsApp message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Error handling WhatsApp message: {str(e)}"})
        }

def lambda_handler(event, context):
    """
    Main Lambda handler function
    
    Args:
        event: The Lambda event
        context: The Lambda context
        
    Returns:
        Response object
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Check if this is a webhook verification request
        if event.get('queryStringParameters'):
            # This might be a webhook verification request
            params = event.get('queryStringParameters', {})
            mode = params.get('hub.mode')
            verify_token = params.get('hub.verify_token')
            challenge = params.get('hub.challenge')
            
            if mode == 'subscribe' and verify_token and challenge:
                # Initialize WhatsApp messaging
                whatsapp = WhatsAppMessaging()
                
                # Verify the webhook with WhatsApp
                verification_token = os.environ.get('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
                
                if verify_token == verification_token:
                    logger.info("Webhook verified successfully")
                    return {
                        'statusCode': 200,
                        'body': challenge
                    }
                else:
                    logger.error("Webhook verification failed - token mismatch")
                    return {
                        'statusCode': 403,
                        'body': json.dumps({'error': 'Verification failed'})
                    }
        
        # Normalize input from various channels
        normalized_input = normalize_input(event)
        
        # Check the channel and route accordingly
        channel = normalized_input.get('channel', 'unknown')
        
        if channel == 'whatsapp':
            return handle_whatsapp_message(normalized_input)
        else:
            # Default handling for other channels
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unsupported channel: {channel}'})
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
