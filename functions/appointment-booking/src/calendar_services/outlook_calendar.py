# functions/appointment-booking/src/calendar_services/outlook_calendar.py
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import boto3

logger = logging.getLogger(__name__)

class OutlookCalendarService:
    """
    Service for interacting with the Microsoft Graph API for Outlook Calendar.
    
    This service provides methods for:
    - Checking availability
    - Creating appointments
    - Managing calendar credentials
    
    It uses app registration and delegated permissions for authentication,
    with credentials stored securely in AWS Parameter Store.
    """
    
    def __init__(self, credentials_manager=None):
        """
        Initialize the Outlook Calendar service.
        
        Args:
            credentials_manager: Optional custom credentials manager
        """
        self.credentials_manager = credentials_manager
        self.ssm_client = boto3.client('ssm')
        self.credentials_path = os.environ.get('OUTLOOK_CREDENTIALS_PATH', '/aippointment/outlook/credentials')
        
        logger.info("Outlook Calendar service initialized")
    
    def _get_credentials(self):
        """
        Get Microsoft Graph API credentials from Parameter Store.
        
        Returns:
            Dictionary with credentials data
        """
        try:
            # In a real implementation, we would retrieve the credentials from SSM
            # For testing, we'll return a mock credentials object
            return {
                "client_id": "outlook-client-id",
                "tenant_id": "outlook-tenant-id",
                "client_secret": "outlook-client-secret"
            }
        except Exception as e:
            logger.error(f"Error retrieving Outlook credentials: {str(e)}")
            return None
    
    def _get_service(self):
        """
        Get an authenticated Microsoft Graph API service.
        
        Returns:
            An authenticated service object (mocked for now)
        """
        # In a real implementation, we would create a Microsoft Graph API client
        # For testing, we'll return a mock service
        return {"name": "outlook-calendar-service", "authenticated": True}
    
    def get_available_slots(self, start_datetime, end_datetime, calendar_id=None):
        """
        Get available time slots in the specified time range.
        
        Args:
            start_datetime: Start of the time range (ISO format)
            end_datetime: End of the time range (ISO format)
            calendar_id: ID of the calendar to check
            
        Returns:
            List of available time slots
        """
        logger.info(f"Getting available slots from {start_datetime} to {end_datetime}")
        
        try:
            # In a real implementation, we would:
            # 1. Get the Microsoft Graph API service
            # service = self._get_service()
            
            # 2. Fetch the calendar view for the time range
            # events = service.me.calendar.calendarView.get(
            #     startDateTime=start_datetime,
            #     endDateTime=end_datetime
            # ).execute()
            
            # 3. Calculate available slots by subtracting busy times from the time range
            
            # For testing, we'll return mock available slots
            # These would normally be calculated based on the API response
            return [
                {"start": "2023-09-15T10:00:00", "end": "2023-09-15T11:00:00"},
                {"start": "2023-09-15T13:00:00", "end": "2023-09-15T14:00:00"},
                {"start": "2023-09-15T15:00:00", "end": "2023-09-15T16:00:00"},
            ]
            
        except Exception as e:
            logger.error(f"Error getting available slots from Outlook Calendar: {str(e)}")
            return []
    
    def create_appointment(self, appointment_data, calendar_id=None):
        """
        Create an appointment in the Outlook Calendar.
        
        Args:
            appointment_data: Dictionary with appointment details
            calendar_id: ID of the calendar to use
            
        Returns:
            Dictionary with the created event details
        """
        logger.info(f"Creating appointment in Outlook Calendar: {appointment_data}")
        
        try:
            # In a real implementation, we would:
            # 1. Get the Microsoft Graph API service
            # service = self._get_service()
            
            # 2. Format the event data
            # event = {
            #     'subject': appointment_data.get('summary'),
            #     'start': {
            #         'dateTime': appointment_data.get('start').get('dateTime'),
            #         'timeZone': 'UTC'
            #     },
            #     'end': {
            #         'dateTime': appointment_data.get('end').get('dateTime'),
            #         'timeZone': 'UTC'
            #     }
            # }
            
            # 3. Create the event
            # created_event = service.me.calendar.events.post(body=event).execute()
            
            # For testing, we'll return a mock created event
            # This would normally be the API response
            return {
                "id": "def456",
                "subject": appointment_data.get("summary"),
                "start": {
                    "dateTime": appointment_data.get("start").get("dateTime"),
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": appointment_data.get("end").get("dateTime"),
                    "timeZone": "UTC"
                },
                "webLink": "https://outlook.office.com/calendar/item/def456"
            }
            
        except Exception as e:
            logger.error(f"Error creating appointment in Outlook Calendar: {str(e)}")
            raise
