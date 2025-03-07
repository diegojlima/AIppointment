"""
Calendar Service Interface Module

This module defines the abstract base class interface for calendar services.
All calendar service implementations should inherit from this class.
"""
import abc
from typing import Dict, Any, List, Optional
from datetime import datetime

class CalendarServiceInterface(abc.ABC):
    """
    Abstract base class defining the interface for calendar services.
    
    This interface ensures that all calendar service implementations
    provide a consistent API regardless of the underlying provider.
    """
    
    @abc.abstractmethod
    def get_available_slots(self, start_datetime: str, end_datetime: str) -> List[Dict[str, str]]:
        """
        Get available time slots in the calendar between the given time range.
        
        Args:
            start_datetime: The start datetime in ISO format (YYYY-MM-DDThh:mm:ss)
            end_datetime: The end datetime in ISO format (YYYY-MM-DDThh:mm:ss)
            
        Returns:
            A list of available time slots, each containing 'start' and 'end' in ISO format
        """
        pass
    
    @abc.abstractmethod
    def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new appointment in the calendar.
        
        Args:
            appointment_data: Dictionary containing appointment details:
                - summary: Title/purpose of the appointment
                - start: Dictionary with 'dateTime' field
                - end: Dictionary with 'dateTime' field
                - attendees: Optional list of attendee dictionaries
                - description: Optional description
                
        Returns:
            Dictionary with the created appointment details
        """
        pass
    
    @abc.abstractmethod
    def update_appointment(self, appointment_id: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing appointment in the calendar.
        
        Args:
            appointment_id: The ID of the appointment to update
            appointment_data: Dictionary containing updated appointment details
                
        Returns:
            Dictionary with the updated appointment details
        """
        pass
    
    @abc.abstractmethod
    def delete_appointment(self, appointment_id: str) -> bool:
        """
        Delete an appointment from the calendar.
        
        Args:
            appointment_id: The ID of the appointment to delete
                
        Returns:
            True if the appointment was deleted successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def get_appointment(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific appointment.
        
        Args:
            appointment_id: The ID of the appointment to retrieve
                
        Returns:
            Dictionary with the appointment details, or None if not found
        """
        pass
