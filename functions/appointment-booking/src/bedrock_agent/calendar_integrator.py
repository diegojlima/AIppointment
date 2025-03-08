"""
CalendarIntegrator action group for AWS Bedrock Agent

This action group handles:
- Calendar API integration with Google Calendar or Microsoft Office 365
- Managing time slot availability
- Synchronizing appointment data
"""
import json
import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os

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
        logger.warning(f"Calendar integration not available: {str(e)}")
        return None, None, False

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CalendarIntegrator:
    """
    Action group for calendar integration operations
    """
    
    def __init__(self, calendar_provider=None):
        """
        Initialize the CalendarIntegrator action group
        
        Args:
            calendar_provider: Optional calendar provider to use (GOOGLE or OUTLOOK)
        """
        self.secrets_manager = boto3.client('secretsmanager')
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
            logger.warning("Calendar integration not available. Using mock data for calendar operations.")
        
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
                logger.warning("Calendar integration not available. Returning mock data.")
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
                logger.warning("Calendar integration not available. Returning mock data.")
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
                logger.warning("Calendar integration not available. Returning mock data.")
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
    
    Args:
        event: The Lambda event
        context: The Lambda context
        
    Returns:
        Dictionary with the action response
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Extract the action name and parameters
    action_name = event.get('actionGroup', {}).get('actionName')
    parameters = event.get('parameters', {})
    
    # Initialize the action group
    calendar_provider = parameters.get('calendar_provider')
    action_group = CalendarIntegrator(calendar_provider)
    
    # Route to the appropriate method
    if action_name == 'check_availability':
        date = parameters.get('date')
        start_time = parameters.get('start_time', "09:00")
        end_time = parameters.get('end_time', "17:00")
        
        return action_group.check_availability(date, start_time, end_time)
    
    elif action_name == 'sync_appointment':
        appointment_id = parameters.get('appointment_id')
        summary = parameters.get('summary')
        date = parameters.get('date')
        start_time = parameters.get('start_time')
        duration_minutes = int(parameters.get('duration_minutes', 60))
        attendee_email = parameters.get('attendee_email')
        
        return action_group.sync_appointment(
            appointment_id, summary, date, start_time, duration_minutes, attendee_email
        )
    
    elif action_name == 'get_next_available_slot':
        date = parameters.get('date')
        min_duration_minutes = int(parameters.get('min_duration_minutes', 60))
        
        return action_group.get_next_available_slot(date, min_duration_minutes)
    
    else:
        return {
            "success": False,
            "error": f"Unknown action: {action_name}"
        }
