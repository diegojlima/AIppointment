# functions/appointment-booking/src/calendar_services/google_calendar.py
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys

# Configure logger first
logger = logging.getLogger(__name__)

# Import the calendar service interface
from calendar_services.calendar_service_interface import CalendarServiceInterface

# Fix for Lambda: Try different import paths for utils
try:
    # Try the local utils module first
    from calendar_services.utils import get_google_credentials
    logger.info("Using calendar_services.utils.get_google_credentials")
except ImportError:
    try:
        # Try direct import next
        from utils.google_credentials import get_google_credentials
        logger.info("Using utils.google_credentials.get_google_credentials")
    except ImportError:
        try:
            # Try to import based on current file location
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from utils.google_credentials import get_google_credentials
            logger.info("Using path-adjusted utils.google_credentials.get_google_credentials")
        except ImportError:
            # If still failing, define a fallback function for debugging
            logger.error("Failed to import utils.google_credentials. Using fallback function.")
            def get_google_credentials():
                """Fallback implementation of get_google_credentials."""
                logger.error("Using fallback get_google_credentials function. This will not work properly!")
                return {}

# Import Google libraries only if available - makes testing easier
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBRARIES_AVAILABLE = True
except ImportError:
    logger.warning("Google API libraries not available. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    GOOGLE_LIBRARIES_AVAILABLE = False

class GoogleCalendarService(CalendarServiceInterface):
    """
    Service for interacting with the Google Calendar API.
    
    This service provides methods for:
    - Checking availability
    - Creating appointments
    - Managing calendar credentials
    
    It uses a service account for authentication, with credentials
    loaded from environment variables.
    """
    
    def __init__(self, credentials_manager=None):
        """
        Initialize the Google Calendar service.
        
        Args:
            credentials_manager: Optional custom credentials manager (not used for env var approach)
        """
        # Store default calendar ID from environment variable or use 'primary'
        self.calendar_id = os.environ.get('GOOGLE_CALENDAR_ID', 'primary')
        # We'll initialize the service when needed, not on instantiation
        self.service = None
        
        logger.info("Google Calendar service initialized")
    
    def _get_credentials(self):
        """
        Get Google API credentials from environment variables.
        
        Returns:
            Google Credentials object if successful, None otherwise
        """
        if not GOOGLE_LIBRARIES_AVAILABLE:
            logger.error("Google API libraries not available.")
            return None
            
        try:
            # Get credentials dictionary from environment variables
            creds_dict = get_google_credentials()
            
            # Create credentials object
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            return credentials
        except Exception as e:
            logger.error(f"Error creating Google credentials: {str(e)}")
            return None
    
    def _get_service(self):
        """
        Get an authenticated Google Calendar API service.
        
        Returns:
            An authenticated service object if successful, None otherwise
        """
        # If we already have a service, return it
        if self.service:
            return self.service
            
        if not GOOGLE_LIBRARIES_AVAILABLE:
            logger.error("Google API libraries not available.")
            return None
            
        try:
            # Get credentials
            credentials = self._get_credentials()
            if not credentials:
                logger.error("Failed to get Google credentials.")
                return None
                
            # Build the service
            self.service = build('calendar', 'v3', credentials=credentials)
            return self.service
            
        except Exception as e:
            logger.error(f"Error creating Google Calendar service: {str(e)}")
            return None
    
    def get_available_slots(self, start_datetime, end_datetime, calendar_id=None):
        """
        Get available time slots in the specified time range.
        
        Args:
            start_datetime: Start of the time range (ISO format)
            end_datetime: End of the time range (ISO format)
            calendar_id: ID of the calendar to check (defaults to environment variable or 'primary')
            
        Returns:
            List of available time slots
        """
        logger.info(f"Getting available slots from {start_datetime} to {end_datetime}")
        
        # Use provided calendar_id or fall back to instance default
        calendar_id = calendar_id or self.calendar_id
        
        # In a real implementation, we'd use the following code:
        try:
            service = self._get_service()
            if not service:
                logger.error("Could not get Google Calendar service")
                return []
                
            # Convert string times to datetime objects with consistent timezone information
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            
            # Get busy periods from the calendar API
            body = {
                "timeMin": start_dt.isoformat(),
                "timeMax": end_dt.isoformat(),
                "items": [{"id": calendar_id}]
            }
            
            # Uncomment this for real implementation
            # freebusy_response = service.freebusy().query(body=body).execute()
            # busy_periods = freebusy_response.get('calendars', {}).get(calendar_id, {}).get('busy', [])
            
            # For testing, we'll use mock data
            # TODO: Replace with real API call
            busy_periods = [
                {"start": "2023-09-15T10:00:00Z", "end": "2023-09-15T11:00:00Z"},
                {"start": "2023-09-15T13:00:00Z", "end": "2023-09-15T14:00:00Z"},
            ]
            
            # Find available slots by removing busy periods
            available_slots = []
            # Ensure current_start is timezone-aware
            current_start = start_dt
            
            for busy in busy_periods:
                # Ensure we have timezone-aware datetimes with consistent timezone info
                busy_start = datetime.fromisoformat(busy["start"].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy["end"].replace('Z', '+00:00'))
                
                # If there's time between current_start and busy_start, that's an available slot
                # Ensure we're comparing datetime objects with consistent timezone information
                if current_start < busy_start:
                    available_slots.append({
                        "start": current_start.isoformat(),
                        "end": busy_start.isoformat()
                    })
                
                # Move current_start to after the busy period
                # When using max() with datetimes, they must have the same tzinfo
                current_start = max(current_start, busy_end)
            
            # Add any remaining time after the last busy period
            # Again, ensure consistent timezone handling in comparison
            if current_start < end_dt:
                available_slots.append({
                    "start": current_start.isoformat(),
                    "end": end_dt.isoformat()
                })
                
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots from Google Calendar: {str(e)}")
            return []
    
    def create_appointment(self, appointment_data, calendar_id=None) -> Dict[str, Any]:
        """
        Create an appointment in the Google Calendar.
        
        Args:
            appointment_data: Dictionary with appointment details
            calendar_id: ID of the calendar to use (defaults to environment variable or 'primary')
            
        Returns:
            Dictionary with the created event details
        """
        logger.info(f"Creating appointment in Google Calendar: {appointment_data}")
        
        # Use provided calendar_id or fall back to instance default
        calendar_id = calendar_id or self.calendar_id
        
        try:
            service = self._get_service()
            if not service:
                raise ValueError("Could not get Google Calendar service")
            
            # Prepare the event data
            event = {
                'summary': appointment_data.get('summary', 'New Appointment'),
                'start': appointment_data.get('start', {}),
                'end': appointment_data.get('end', {}),
            }
            
            # Add optional fields if present
            if 'attendees' in appointment_data:
                event['attendees'] = appointment_data['attendees']
                
            if 'description' in appointment_data:
                event['description'] = appointment_data['description']
                
            if 'location' in appointment_data:
                event['location'] = appointment_data['location']
                
            # Uncomment this for real implementation
            # created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
            # return created_event
            
            # For testing, we'll return a mock created event
            # TODO: Replace with real API call
            return {
                "id": "event_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                "summary": event.get("summary"),
                "start": event.get("start"),
                "end": event.get("end"),
                "htmlLink": "https://calendar.google.com/calendar/event?id=mockevent"
            }
            
        except Exception as e:
            logger.error(f"Error creating appointment in Google Calendar: {str(e)}")
            raise
    
    def update_appointment(self, appointment_id: str, appointment_data: Dict[str, Any], calendar_id=None) -> Dict[str, Any]:
        """
        Update an existing appointment in the Google Calendar.
        
        Args:
            appointment_id: ID of the appointment to update
            appointment_data: Dictionary with updated appointment details
            calendar_id: ID of the calendar to use (defaults to environment variable or 'primary')
            
        Returns:
            Dictionary with the updated event details
        """
        logger.info(f"Updating appointment {appointment_id} in Google Calendar")
        
        # Use provided calendar_id or fall back to instance default
        calendar_id = calendar_id or self.calendar_id
        
        try:
            service = self._get_service()
            if not service:
                raise ValueError("Could not get Google Calendar service")
            
            # First, get the existing event
            # Uncomment this for real implementation
            # existing_event = service.events().get(calendarId=calendar_id, eventId=appointment_id).execute()
            
            # For testing, we'll use a mock existing event
            # TODO: Replace with real API call
            existing_event = {
                "id": appointment_id,
                "summary": "Existing Appointment",
                "start": {"dateTime": "2023-09-15T14:00:00"},
                "end": {"dateTime": "2023-09-15T15:00:00"},
            }
            
            # Update the event with new data
            for key, value in appointment_data.items():
                existing_event[key] = value
            
            # Uncomment this for real implementation
            # updated_event = service.events().update(
            #     calendarId=calendar_id,
            #     eventId=appointment_id,
            #     body=existing_event
            # ).execute()
            # return updated_event
            
            # For testing, we'll return the mock updated event
            return existing_event
            
        except Exception as e:
            logger.error(f"Error updating appointment in Google Calendar: {str(e)}")
            raise
    
    def delete_appointment(self, appointment_id: str, calendar_id=None) -> bool:
        """
        Delete an appointment from the Google Calendar.
        
        Args:
            appointment_id: ID of the appointment to delete
            calendar_id: ID of the calendar to use (defaults to environment variable or 'primary')
            
        Returns:
            True if the appointment was deleted successfully, False otherwise
        """
        logger.info(f"Deleting appointment {appointment_id} from Google Calendar")
        
        # Use provided calendar_id or fall back to instance default
        calendar_id = calendar_id or self.calendar_id
        
        try:
            service = self._get_service()
            if not service:
                raise ValueError("Could not get Google Calendar service")
            
            # Uncomment this for real implementation
            # service.events().delete(calendarId=calendar_id, eventId=appointment_id).execute()
            
            # For testing, we'll just return success
            # TODO: Replace with real API call
            return True
            
        except Exception as e:
            logger.error(f"Error deleting appointment from Google Calendar: {str(e)}")
            return False
    
    def get_appointment(self, appointment_id: str, calendar_id=None) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific appointment from the Google Calendar.
        
        Args:
            appointment_id: ID of the appointment to retrieve
            calendar_id: ID of the calendar to use (defaults to environment variable or 'primary')
            
        Returns:
            Dictionary with the appointment details, or None if not found
        """
        logger.info(f"Getting appointment {appointment_id} from Google Calendar")
        
        # Use provided calendar_id or fall back to instance default
        calendar_id = calendar_id or self.calendar_id
        
        try:
            service = self._get_service()
            if not service:
                logger.error("Could not get Google Calendar service")
                return None
                
            # Uncomment this for real implementation
            # event = service.events().get(calendarId=calendar_id, eventId=appointment_id).execute()
            # return event
            
            # For testing, we'll return a mock event
            # TODO: Replace with real API call
            return {
                "id": appointment_id,
                "summary": "Mock Appointment",
                "start": {"dateTime": "2023-09-15T14:00:00"},
                "end": {"dateTime": "2023-09-15T15:00:00"},
                "htmlLink": "https://calendar.google.com/calendar/event?id=" + appointment_id
            }
            
        except Exception as e:
            logger.error(f"Error getting appointment from Google Calendar: {str(e)}")
            return None
