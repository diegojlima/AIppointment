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
from datetime import datetime, timedelta
from typing import Dict, Any, List
from botocore.exceptions import ClientError

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
                available_slots = self.calendar_integration.check_availability(
                    provider=self.calendar_integration.default_calendar_provider,
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
            appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            
            if appointment_datetime < now:
                return {
                    "success": False,
                    "error": "Appointment date/time is in the past"
                }
            
            # Create a unique appointment ID
            appointment_id = f"{user_id}-{date}-{time}".replace(":", "")
            
            # Calculate end time
            end_time = (appointment_datetime + timedelta(minutes=duration_minutes)).strftime("%H:%M")
            
            # Create the appointment item
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
            
            # Save to DynamoDB
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=appointment_item
            )
            
            # If calendar integration is available, add to calendar
            calendar_link = None
            if self.calendar_integration and user_email:
                calendar_result = self.calendar_integration.book_appointment(
                    provider=self.calendar_integration.default_calendar_provider,
                    appointment_details={
                        "date": date,
                        "time": time,
                        "duration_minutes": duration_minutes,
                        "purpose": purpose,
                        "attendee_email": user_email
                    }
                )
                
                if calendar_result["success"]:
                    calendar_link = calendar_result.get("appointment_details", {}).get("htmlLink")
            
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
        Dictionary with the action response
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Extract the action name and parameters - support different structures
    action_group_info = event.get('actionGroup', {})
    action_name = action_group_info.get('actionName') if 'actionName' in action_group_info else action_group_info.get('name', '')
    parameters = event.get('parameters', {})
    
    # Initialize the action group
    action_group = AppointmentCreator()
    
    # Route to the appropriate method
    if action_name == 'check_availability' or action_name == 'checkAvailability':
        date = parameters.get('date')
        # Support both snake_case and camelCase parameter names
        duration_minutes = int(parameters.get('duration_minutes', parameters.get('durationMinutes', 60)))
        
        return action_group.check_availability(date, duration_minutes)
    
    elif action_name == 'create_appointment' or action_name == 'createAppointment':
        # Support both snake_case and camelCase parameter names
        user_id = parameters.get('user_id', parameters.get('userId'))
        date = parameters.get('date')
        time = parameters.get('time')
        purpose = parameters.get('purpose')
        duration_minutes = int(parameters.get('duration_minutes', parameters.get('durationMinutes', 60)))
        user_email = parameters.get('user_email', parameters.get('userEmail'))
        
        return action_group.create_appointment(
            user_id, date, time, purpose, duration_minutes, user_email
        )
    
    elif action_name == 'generate_confirmation' or action_name == 'generateConfirmation':
        appointment_id = parameters.get('appointment_id', parameters.get('appointmentId'))
        
        return action_group.generate_confirmation(appointment_id)
    
    else:
        return {
            "success": False,
            "error": f"Unknown action: {action_name}"
        }
