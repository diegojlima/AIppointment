"""
AppointmentCreator action group for AWS Bedrock Agent

This action group handles:
- Checking calendar availability
- Creating new appointments
- Generating confirmation messages
"""
import json
import logging
import boto3
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List
from botocore.exceptions import ClientError

# Add parent directory to Python path to fix imports
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import calendar integration
from calendar_integration import CalendarIntegration, CalendarProvider

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class AppointmentCreator:
    """
    Action group for creating and managing appointments
    """
    
    def __init__(self, dynamodb_client=None, calendar_integration=None):
        """
        Initialize the AppointmentCreator action group
        
        Args:
            dynamodb_client: Optional DynamoDB client
            calendar_integration: Optional calendar integration service
        """
        self.dynamodb = dynamodb_client or boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE', 'appointment-system-appointments')
        
        # If calendar integration is provided, use it
        self.calendar_integration = calendar_integration
        
        # Log initialization
        logger.info("AppointmentCreator action group initialized")
    
    def check_availability(self, date: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Check available time slots for a given date
        
        Args:
            date: The date to check in ISO format (YYYY-MM-DD)
            duration_minutes: Duration of the appointment in minutes
            
        Returns:
            Dictionary with available time slots
        """
        logger.info(f"Checking availability for date: {date}")
        
        try:
            # Business hours (9 AM to 5 PM)
            business_start = "09:00"
            business_end = "17:00"
            
            # If calendar integration is available, use it
            if self.calendar_integration:
                # Get the default provider - safely handle if it's not available as a property
                try:
                    default_provider = self.calendar_integration.default_calendar_provider
                except AttributeError:
                    # If default_calendar_provider is not available, use GOOGLE as default
                    default_provider = CalendarProvider.GOOGLE
                    logger.info(f"Using {default_provider.value} as default calendar provider")
                
                available_slots = self.calendar_integration.check_availability(
                    provider=default_provider,
                    date=date,
                    start_time=business_start,
                    end_time=business_end
                )
                
                # Format the slots
                formatted_slots = []
                for slot in available_slots:
                    slot_start = datetime.fromisoformat(slot["start"])
                    slot_end = datetime.fromisoformat(slot["end"])
                    
                    formatted_slots.append({
                        "startTime": slot_start.strftime("%H:%M"),
                        "endTime": slot_end.strftime("%H:%M"),
                        "available": True
                    })
                
                return {
                    "date": date,
                    "availableSlots": formatted_slots,
                    "success": True
                }
            else:
                # Mock available slots for demonstration
                available_slots = [
                    {"startTime": "09:00", "endTime": "10:00", "available": True},
                    {"startTime": "10:00", "endTime": "11:00", "available": True},
                    {"startTime": "11:00", "endTime": "12:00", "available": True},
                    {"startTime": "13:00", "endTime": "14:00", "available": True},
                    {"startTime": "14:00", "endTime": "15:00", "available": True},
                    {"startTime": "15:00", "endTime": "16:00", "available": True},
                    {"startTime": "16:00", "endTime": "17:00", "available": True}
                ]
                
                return {
                    "date": date,
                    "availableSlots": available_slots,
                    "success": True
                }
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return {
                "date": date,
                "availableSlots": [],
                "success": False,
                "error": str(e)
            }
    
    def create_appointment(self, 
                           user_id: str, 
                           date: str, 
                           time: str, 
                           purpose: str,
                           duration_minutes: int = 60,
                           user_email: str = None) -> Dict[str, Any]:
        """
        Create a new appointment
        
        Args:
            user_id: Unique identifier for the user (e.g., phone number)
            date: The date for the appointment (YYYY-MM-DD)
            time: The time for the appointment (HH:MM)
            purpose: The purpose of the appointment
            duration_minutes: Duration of the appointment in minutes
            user_email: Optional email for calendar invitations
            
        Returns:
            Dictionary with appointment details and status
        """
        logger.info(f"Creating appointment for user {user_id} on {date} at {time}")
        
        try:
            # Validate the appointment date and time
            logger.info("Validating appointment date and time")
            appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            
            if appointment_datetime < now:
                logger.info(f"Appointment date/time {date} {time} is in the past")
                return {
                    "success": False,
                    "error": "Appointment date/time is in the past"
                }
            
            # Create a unique appointment ID
            appointment_id = f"{user_id}-{date}-{time}".replace(":", "")
            logger.info(f"Generated appointment ID: {appointment_id}")
            
            # Calculate end time
            end_time = (appointment_datetime + timedelta(minutes=duration_minutes)).strftime("%H:%M")
            logger.info(f"Calculated end time: {end_time}")
            
            # Create the appointment item
            logger.info("Creating DynamoDB item")
            appointment_item = {
                'PhoneNumber': {'S': user_id},
                'CreatedAt': {'S': datetime.utcnow().isoformat()},
                'date': {'S': date},
                'startTime': {'S': time},
                'endTime': {'S': end_time},
                'purpose': {'S': purpose},
                'durationMinutes': {'N': str(duration_minutes)},
                'status': {'S': 'confirmed'},
                'appointmentId': {'S': appointment_id}
            }
            
            # Add optional email
            if user_email:
                appointment_item['userEmail'] = {'S': user_email}
                logger.info(f"Added user email: {user_email} to appointment")
            
            # Save to DynamoDB
            logger.info(f"Saving appointment to DynamoDB table: {self.table_name}")
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=appointment_item
            )
            logger.info("Successfully saved appointment to DynamoDB")
            
            # If calendar integration is available, add to calendar
            calendar_link = None
            if self.calendar_integration:
                logger.info("Calendar integration available")
                # Get the default provider - safely handle if it's not available as a property
                try:
                    logger.info("Attempting to get default calendar provider")
                    default_provider = self.calendar_integration.default_calendar_provider
                    logger.info(f"Using default calendar provider: {default_provider.value}")
                except AttributeError as e:
                    # If default_calendar_provider is not available, use GOOGLE as default
                    logger.info(f"Error getting default calendar provider: {str(e)}")
                    default_provider = CalendarProvider.GOOGLE
                    logger.info(f"Using {default_provider.value} as default calendar provider")
                
                try:
                    logger.info("Preparing to book appointment in calendar")
                    appointment_details = {
                        "date": date,
                        "time": time,
                        "duration_minutes": duration_minutes,
                        "purpose": purpose
                    }
                    
                    # Only add attendee_email if provided, but don't require it
                    if user_email:
                        appointment_details["attendee_email"] = user_email
                        
                    logger.info(f"Appointment details for calendar: {appointment_details}")
                    
                    logger.info("Calling calendar_integration.book_appointment")
                    calendar_result = self.calendar_integration.book_appointment(
                        provider=default_provider,
                        appointment_details=appointment_details
                    )
                    logger.info(f"Calendar integration result: {calendar_result}")
                    
                    if calendar_result["success"]:
                        calendar_link = calendar_result.get("appointment_details", {}).get("htmlLink")
                        logger.info(f"Successfully booked in calendar. Link: {calendar_link}")
                    else:
                        logger.info(f"Failed to book in calendar: {calendar_result.get('error')}")
                except Exception as e:
                    logger.error(f"Exception during calendar booking: {str(e)}", exc_info=True)
            else:
                logger.info("No calendar integration available")
            
            return {
                "appointmentId": appointment_id,
                "userId": user_id,
                "date": date,
                "startTime": time,
                "endTime": end_time,
                "purpose": purpose,
                "status": "confirmed",
                "calendarLink": calendar_link,
                "success": True
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error creating appointment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_confirmation(self, appointment_id: str) -> Dict[str, Any]:
        """
        Generate a confirmation message for an appointment
        
        Args:
            appointment_id: The ID of the appointment
            
        Returns:
            Dictionary with confirmation message and details
        """
        logger.info(f"Generating confirmation for appointment: {appointment_id}")
        
        try:
            # Get the appointment from DynamoDB
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'id': {'S': appointment_id}
                }
            )
            
            # Check if the appointment exists
            if 'Item' not in response:
                return {
                    "success": False,
                    "error": "Appointment not found"
                }
            
            # Extract appointment details
            appointment = {k: list(v.values())[0] for k, v in response['Item'].items()}
            
            # Format the confirmation message
            date_formatted = datetime.strptime(appointment['date'], "%Y-%m-%d").strftime("%A, %B %d, %Y")
            
            confirmation_message = (
                f"Your appointment has been confirmed for {date_formatted} at {appointment['startTime']}. "
                f"Purpose: {appointment['purpose']}. "
                f"Please arrive 10 minutes early."
            )
            
            # Add calendar link if available
            if 'calendarLink' in appointment:
                confirmation_message += f" You can view and manage this appointment in your calendar: {appointment['calendarLink']}"
            
            return {
                "appointmentId": appointment_id,
                "confirmationMessage": confirmation_message,
                "appointmentDetails": appointment,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating confirmation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Lambda handler for the action group
def lambda_handler(event, context):
    """
    Lambda handler for the AppointmentCreator action group
    
    Args:
        event: The Lambda event
        context: The Lambda context
        
    Returns:
        Dictionary with the action response formatted for AWS Bedrock Agents
    """
    try:
        # First, let's log the raw event for debugging
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Defensive approach - always stringify then parse the event
        if isinstance(event, str):
            try:
                event = json.loads(event)
            except json.JSONDecodeError:
                return format_bedrock_response({
                    "error": "Invalid event format: not valid JSON"
                })
        
        # Extract the action name from apiPath and actionGroup
        try:
            action_group_name = event.get('actionGroup')
            if not action_group_name:
                return format_bedrock_response({"error": "Missing actionGroup in event"})
                
            api_path = event.get('apiPath')
            if not api_path:
                return format_bedrock_response({"error": "Missing apiPath in event"})
            
            http_method = event.get('httpMethod')
            if not http_method:
                return format_bedrock_response({"error": "Missing httpMethod in event"})
            
            # Map API paths to action names
            api_path_to_action = {
                "/appointments": "createAppointment",
                "/appointments/availability": "checkAvailability",
                "/appointments/confirmation": "generateConfirmation"
            }
            
            action_name = api_path_to_action.get(api_path)
            if not action_name:
                return format_bedrock_response({
                    "error": f"Unknown API path: {api_path}"
                }, action_group_name, api_path, http_method)
                
        except Exception as e:
            logger.error(f"Event structure error: {str(e)}")
            return format_bedrock_response({"error": f"Invalid event format: {str(e)}"})
        
        # Process parameters - support both parameters array and requestBody
        parameters = {}
        
        # Process parameters from list format (Bedrock Agents format)
        params_list = event.get('parameters', [])
        for param in params_list:
            if isinstance(param, dict) and 'name' in param and 'value' in param:
                parameters[param['name']] = param['value']
        
        # Process requestBody if present (for POST requests)
        request_body = event.get('requestBody', {})
        if request_body and isinstance(request_body, dict):
            content = request_body.get('content', {})
            if content and isinstance(content, dict):
                json_content = content.get('application/json', {})
                if json_content and isinstance(json_content, dict):
                    properties = json_content.get('properties', [])
                    if properties and isinstance(properties, list):
                        for prop in properties:
                            if isinstance(prop, dict) and 'name' in prop and 'value' in prop:
                                parameters[prop['name']] = prop['value']
        
        logger.info(f"Processed parameters: {parameters}")
        
        # Initialize the calendar integration and action group
        try:
            logger.info("Initializing calendar integration service")
            calendar_integration = CalendarIntegration()
            logger.info("Calendar integration service initialized successfully")
            
            # Initialize the action group with calendar integration
            action_group_instance = AppointmentCreator(calendar_integration=calendar_integration)
            logger.info("AppointmentCreator initialized with calendar integration")
        except Exception as e:
            logger.info(f"Calendar integration initialization failed: {str(e)}")
            # Fallback to no calendar integration
            action_group_instance = AppointmentCreator()
            logger.info("AppointmentCreator initialized without calendar integration")
        
        # Route to the appropriate method based on the action_name
        if action_name == 'checkAvailability':
            date = parameters.get('date')
            if not date:
                return format_bedrock_response({
                    "error": "Missing required parameter: date"
                }, action_group_name, api_path, http_method)
                
            # Support both snake_case and camelCase parameter names
            try:
                duration_minutes = int(parameters.get('durationMinutes') or parameters.get('duration_minutes', 60))
            except (ValueError, TypeError):
                duration_minutes = 60
            
            result = action_group_instance.check_availability(date, duration_minutes)
            return format_bedrock_response(result, action_group_name, api_path, http_method)
        
        elif action_name == 'createAppointment':
            # Extract required parameters
            user_id = parameters.get('userId') or parameters.get('user_id')
            if not user_id:
                return format_bedrock_response({
                    "error": "Missing required parameter: userId"
                }, action_group_name, api_path, http_method)
                
            date = parameters.get('date')
            if not date:
                return format_bedrock_response({
                    "error": "Missing required parameter: date"
                }, action_group_name, api_path, http_method)
                
            time = parameters.get('time')
            if not time:
                return format_bedrock_response({
                    "error": "Missing required parameter: time"
                }, action_group_name, api_path, http_method)
                
            purpose = parameters.get('purpose')
            if not purpose:
                return format_bedrock_response({
                    "error": "Missing required parameter: purpose"
                }, action_group_name, api_path, http_method)
            
            # Optional parameters
            try:
                duration_minutes = int(parameters.get('durationMinutes') or parameters.get('duration_minutes', 60))
            except (ValueError, TypeError):
                duration_minutes = 60
                
            # Email is completely optional now
            user_email = parameters.get('userEmail') or parameters.get('user_email')
            
            # NOTE: We're not extracting email from session state or input text since email is now optional
            
            result = action_group_instance.create_appointment(
                user_id, date, time, purpose, duration_minutes, user_email
            )
            return format_bedrock_response(result, action_group_name, api_path, http_method)
        
        elif action_name == 'generateConfirmation':
            appointment_id = parameters.get('appointmentId') or parameters.get('appointment_id')
            if not appointment_id:
                return format_bedrock_response({
                    "error": "Missing required parameter: appointmentId"
                }, action_group_name, api_path, http_method)
                
            result = action_group_instance.generate_confirmation(appointment_id)
            return format_bedrock_response(result, action_group_name, api_path, http_method)
        
        else:
            return format_bedrock_response({
                "error": f"Unknown action: {action_name}"
            }, action_group_name, api_path, http_method)
            
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}", exc_info=True)
        # Even in error case, try to include original action_group, api_path and http_method if available
        action_group_name = event.get('actionGroup', 'AppointmentCreator') if isinstance(event, dict) else 'AppointmentCreator'
        api_path = event.get('apiPath', '/appointments') if isinstance(event, dict) else '/appointments'
        http_method = event.get('httpMethod', 'POST') if isinstance(event, dict) else 'POST'
        
        return format_bedrock_response({
            "error": f"Internal server error: {str(e)}"
        }, action_group_name, api_path, http_method)

def format_bedrock_response(result, action_group=None, api_path=None, http_method=None):
    """
    Format the response for AWS Bedrock Agents
    
    Args:
        result: The result dict from the action
        action_group: The action group name from the request
        api_path: The API path from the request
        http_method: The HTTP method from the request
        
    Returns:
        Properly formatted response for Bedrock Agents
    """
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group or "AppointmentCreator",
            "apiPath": api_path,
            "httpMethod": http_method,
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": result
                }
            }
        }
    }
