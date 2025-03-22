"""
Bedrock Calendar Adapter for AWS Bedrock Agent

This file serves as an adapter/wrapper between the core calendar integration service
and AWS Bedrock Agent. It translates between the Bedrock Agent API format and our 
internal calendar integration service.

Key responsibilities:
- Formats requests from Bedrock Agent into calls to our calendar service
- Formats responses from our calendar service into Bedrock Agent compatible format
- Handles AWS Bedrock Agent specific request/response formatting
- Provides a Lambda handler for AWS Bedrock Agent integration

This adapter uses the core CalendarIntegration class from calendar_integration.py
which contains the actual business logic for calendar operations.
"""
import json
import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os

# Add parent directory to Python path to fix imports
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import calendar integration
import importlib
from typing import Optional, Type

# Dynamic imports for better resilience
def import_calendar_integration():
    """Dynamically import calendar integration classes"""
    try:
        # Import the main calendar integration module
        calendar_module = importlib.import_module('calendar_integration')
        
        # Get the classes
        CalendarIntegration = getattr(calendar_module, 'CalendarIntegration')
        CalendarProvider = getattr(calendar_module, 'CalendarProvider')
        
        return CalendarIntegration, CalendarProvider, True
    except (ImportError, AttributeError) as e:
        logger.info(f"Calendar integration not available: {str(e)}")
        return None, None, False

# Configure logging
logger = logging.getLogger(__name__)
level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, level))

# Add a stream handler to ensure logs are output
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class CalendarIntegrator:
    """
    Action group for calendar integration operations
    
    This class serves as an adapter between AWS Bedrock Agent and our core
    calendar integration service. It handles formatting requests and responses
    to be compatible with Bedrock Agent requirements.
    """
    
    def __init__(self, calendar_provider=None):
        """
        Initialize the CalendarIntegrator action group
        
        Args:
            calendar_provider: Optional calendar provider to use (GOOGLE or OUTLOOK)
        """
        self.table_name = os.environ.get('DYNAMODB_TABLE', 'appointment-system-appointments')
        
        # Import calendar integration dynamically
        CalendarIntegration, CalendarProvider, available = import_calendar_integration()
        
        # Initialize calendar integration if available
        if available:
            self.calendar_integration = CalendarIntegration()
            
            # Set the default provider based on the input or environment variable
            if calendar_provider:
                self.provider = CalendarProvider(calendar_provider.lower())
            else:
                provider_str = os.environ.get('DEFAULT_CALENDAR_PROVIDER', 'GOOGLE').lower()
                self.provider = CalendarProvider(provider_str)
        else:
            self.calendar_integration = None
            self.provider = None
            logger.info("Calendar integration not available. Using mock data for calendar operations.")
        
        # Log initialization
        logger.info(f"CalendarIntegrator action group initialized with provider: {self.provider.value if self.provider else 'None'}")
    
    def check_availability(self, date: str, start_time: str = "09:00", end_time: str = "17:00") -> Dict[str, Any]:
        """
        Check availability in the calendar for a specific date
        
        Args:
            date: The date to check (YYYY-MM-DD)
            start_time: Start of business hours (HH:MM)
            end_time: End of business hours (HH:MM)
            
        Returns:
            Dictionary with available time slots
        """
        logger.info(f"Checking calendar availability for {date} from {start_time} to {end_time}")
        
        try:
            if not self.calendar_integration:
                logger.info("Calendar integration not available. Returning mock data.")
                return {
                    "date": date,
                    "availableSlots": [
                        {"startTime": "09:00", "endTime": "10:00", "duration": 60},
                        {"startTime": "11:00", "endTime": "12:00", "duration": 60},
                        {"startTime": "14:00", "endTime": "15:00", "duration": 60}
                    ],
                    "success": True
                }
            
            # Get available slots from the calendar
            available_slots = self.calendar_integration.check_availability(
                provider=self.provider,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            
            # Format the result
            formatted_slots = []
            for slot in available_slots:
                slot_start = datetime.fromisoformat(slot["start"])
                slot_end = datetime.fromisoformat(slot["end"])
                
                formatted_slots.append({
                    "startTime": slot_start.strftime("%H:%M"),
                    "endTime": slot_end.strftime("%H:%M"),
                    "duration": int((slot_end - slot_start).total_seconds() / 60)
                })
            
            return {
                "date": date,
                "availableSlots": formatted_slots,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error checking calendar availability: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def sync_appointment(self, 
                        appointment_id: str, 
                        summary: str, 
                        date: str, 
                        start_time: str,
                        duration_minutes: int = 60,
                        attendee_email: str = None) -> Dict[str, Any]:
        """
        Sync an appointment with the calendar system
        
        Args:
            appointment_id: Unique ID for the appointment
            summary: Summary/title of the appointment
            date: Date of the appointment (YYYY-MM-DD)
            start_time: Start time of the appointment (HH:MM)
            duration_minutes: Duration in minutes
            attendee_email: Optional email of the attendee
            
        Returns:
            Dictionary with calendar sync result
        """
        logger.info(f"Syncing appointment {appointment_id} to calendar")
        
        try:
            if not self.calendar_integration:
                logger.info("Calendar integration not available. Returning mock data.")
                return {
                    "appointmentId": appointment_id,
                    "calendarEventId": "mock-calendar-event-" + appointment_id,
                    "calendarLink": "https://example.com/calendar/event/" + appointment_id,
                    "success": True
                }
            
            # Book the appointment in the calendar
            result = self.calendar_integration.book_appointment(
                provider=self.provider,
                appointment_details={
                    "date": date,
                    "time": start_time,
                    "duration_minutes": duration_minutes,
                    "purpose": summary,
                    "attendee_email": attendee_email
                }
            )
            
            if not result["success"]:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error syncing with calendar")
                }
            
            # Get the calendar event ID and link
            calendar_event_id = result.get("appointment_id")
            calendar_link = result.get("appointment_details", {}).get("htmlLink")
            
            return {
                "appointmentId": appointment_id,
                "calendarEventId": calendar_event_id,
                "calendarLink": calendar_link,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error syncing appointment with calendar: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_next_available_slot(self, date: str = None, min_duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Get the next available time slot in the calendar
        
        Args:
            date: Optional start date (defaults to today)
            min_duration_minutes: Minimum duration required in minutes
            
        Returns:
            Dictionary with next available slot
        """
        logger.info(f"Finding next available slot from {date or 'today'}")
        
        try:
            if not self.calendar_integration:
                logger.info("Calendar integration not available. Returning mock data.")
                next_day = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                return {
                    "date": next_day,
                    "startTime": "10:00",
                    "endTime": "11:00",
                    "duration": 60,
                    "success": True
                }
            
            # If no date provided, use today
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Get the next available slot
            next_slot = self.calendar_integration.get_next_available_slot(
                provider=self.provider,
                date=date
            )
            
            if not next_slot:
                return {
                    "success": False,
                    "error": "No available slots found"
                }
            
            # Format the result
            slot_start = datetime.fromisoformat(next_slot["start"])
            slot_end = datetime.fromisoformat(next_slot["end"])
            
            slot_date = slot_start.strftime("%Y-%m-%d")
            slot_start_time = slot_start.strftime("%H:%M")
            slot_end_time = slot_end.strftime("%H:%M")
            slot_duration = int((slot_end - slot_start).total_seconds() / 60)
            
            # Check if the slot meets the minimum duration requirement
            if slot_duration < min_duration_minutes:
                return {
                    "success": False,
                    "error": f"No available slots found with minimum duration of {min_duration_minutes} minutes"
                }
            
            return {
                "date": slot_date,
                "startTime": slot_start_time,
                "endTime": slot_end_time,
                "duration": slot_duration,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting next available slot: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Lambda handler for the action group
def lambda_handler(event, context):
    """
    Lambda handler for the CalendarIntegrator action group
    
    Note: This Lambda expects the following environment variables to be set:
    - GOOGLE_CALENDAR_TYPE=service_account
    - GOOGLE_CALENDAR_PROJECT_ID=pede-ai-core
    - GOOGLE_CALENDAR_PRIVATE_KEY_ID=e317959746d8b6f2b5328e147d9a87e97a9af31d
    - GOOGLE_CALENDAR_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIIE...==\n-----END PRIVATE KEY-----\n
    - GOOGLE_CALENDAR_CLIENT_EMAIL=aippointment-calendar@pede-ai-core.iam.gserviceaccount.com
    - GOOGLE_CALENDAR_CLIENT_ID=114676092833790726786
    - Additional Google Calendar environment variables as needed
    
    Args:
        event: The Lambda event
        context: The Lambda context
        
    Returns:
        Dictionary with the action response formatted for AWS Bedrock Agents
    """
    try:
        # First, let's log the raw event for debugging
        logger.info(f"Raw event type: {type(event)}, content: {event}")
        
        # *** Super defensive approach - always stringify and then parse the event ***
        try:
            # Convert the event to a string then back to a dictionary
            # This ensures consistent handling regardless of how Lambda provides it
            if isinstance(event, dict):
                event_str = json.dumps(event)
            else:
                event_str = str(event)
                
            # If event_str isn't already valid JSON (i.e., with quotes and formatting)
            # this will try to fix it by interpreting it as a Python literal
            if not event_str.startswith('{') and not event_str.startswith('['):
                import ast
                try:
                    # Try to convert Python literal to dict
                    event_dict = ast.literal_eval(event_str)
                    if isinstance(event_dict, dict):
                        event_str = json.dumps(event_dict)
                except (SyntaxError, ValueError):
                    # If that fails, wrap it as a simple string payload
                    event_str = json.dumps({"raw_content": event_str})
            
            # Now parse it back to a dictionary
            event = json.loads(event_str)
            logger.info(f"Processed event: {json.dumps(event)}")
            
        except (TypeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to process event format: {str(e)}")
            return format_bedrock_response({
                "error": f"Invalid event format: {str(e)}"
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
                "/calendar/availability": "checkAvailability",
                "/appointment/sync": "syncAppointment",
                "/calendar/next-slot": "getNextAvailableSlot"
            }
            
            action_name = api_path_to_action.get(api_path)
            if not action_name:
                return format_bedrock_response({"error": f"Unknown API path: {api_path}"}, action_group_name, api_path, http_method)
                
        except AttributeError as e:
            logger.error(f"Event structure error: {str(e)}")
            return format_bedrock_response({"error": "Invalid event format: event structure error"})
        
        # Process parameters from the parameters list format
        parameters = {}
        params_list = event.get('parameters', [])
        
        # Process parameters from list format (which is what Bedrock Agents uses)
        for param in params_list:
            if isinstance(param, dict) and 'name' in param and 'value' in param:
                parameters[param['name']] = param['value']
        
        logger.info(f"Processed parameters: {parameters}")
        
        # Initialize the action group
        calendar_provider = parameters.get('calendar_provider')
        action_group_instance = CalendarIntegrator(calendar_provider)
        
        # Route to the appropriate method
        if action_name == 'checkAvailability':
            date = parameters.get('date')
            if not date:
                return format_bedrock_response({
                    "error": "Missing required parameter: date"
                }, action_group_name, api_path, http_method)
                
            # Check for camelCase and snake_case parameter names
            start_time = parameters.get('startTime') or parameters.get('start_time', "09:00")
            end_time = parameters.get('endTime') or parameters.get('end_time', "17:00")
            
            result = action_group_instance.check_availability(date, start_time, end_time)
            return format_bedrock_response(result, action_group_name, api_path, http_method)
        
        elif action_name == 'syncAppointment':
            # Check for camelCase and snake_case parameter names
            appointment_id = parameters.get('appointmentId') or parameters.get('appointment_id')
            if not appointment_id:
                return format_bedrock_response({
                    "error": "Missing required parameter: appointmentId"
                }, action_group_name, api_path, http_method)
                
            summary = parameters.get('summary')
            if not summary:
                return format_bedrock_response({
                    "error": "Missing required parameter: summary"
                }, action_group_name, api_path, http_method)
                
            date = parameters.get('date')
            if not date:
                return format_bedrock_response({
                    "error": "Missing required parameter: date"
                }, action_group_name, api_path, http_method)
                
            start_time = parameters.get('startTime') or parameters.get('start_time')
            if not start_time:
                return format_bedrock_response({
                    "error": "Missing required parameter: startTime"
                }, action_group_name, api_path, http_method)
                
            # These parameters are optional or have defaults
            try:
                duration_minutes = int(parameters.get('durationMinutes') or parameters.get('duration_minutes', 60))
            except (ValueError, TypeError):
                duration_minutes = 60
                
            attendee_email = parameters.get('attendeeEmail') or parameters.get('attendee_email')
            
            result = action_group_instance.sync_appointment(
                appointment_id, summary, date, start_time, duration_minutes, attendee_email
            )
            return format_bedrock_response(result, action_group_name, api_path, http_method)
            
        elif action_name == 'getNextAvailableSlot':
            # Check for camelCase and snake_case parameter names
            date = parameters.get('date')
            
            # Default to 60 minutes, handle conversion errors
            try:
                min_duration_minutes = int(parameters.get('minDurationMinutes') or parameters.get('min_duration_minutes', 60))
            except (ValueError, TypeError):
                min_duration_minutes = 60
            
            result = action_group_instance.get_next_available_slot(date, min_duration_minutes)
            return format_bedrock_response(result, action_group_name, api_path, http_method)
        
        else:
            return format_bedrock_response({
                "error": f"Unknown action: {action_name}"
            }, action_group_name, api_path, http_method)
            
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}", exc_info=True)
        # Even in error case, we need to try to include the original action_group, api_path and http_method if available
        action_group_name = event.get('actionGroup', 'CalendarIntegrator') if isinstance(event, dict) else 'CalendarIntegrator'
        api_path = event.get('apiPath', '/calendar/availability') if isinstance(event, dict) else '/calendar/availability'
        http_method = event.get('httpMethod', 'GET') if isinstance(event, dict) else 'GET'
        
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
            "actionGroup": action_group or "CalendarIntegrator",
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
