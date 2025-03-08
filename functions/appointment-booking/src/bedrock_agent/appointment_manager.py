"""
AppointmentManager action group for AWS Bedrock Agent

This action group handles:
- Viewing upcoming appointments
- Rescheduling appointments
- Cancelling appointments
- Sending reminders
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

class AppointmentManager:
    """
    Action group for managing existing appointments
    """
    
    def __init__(self, dynamodb_client=None, calendar_integration=None):
        """
        Initialize the AppointmentManager action group
        
        Args:
            dynamodb_client: Optional DynamoDB client
            calendar_integration: Optional calendar integration service
        """
        self.dynamodb = dynamodb_client or boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE', 'appointment-system-appointments')
        
        # If calendar integration is provided, use it
        self.calendar_integration = calendar_integration
        
        # Log initialization
        logger.info("AppointmentManager action group initialized")
    
    def get_appointments(self, user_id: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Get appointments for a user with optional date filtering
        
        Args:
            user_id: The user ID to get appointments for
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            Dictionary with appointments and status
        """
        logger.info(f"Getting appointments for user {user_id} from {start_date} to {end_date}")
        
        try:
            # If no date range is provided, use the current date
            if not start_date:
                start_date = datetime.now().strftime("%Y-%m-%d")
            
            # Create expression attributes
            expression_attributes = {
                ':user_id': {'S': user_id}
            }
            
            # Create the filter expression
            filter_expression = "userId = :user_id"
            
            # Add date filters if provided
            if start_date:
                filter_expression += " AND #date >= :start_date"
                expression_attributes[':start_date'] = {'S': start_date}
            
            if end_date:
                filter_expression += " AND #date <= :end_date"
                expression_attributes[':end_date'] = {'S': end_date}
            
            # Add attribute names for reserved words
            expression_attribute_names = {
                '#date': 'date'
            }
            
            # Query the appointments
            response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_attributes,
                ExpressionAttributeNames=expression_attribute_names
            )
            
            # Extract and format the appointments
            appointments = []
            for item in response.get('Items', []):
                appointment = {k: list(v.values())[0] for k, v in item.items()}
                appointments.append(appointment)
            
            # Sort appointments by date and time
            appointments.sort(key=lambda x: (x['date'], x['startTime']))
            
            return {
                "userId": user_id,
                "appointments": appointments,
                "count": len(appointments),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting appointments: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def reschedule_appointment(self, 
                              appointment_id: str, 
                              new_date: str, 
                              new_time: str) -> Dict[str, Any]:
        """
        Reschedule an existing appointment
        
        Args:
            appointment_id: The ID of the appointment to reschedule
            new_date: The new date for the appointment (YYYY-MM-DD)
            new_time: The new time for the appointment (HH:MM)
            
        Returns:
            Dictionary with updated appointment details and status
        """
        logger.info(f"Rescheduling appointment {appointment_id} to {new_date} at {new_time}")
        
        try:
            # Validate the new date and time
            new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            
            if new_datetime < now:
                return {
                    "success": False,
                    "error": "New appointment date/time is in the past"
                }
            
            # Get the current appointment
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
            
            # Extract the current appointment details
            current_appointment = {k: list(v.values())[0] for k, v in response['Item'].items()}
            
            # Calculate the duration from the current appointment
            duration_minutes = int(current_appointment.get('durationMinutes', 60))
            
            # Calculate new end time
            new_end_time = (new_datetime + timedelta(minutes=duration_minutes)).strftime("%H:%M")
            
            # Update the appointment in DynamoDB
            update_response = self.dynamodb.update_item(
                TableName=self.table_name,
                Key={
                    'id': {'S': appointment_id}
                },
                UpdateExpression="SET #date = :date, startTime = :start_time, endTime = :end_time, updatedAt = :updated_at",
                ExpressionAttributeNames={
                    '#date': 'date'
                },
                ExpressionAttributeValues={
                    ':date': {'S': new_date},
                    ':start_time': {'S': new_time},
                    ':end_time': {'S': new_end_time},
                    ':updated_at': {'S': datetime.utcnow().isoformat()}
                },
                ReturnValues="ALL_NEW"
            )
            
            # Extract the updated appointment
            updated_appointment = {k: list(v.values())[0] for k, v in update_response.get('Attributes', {}).items()}
            
            # If calendar integration is available, update the calendar event
            if self.calendar_integration and 'userEmail' in current_appointment:
                # Update the calendar event
                calendar_result = self.calendar_integration.update_appointment(
                    provider=self.calendar_integration.default_calendar_provider,
                    appointment_id=current_appointment.get('calendarEventId'),
                    appointment_details={
                        "date": new_date,
                        "time": new_time,
                        "duration_minutes": duration_minutes,
                        "purpose": current_appointment.get('purpose')
                    }
                )
                
                if calendar_result["success"] and calendar_result.get("appointment_details"):
                    # Update the calendar link if available
                    calendar_link = calendar_result.get("appointment_details", {}).get("htmlLink")
                    if calendar_link:
                        updated_appointment['calendarLink'] = calendar_link
            
            return {
                "appointmentId": appointment_id,
                "oldDate": current_appointment['date'],
                "oldTime": current_appointment['startTime'],
                "newDate": new_date,
                "newTime": new_time,
                "updatedAppointment": updated_appointment,
                "success": True
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error rescheduling appointment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Cancel an existing appointment
        
        Args:
            appointment_id: The ID of the appointment to cancel
            
        Returns:
            Dictionary with cancellation status
        """
        logger.info(f"Cancelling appointment {appointment_id}")
        
        try:
            # Get the current appointment
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
            
            # Extract the current appointment details
            current_appointment = {k: list(v.values())[0] for k, v in response['Item'].items()}
            
            # Update the appointment status in DynamoDB
            update_response = self.dynamodb.update_item(
                TableName=self.table_name,
                Key={
                    'id': {'S': appointment_id}
                },
                UpdateExpression="SET #status = :status, updatedAt = :updated_at",
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': {'S': 'cancelled'},
                    ':updated_at': {'S': datetime.utcnow().isoformat()}
                },
                ReturnValues="ALL_NEW"
            )
            
            # Extract the updated appointment
            updated_appointment = {k: list(v.values())[0] for k, v in update_response.get('Attributes', {}).items()}
            
            # If calendar integration is available, cancel the calendar event
            if self.calendar_integration and 'calendarEventId' in current_appointment:
                calendar_result = self.calendar_integration.cancel_appointment(
                    provider=self.calendar_integration.default_calendar_provider,
                    appointment_id=current_appointment.get('calendarEventId')
                )
            
            return {
                "appointmentId": appointment_id,
                "date": current_appointment['date'],
                "time": current_appointment['startTime'],
                "status": "cancelled",
                "success": True
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error cancelling appointment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_reminder(self, appointment_id: str) -> Dict[str, Any]:
        """
        Send a reminder for an upcoming appointment
        
        Args:
            appointment_id: The ID of the appointment to send a reminder for
            
        Returns:
            Dictionary with reminder status
        """
        logger.info(f"Sending reminder for appointment {appointment_id}")
        
        try:
            # Get the appointment by scanning with filter
            response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression="appointmentId = :appointmentId",
                ExpressionAttributeValues={
                    ':appointmentId': {'S': appointment_id}
                },
                Limit=1
            )
            
            # Extract the item from scan results
            if response.get('Items', []):
                item = response['Items'][0]
                response = {'Item': item}
            
            
            # Check if the appointment exists
            if 'Item' not in response:
                return {
                    "success": False,
                    "error": "Appointment not found"
                }
            
            # Extract appointment details
            appointment = {k: list(v.values())[0] for k, v in response['Item'].items()}
            
            # Check if the appointment is still active
            if appointment['status'] != 'confirmed':
                return {
                    "success": False,
                    "error": f"Cannot send reminder for {appointment['status']} appointment"
                }
            
            # Format the reminder message
            date_formatted = datetime.strptime(appointment['date'], "%Y-%m-%d").strftime("%A, %B %d, %Y")
            
            reminder_message = (
                f"Reminder: You have an appointment scheduled for {date_formatted} at {appointment['startTime']}. "
                f"Purpose: {appointment['purpose']}. "
                f"Please arrive 10 minutes early."
            )
            
            # Add calendar link if available
            if 'calendarLink' in appointment:
                reminder_message += f" View in calendar: {appointment['calendarLink']}"
            
            # Update the reminder sent status in DynamoDB
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={
                    'id': {'S': appointment_id}
                },
                UpdateExpression="SET reminderSent = :reminder_sent, updatedAt = :updated_at",
                ExpressionAttributeValues={
                    ':reminder_sent': {'BOOL': True},
                    ':updated_at': {'S': datetime.utcnow().isoformat()}
                }
            )
            
            return {
                "appointmentId": appointment_id,
                "userId": appointment['userId'],
                "reminderMessage": reminder_message,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Lambda handler for the action group
def lambda_handler(event, context):
    """
    Lambda handler for the AppointmentManager action group
    
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
    action_group = AppointmentManager()
    
    # Route to the appropriate method
    if action_name == 'get_appointments':
        user_id = parameters.get('user_id')
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        
        return action_group.get_appointments(user_id, start_date, end_date)
    
    elif action_name == 'reschedule_appointment':
        appointment_id = parameters.get('appointment_id')
        new_date = parameters.get('new_date')
        new_time = parameters.get('new_time')
        
        return action_group.reschedule_appointment(appointment_id, new_date, new_time)
    
    elif action_name == 'cancel_appointment':
        appointment_id = parameters.get('appointment_id')
        
        return action_group.cancel_appointment(appointment_id)
    
    elif action_name == 'send_reminder':
        appointment_id = parameters.get('appointment_id')
        
        return action_group.send_reminder(appointment_id)
    
    else:
        return {
            "success": False,
            "error": f"Unknown action: {action_name}"
        }
