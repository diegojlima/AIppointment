# functions/appointment-booking/src/calendar_integration.py
"""
Core Calendar Integration Service

This module provides the core calendar integration functionality for the AIppointment system.
It serves as the primary interface for interacting with different calendar providers (Google, Outlook).

Key responsibilities:
- Provides a unified interface for working with different calendar providers
- Handles core calendar operations (availability checking, appointment booking)
- Manages calendar provider-specific implementations
- Contains the core business logic for calendar operations

This module is used by:
1. The main application in main.py for direct calendar operations
2. The Bedrock Agent adapter (bedrock_calendar_adapter.py) which formats requests/responses
   for AWS Bedrock Agent compatibility
"""
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Type
import boto3
import json
import importlib

# Import the calendar service interface
from calendar_services.calendar_service_interface import CalendarServiceInterface

logger = logging.getLogger(__name__)

class CalendarProvider(Enum):
    """Enum for supported calendar providers"""
    GOOGLE = "google"
    OUTLOOK = "outlook"

class CalendarIntegration:
    """
    Calendar integration service that provides a unified interface
    for working with different calendar providers (Google, Outlook).
    
    This class handles:
    - Retrieving availability information
    - Booking appointments
    - Checking for scheduling conflicts
    - Converting between provider-specific formats
    """
    
    def __init__(self, dynamo_client=None):
        """
        Initialize the calendar integration service.
        
        Args:
            dynamo_client: Optional DynamoDB client for calendar credentials storage
        """
        self.dynamo_client = dynamo_client or boto3.client('dynamodb')
        self.table_name = os.environ.get('CALENDAR_CREDENTIALS_TABLE', 'calendar_credentials')
        
        # Cache for calendar service instances
        self._services = {}
        
        # Set the default calendar provider based on environment variable
        default_provider = os.environ.get('DEFAULT_CALENDAR_PROVIDER', 'GOOGLE').upper()
        try:
            self._default_provider = CalendarProvider[default_provider]
            logger.info(f"Default calendar provider set to {self._default_provider.value}")
        except KeyError:
            # Fallback to Google if the environment variable is not a valid provider
            self._default_provider = CalendarProvider.GOOGLE
            logger.info(f"Invalid calendar provider '{default_provider}'. Using {self._default_provider.value} as default")
        
        logger.info("Calendar integration service initialized")
    
    def get_calendar_service(self, provider: CalendarProvider) -> CalendarServiceInterface:
        """
        Factory method to get the appropriate calendar service.
        
        Args:
            provider: The calendar provider to use
            
        Returns:
            An instance of the appropriate calendar service
        """
        logger.info(f"Getting calendar service for provider: {provider.value}")
        
        if provider in self._services:
            logger.info(f"Using cached service for provider: {provider.value}")
            return self._services[provider]
        
        # Map provider enum to service class names
        provider_to_class = {
            CalendarProvider.GOOGLE: "calendar_services.google_calendar_v2.GoogleCalendarServiceV2",
            CalendarProvider.OUTLOOK: "calendar_services.outlook_calendar.OutlookCalendarService"
        }
        
        if provider not in provider_to_class:
            error_msg = f"Unsupported calendar provider: {provider}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Dynamically import the service class
        service_class_path = provider_to_class[provider]
        module_path, class_name = service_class_path.rsplit('.', 1)
        
        try:
            logger.info(f"Importing module: {module_path}")
            module = importlib.import_module(module_path)
            logger.info(f"Getting class: {class_name}")
            service_class = getattr(module, class_name)
            
            logger.info(f"Instantiating service: {class_name}")
            service = service_class()
            self._services[provider] = service
            logger.info(f"Successfully created calendar service for provider: {provider.value}")
            return service
        except ImportError as e:
            error_msg = f"Error importing calendar service module {module_path}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(f"Calendar service for provider {provider.value} is not available: {str(e)}")
        except AttributeError as e:
            error_msg = f"Error getting calendar service class {class_name}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(f"Calendar service class {class_name} not found: {str(e)}")
        except Exception as e:
            error_msg = f"Unexpected error creating calendar service: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(f"Error initializing calendar service for provider {provider.value}: {str(e)}")
    
    def _get_credentials_manager(self, provider: CalendarProvider):
        """
        Get a credentials manager for the specified provider.
        
        Args:
            provider: The calendar provider
            
        Returns:
            A credentials manager for the provider
        """
        # In a real implementation, this would return a credentials manager
        # that handles token retrieval, refresh, and storage.
        # For now, we'll return None as the services will handle this internally.
        return None
    
    def check_availability(self, provider: CalendarProvider, date: str, 
                          start_time: str, end_time: str) -> List[Dict[str, str]]:
        """
        Check for available time slots on a specific date.
        
        Args:
            provider: The calendar provider to use
            date: The date to check (YYYY-MM-DD)
            start_time: The start time to check from (HH:MM)
            end_time: The end time to check until (HH:MM)
            
        Returns:
            A list of available time slots with start and end times
        """
        logger.info(f"Checking availability for {date} from {start_time} to {end_time} with {provider.value}")
        
        service = self.get_calendar_service(provider)
        
        # Convert date and times to provider-specific format
        # Need full ISO format with seconds for Google Calendar (YYYY-MM-DDThh:mm:ss)
        start_datetime = f"{date}T{start_time}:00"
        end_datetime = f"{date}T{end_time}:00"
        
        logger.info(f"Formatted datetimes: {start_datetime} to {end_datetime}")
        
        # Get available slots from the calendar service
        available_slots = service.get_available_slots(start_datetime, end_datetime)
        
        logger.info(f"Found {len(available_slots)} available slots")
        return available_slots
    
    def book_appointment(self, provider: CalendarProvider, 
                        appointment_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Book an appointment on the calendar.
        
        Args:
            provider: The calendar provider to use
            appointment_details: Dictionary containing appointment details:
                - date: The date of the appointment (YYYY-MM-DD)
                - time: The time of the appointment (HH:MM)
                - duration_minutes: The duration of the appointment in minutes
                - purpose: The purpose or summary of the appointment
                - attendee_email: Email of the attendee (optional)
                
        Returns:
            Dictionary with booking result including:
                - success: Boolean indicating success
                - appointment_id: The ID of the created appointment
                - appointment_details: The details of the created appointment
        """
        logger.info(f"Booking appointment with {provider.value}: {appointment_details}")
        
        try:
            service = self.get_calendar_service(provider)
        except ValueError as e:
            logger.error(f"Failed to get calendar service for provider {provider.value}: {str(e)}")
            return {
                "success": False,
                "error": f"Calendar service unavailable: {str(e)}",
                "error_type": "ServiceUnavailable"
            }
        
        # Extract appointment details
        date = appointment_details.get("date")
        time = appointment_details.get("time")
        duration_minutes = appointment_details.get("duration_minutes", 60)
        purpose = appointment_details.get("purpose", "Appointment")
        attendee_email = appointment_details.get("attendee_email")
        
        # Calculate end time based on duration
        # Adding proper timezone information (defaulting to UTC)
        timezone_str = os.environ.get('DEFAULT_TIMEZONE', 'UTC')  # Use region name like 'UTC', 'America/Sao_Paulo'
        timezone_offset = os.environ.get('DEFAULT_TIMEZONE_OFFSET', 'Z')  # Use 'Z' for UTC or offsets like '+03:00'
        
        logger.info(f"Using timezone: {timezone_str} (offset: {timezone_offset})")
        
        # Format with timezone info
        start_datetime = f"{date}T{time}:00{timezone_offset}"
        
        # Convert to datetime object to add duration
        if timezone_offset == 'Z':
            dt_start = datetime.fromisoformat(f"{date}T{time}:00+00:00")
        else:
            dt_start = datetime.fromisoformat(f"{date}T{time}:00{timezone_offset}")
            
        dt_end = dt_start + timedelta(minutes=duration_minutes)
        
        # Ensure timezone is preserved in end_datetime
        if timezone_offset == 'Z':
            end_datetime = dt_end.isoformat().replace('+00:00', 'Z')
        else:
            end_datetime = dt_end.isoformat()
        
        # Format appointment data for the service
        appointment_data = {
            "summary": purpose,
            "start": {
                "dateTime": start_datetime,
                "timeZone": timezone_str
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": timezone_str
            }
        }
        
        # Always add the attendee - the service will handle it properly based on service account configuration
        if attendee_email:
            appointment_data["attendees"] = [{"email": attendee_email}]
        
        # Create the appointment
        try:
            logger.info(f"Calling calendar service create_appointment with data: {appointment_data}")
            result = service.create_appointment(appointment_data)
            
            logger.info(f"Appointment booked successfully with ID: {result.get('id')}")
            return {
                "success": True,
                "appointment_id": result.get("id"),
                "appointment_details": result
            }
            
        except Exception as e:
            logger.error(f"Failed to book appointment: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def has_conflicts(self, provider: CalendarProvider, date: str, 
                     time: str, duration_minutes: int = 60) -> bool:
        """
        Check if the specified time has any conflicts with existing appointments.
        
        Args:
            provider: The calendar provider to use
            date: The date to check (YYYY-MM-DD)
            time: The time to check (HH:MM)
            duration_minutes: The duration of the appointment in minutes
            
        Returns:
            True if there are conflicts, False otherwise
        """
        logger.info(f"Checking conflicts for {date} at {time} with {provider.value}")
        
        # Convert the specified time to start and end times
        start_time = time.split(':')[0].zfill(2) + ":" + time.split(':')[1].zfill(2)
        
        # Calculate the business hours (e.g., 9 AM to 5 PM)
        business_start = "09:00"
        business_end = "17:00"
        
        # Get available slots for the entire day
        available_slots = self.check_availability(
            provider=provider,
            date=date,
            start_time=business_start,
            end_time=business_end
        )
        
        # Calculate the target time slot
        target_start = f"{date}T{start_time}:00"
        dt_start = datetime.fromisoformat(target_start)
        dt_end = dt_start + timedelta(minutes=duration_minutes)
        target_end = dt_end.isoformat()
        
        # Check if the target time slot is in any of the available slots
        for slot in available_slots:
            slot_start = datetime.fromisoformat(slot["start"])
            slot_end = datetime.fromisoformat(slot["end"])
            
            # If the requested time fits within an available slot, there's no conflict
            if slot_start <= dt_start and dt_end <= slot_end:
                logger.info(f"No conflicts found for {date} at {time}")
                return False
        
        logger.info(f"Conflicts found for {date} at {time}")
        return True
    
    @property
    def default_calendar_provider(self) -> CalendarProvider:
        """
        Get the default calendar provider
        
        Returns:
            The default calendar provider enum value
        """
        return self._default_provider
    
    def get_next_available_slot(self, provider: CalendarProvider, 
                               date: str, time: str = None) -> Optional[Dict[str, str]]:
        """
        Get the next available time slot on or after the specified date and time.
        
        Args:
            provider: The calendar provider to use
            date: The date to check (YYYY-MM-DD)
            time: The time to start checking from (HH:MM), or None for start of day
            
        Returns:
            Dictionary with start and end times for the next available slot,
            or None if no slots are available
        """
        logger.info(f"Finding next available slot on/after {date} {time or '(start of day)'}")
        
        # Default to start of business day if no time provided
        if not time:
            time = "09:00"
        
        # Get available slots for the day
        available_slots = self.check_availability(
            provider=provider,
            date=date,
            start_time=time,
            end_time="17:00"  # End of business day
        )
        
        if not available_slots:
            # Try the next day if no slots available today
            next_date = (datetime.fromisoformat(date) + timedelta(days=1)).strftime("%Y-%m-%d")
            return self.get_next_available_slot(provider, next_date)
        
        # Convert the specified time to a datetime object
        target_time = f"{date}T{time}:00"
        dt_target = datetime.fromisoformat(target_time)
        
        # Find the first slot that starts after the target time
        for slot in available_slots:
            slot_start = datetime.fromisoformat(slot["start"])
            
            if slot_start >= dt_target:
                logger.info(f"Next available slot: {slot['start']} - {slot['end']}")
                return slot
        
        # If we've checked all slots and none are after the target time,
        # try the next day
        next_date = (datetime.fromisoformat(date) + timedelta(days=1)).strftime("%Y-%m-%d")
        return self.get_next_available_slot(provider, next_date)
