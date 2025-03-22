"""
Google Calendar V2 Service Module - Simplified MVP

Simple MVP implementation of Google Calendar service 
for checking availability using service account authentication.
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any, List
import json

# Configure logger
logger = logging.getLogger(__name__)
# Set to DEBUG level to get all messages
logger.setLevel(logging.INFO)

# Import the calendar service interface
from calendar_services.calendar_service_interface import CalendarServiceInterface

# Import Google libraries
# First check to see if we have the libraries (with try/except)
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBRARIES_AVAILABLE = True
    logger.info("Google Calendar libraries loaded successfully")
except ImportError as e:
    logger.error(f"Failed to import Google Calendar libraries: {str(e)}")
    GOOGLE_LIBRARIES_AVAILABLE = False

class GoogleCalendarServiceV2(CalendarServiceInterface):
    """
    Minimal implementation of Google Calendar service using service account authentication.
    Focused on the core functionality needed for the MVP.
    """
    
    def __init__(self):
        """
        Initialize the Google Calendar service.
        """
        logger.info("Initializing GoogleCalendarServiceV2")
        
        # Get the user calendar ID if specified (for creating events in a user's personal calendar)
        self.user_calendar_id = os.environ.get('PRIMARY_USER_CALENDAR')
        
        # Store default calendar ID from environment variable or use 'primary'
        self.calendar_id = os.environ.get('GOOGLE_CALENDAR_ID', 'primary')
        logger.info(f"Default Calendar ID: {self.calendar_id}")
        
        if self.user_calendar_id:
            logger.info(f"User Calendar ID configured: {self.user_calendar_id}")
        
        # Will store the service instance once initialized
        self.service = None
                
        # Log environment variables (redacted)
        self._log_environment_vars()
        
        logger.info("Google Calendar V2 service initialized")
    
    def _log_environment_vars(self):
        """Log environment variables (with sensitive information redacted)"""
        env_vars = {
            "GOOGLE_CALENDAR_TYPE": os.environ.get("GOOGLE_CALENDAR_TYPE"),
            "GOOGLE_CALENDAR_PROJECT_ID": os.environ.get("GOOGLE_CALENDAR_PROJECT_ID"),
            "GOOGLE_CALENDAR_PRIVATE_KEY_ID": os.environ.get("GOOGLE_CALENDAR_PRIVATE_KEY_ID", "")[:4] + "..." if os.environ.get("GOOGLE_CALENDAR_PRIVATE_KEY_ID") else None,
            "GOOGLE_CALENDAR_PRIVATE_KEY": "REDACTED" if os.environ.get("GOOGLE_CALENDAR_PRIVATE_KEY") else None,
            "GOOGLE_CALENDAR_CLIENT_EMAIL": os.environ.get("GOOGLE_CALENDAR_CLIENT_EMAIL"),
            "GOOGLE_CALENDAR_CLIENT_ID": os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", "")[:5] + "..." if os.environ.get("GOOGLE_CALENDAR_CLIENT_ID") else None,
        }
        logger.info(f"Environment variables: {json.dumps(env_vars)}")
    
    def _get_credentials(self):
        """
        Get Google API credentials from environment variables.
        
        Returns:
            Google Credentials object
        """
        logger.info("Getting Google API credentials")
        
        if not GOOGLE_LIBRARIES_AVAILABLE:
            logger.error("Google API libraries not available")
            return None
            
        try:
            # Check for required environment variables
            required_vars = [
                "GOOGLE_CALENDAR_TYPE", 
                "GOOGLE_CALENDAR_PROJECT_ID",
                "GOOGLE_CALENDAR_PRIVATE_KEY_ID", 
                "GOOGLE_CALENDAR_PRIVATE_KEY",
                "GOOGLE_CALENDAR_CLIENT_EMAIL", 
                "GOOGLE_CALENDAR_CLIENT_ID"
            ]
            
            missing = [var for var in required_vars if not os.environ.get(var)]
            if missing:
                logger.error(f"Missing required environment variables: {', '.join(missing)}")
                return None
                
            # Reconstruct service account JSON from environment variables
            creds_dict = {
                "type": os.environ.get("GOOGLE_CALENDAR_TYPE"),
                "project_id": os.environ.get("GOOGLE_CALENDAR_PROJECT_ID"),
                "private_key_id": os.environ.get("GOOGLE_CALENDAR_PRIVATE_KEY_ID"),
                "private_key": os.environ.get("GOOGLE_CALENDAR_PRIVATE_KEY").replace("\\n", "\n"),
                "client_email": os.environ.get("GOOGLE_CALENDAR_CLIENT_EMAIL"),
                "client_id": os.environ.get("GOOGLE_CALENDAR_CLIENT_ID"),
                "auth_uri": os.environ.get("GOOGLE_CALENDAR_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.environ.get("GOOGLE_CALENDAR_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.environ.get(
                    "GOOGLE_CALENDAR_AUTH_PROVIDER_X509_CERT_URL", 
                    "https://www.googleapis.com/oauth2/v1/certs"
                ),
                "client_x509_cert_url": os.environ.get("GOOGLE_CALENDAR_CLIENT_X509_CERT_URL"),
                "universe_domain": os.environ.get("GOOGLE_CALENDAR_UNIVERSE_DOMAIN", "googleapis.com"),
            }
            
            logger.info("Creating credentials from service account info")
            
            # Create credentials object
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            # Check if domain-wide delegation is enabled (for accessing users' calendars)
            delegation_email = os.environ.get("GOOGLE_CALENDAR_DELEGATE_EMAIL")
            if delegation_email:
                logger.info(f"Using domain-wide delegation with {delegation_email}")
                credentials = credentials.with_subject(delegation_email)
            
            logger.info("Credentials created successfully")
            return credentials
            
        except Exception as e:
            logger.error(f"Error creating credentials: {str(e)}", exc_info=True)
            return None
    
    def _get_service(self):
        """
        Get an authenticated Google Calendar API service.
        
        Returns:
            An authenticated service object
        """
        logger.info("Getting Google Calendar service")
        
        # Return cached service if available
        if self.service:
            logger.info("Using cached service")
            return self.service
            
        if not GOOGLE_LIBRARIES_AVAILABLE:
            logger.error("Google API libraries not available")
            return None
            
        try:
            # Get credentials
            credentials = self._get_credentials()
            if not credentials:
                logger.error("Failed to get credentials")
                return None
                
            # Build the service
            logger.info("Building service")
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.info("Service built successfully")
            return self.service
            
        except Exception as e:
            logger.error(f"Error building service: {str(e)}", exc_info=True)
            return None
    
    def get_available_slots(self, start_datetime, end_datetime, calendar_id=None):
        """
        Get available time slots in the specified time range.
        
        Args:
            start_datetime: Start of the time range (ISO format)
            end_datetime: End of the time range (ISO format)
            calendar_id: ID of the calendar to check (defaults to instance default)
            
        Returns:
            List of available time slots
        """
        logger.info(f"Getting available slots from {start_datetime} to {end_datetime}")
        
        # Prioritize using user's personal calendar if configured
        # Otherwise use provided calendar_id or fall back to instance default
        if self.user_calendar_id:
            calendar_id = self.user_calendar_id
            logger.info(f"Using user's personal calendar: {calendar_id}")
        else:
            calendar_id = calendar_id or self.calendar_id
            logger.info(f"Using calendar ID: {calendar_id}")
        
        try:
            service = self._get_service()
            if not service:
                logger.error("Could not get Google Calendar service")
                return []
                
            # Format datetimes for Google Calendar API
            if 'Z' not in start_datetime and '+' not in start_datetime:
                start_datetime = f"{start_datetime}Z"
            if 'Z' not in end_datetime and '+' not in end_datetime:
                end_datetime = f"{end_datetime}Z"
            
            # Prepare the freebusy request
            body = {
                "timeMin": start_datetime,
                "timeMax": end_datetime,
                "timeZone": "UTC",
                "items": [{"id": calendar_id}]
            }
            
            logger.info(f"Freebusy request: {json.dumps(body)}")
            
            # Make the API call
            freebusy_response = service.freebusy().query(body=body).execute()
            logger.info(f"Freebusy response: {json.dumps(freebusy_response)}")
            
            # Extract busy periods
            busy_periods = freebusy_response.get('calendars', {}).get(calendar_id, {}).get('busy', [])
            
            # Convert start_datetime and end_datetime to datetime objects
            dt_start = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            dt_end = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            
            # Convert busy periods to datetime objects
            busy_periods_dt = []
            for period in busy_periods:
                period_start = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
                period_end = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
                busy_periods_dt.append((period_start, period_end))
            
            # Sort busy periods by start time
            busy_periods_dt.sort(key=lambda x: x[0])
            
            # Find available slots between busy periods
            available_slots = []
            current_start = dt_start
            
            # Add slots between busy periods
            for busy_start, busy_end in busy_periods_dt:
                # If there's time between current_start and busy_start, add it as an available slot
                if current_start < busy_start:
                    available_slots.append({
                        "start": current_start.isoformat(),
                        "end": busy_start.isoformat()
                    })
                
                # Update current_start to after this busy period
                current_start = max(current_start, busy_end)
            
            # Add any remaining time after the last busy period
            if current_start < dt_end:
                available_slots.append({
                    "start": current_start.isoformat(),
                    "end": dt_end.isoformat()
                })
            
            # If there are no busy periods, the entire requested time is available
            if not busy_periods_dt and dt_start < dt_end:
                available_slots.append({
                    "start": dt_start.isoformat(),
                    "end": dt_end.isoformat()
                })
            
            # Filter out slots shorter than 30 minutes (1800 seconds)
            filtered_slots = []
            min_duration = 1800  # 30 minutes in seconds
            
            for slot in available_slots:
                slot_start = datetime.fromisoformat(slot["start"])
                slot_end = datetime.fromisoformat(slot["end"])
                duration = (slot_end - slot_start).total_seconds()
                
                if duration >= min_duration:
                    filtered_slots.append(slot)
            
            logger.info(f"Found {len(filtered_slots)} available slots after filtering")
            return filtered_slots
            
        except Exception as e:
            logger.error(f"Error in get_available_slots: {str(e)}", exc_info=True)
            return []
    
    def create_appointment(self, appointment_data, calendar_id=None):
        """
        Create an appointment in the Google Calendar.
        
        Args:
            appointment_data: Dictionary with appointment details
            calendar_id: ID of the calendar to use
            
        Returns:
            Dictionary with the created event details
        """
        logger.info(f"Creating appointment: {json.dumps(appointment_data)}")
        
        # Prioritize using user's personal calendar if configured
        # Otherwise use provided calendar_id or fall back to instance default
        if self.user_calendar_id:
            calendar_id = self.user_calendar_id
            logger.info(f"Using user's personal calendar: {calendar_id}")
        else:
            calendar_id = calendar_id or self.calendar_id
            logger.info(f"Using calendar ID: {calendar_id}")
        
        try:
            service = self._get_service()
            if not service:
                logger.error("Could not get Google Calendar service")
                return {"success": False, "error": "Could not get Google Calendar service"}
            
            # Ensure appointment_data has the required fields
            if 'summary' not in appointment_data:
                appointment_data['summary'] = 'Appointment'
            
            # Convert start and end to Google Calendar API format if needed
            if isinstance(appointment_data.get('start', {}), str):
                start_time = appointment_data['start']
                appointment_data['start'] = {"dateTime": start_time, "timeZone": "UTC"}
                
            if isinstance(appointment_data.get('end', {}), str):
                end_time = appointment_data['end']
                appointment_data['end'] = {"dateTime": end_time, "timeZone": "UTC"}
            
            # Add optional fields
            if 'description' not in appointment_data:
                appointment_data['description'] = 'Created by AIppointment system'
            
            # Handle attendees for service accounts
            is_service_account = os.environ.get('GOOGLE_CALENDAR_TYPE') == 'service_account'
            has_delegation = bool(os.environ.get('GOOGLE_CALENDAR_DELEGATE_EMAIL'))
            has_attendees = 'attendees' in appointment_data and appointment_data['attendees']
            
            if has_attendees and is_service_account and not has_delegation:
                # Extract attendees before removing them
                attendees = appointment_data.pop('attendees', [])
                attendee_emails = [a.get('email') for a in attendees if 'email' in a]
                
                # Add to description instead
                appointment_data['description'] = f"{appointment_data.get('description', '')}\n\nAttendees: {', '.join(attendee_emails)}"
                logger.info(f"Removed attendees for service account without DWA and added to description: {attendee_emails}")
                
                # Don't send notifications since we removed attendees
                appointment_data['sendUpdates'] = 'none'
            else:
                # Send notification to attendees by default
                appointment_data['sendUpdates'] = appointment_data.get('sendUpdates', 'all')
            
            # Create the event
            event = service.events().insert(
                calendarId=calendar_id, 
                body=appointment_data
            ).execute()
            
            logger.info(f"Appointment created with ID: {event.get('id')}")
            return {
                "success": True,
                "id": event.get('id'),
                "htmlLink": event.get('htmlLink'),
                "created": event.get('created'),
                "appointment_details": event
            }
            
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def update_appointment(self, appointment_id, appointment_data, calendar_id=None):
        """
        Update an existing appointment in the Google Calendar.
        
        Args:
            appointment_id: ID of the appointment to update
            appointment_data: Dictionary with updated appointment details
            calendar_id: ID of the calendar to use
            
        Returns:
            Dictionary with the updated event details
        """
        logger.info(f"Updating appointment {appointment_id}")
        
        # Prioritize using user's personal calendar if configured
        # Otherwise use provided calendar_id or fall back to instance default
        if self.user_calendar_id:
            calendar_id = self.user_calendar_id
            logger.info(f"Using user's personal calendar: {calendar_id}")
        else:
            calendar_id = calendar_id or self.calendar_id
            logger.info(f"Using calendar ID: {calendar_id}")
        
        try:
            service = self._get_service()
            if not service:
                logger.error("Could not get Google Calendar service")
                return {"success": False, "error": "Could not get Google Calendar service"}
            
            # First get the existing event to merge with updates
            existing_event = service.events().get(
                calendarId=calendar_id,
                eventId=appointment_id
            ).execute()
            
            # Update the event with new data (merge dictionaries)
            for key, value in appointment_data.items():
                existing_event[key] = value
            
            # Update the event
            updated_event = service.events().update(
                calendarId=calendar_id, 
                eventId=appointment_id,
                body=existing_event
            ).execute()
            
            logger.info(f"Appointment {appointment_id} updated successfully")
            return {
                "success": True,
                "id": updated_event.get('id'),
                "htmlLink": updated_event.get('htmlLink'),
                "updated": updated_event.get('updated'),
                "appointment_details": updated_event
            }
            
        except Exception as e:
            logger.error(f"Error updating appointment: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def delete_appointment(self, appointment_id, calendar_id=None):
        """
        Delete an appointment from the Google Calendar.
        
        Args:
            appointment_id: ID of the appointment to delete
            calendar_id: ID of the calendar to use
            
        Returns:
            True if the appointment was deleted successfully, False otherwise
        """
        logger.info(f"Deleting appointment {appointment_id}")
        
        # Prioritize using user's personal calendar if configured
        # Otherwise use provided calendar_id or fall back to instance default
        if self.user_calendar_id:
            calendar_id = self.user_calendar_id
            logger.info(f"Using user's personal calendar: {calendar_id}")
        else:
            calendar_id = calendar_id or self.calendar_id
            logger.info(f"Using calendar ID: {calendar_id}")
        
        try:
            service = self._get_service()
            if not service:
                logger.error("Could not get Google Calendar service")
                return False
            
            # Delete the event
            service.events().delete(
                calendarId=calendar_id, 
                eventId=appointment_id,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Appointment {appointment_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting appointment: {str(e)}", exc_info=True)
            return False
    
    def get_appointment(self, appointment_id, calendar_id=None):
        """
        Get details of a specific appointment from the Google Calendar.
        
        Args:
            appointment_id: ID of the appointment to retrieve
            calendar_id: ID of the calendar to use
            
        Returns:
            Dictionary with the appointment details, or None if not found
        """
        logger.info(f"Getting appointment {appointment_id}")
        
        # Prioritize using user's personal calendar if configured
        # Otherwise use provided calendar_id or fall back to instance default
        if self.user_calendar_id:
            calendar_id = self.user_calendar_id
            logger.info(f"Using user's personal calendar: {calendar_id}")
        else:
            calendar_id = calendar_id or self.calendar_id
            logger.info(f"Using calendar ID: {calendar_id}")
        
        try:
            service = self._get_service()
            if not service:
                logger.error("Could not get Google Calendar service")
                return None
            
            # Get the event
            event = service.events().get(
                calendarId=calendar_id, 
                eventId=appointment_id
            ).execute()
            
            logger.info(f"Successfully retrieved appointment {appointment_id}")
            return event
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.info(f"Appointment {appointment_id} not found")
                return None
            else:
                logger.error(f"Error getting appointment: {str(e)}", exc_info=True)
                return None
                
        except Exception as e:
            logger.error(f"Error getting appointment: {str(e)}", exc_info=True)
            return None
