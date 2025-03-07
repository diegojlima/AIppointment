#!/usr/bin/env python3
"""
Migration script for AIppointment data from old LangChain structure to AWS Bedrock Agents structure.

This script:
1. Reads appointments from the old DynamoDB table
2. Converts them to the new format
3. Writes them to the new DynamoDB tables
4. Creates conversation history entries for existing users

Usage:
    python migrate_appointments_data.py --source-table <old-table> --target-table <new-table> --conversation-table <conversation-table>
"""
import argparse
import boto3
import json
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Migrate appointment data from old to new structure')
    parser.add_argument('--source-table', required=True, help='Source DynamoDB table name')
    parser.add_argument('--target-table', required=True, help='Target DynamoDB table name')
    parser.add_argument('--conversation-table', required=True, help='Conversation history table name')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without writing data')
    return parser.parse_args()

def read_source_appointments(source_table_name):
    """Read appointments from source table."""
    logger.info(f"Reading appointments from {source_table_name}")
    
    table = dynamodb.Table(source_table_name)
    response = table.scan()
    items = response.get('Items', [])
    
    # Continue scanning if we haven't retrieved all items
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    logger.info(f"Read {len(items)} appointments from source table")
    return items

def convert_appointment(old_appointment):
    """Convert appointment from old format to new format."""
    # Extract the basic appointment details
    phone_number = old_appointment.get('PhoneNumber')
    created_at = old_appointment.get('CreatedAt')
    
    # Extract appointment details from the old format
    appointment_details = old_appointment.get('AppointmentDetails', {})
    date = appointment_details.get('date')
    time = appointment_details.get('time', '')
    purpose = appointment_details.get('purpose', 'Appointment')
    
    # Create a unique ID for the appointment
    appointment_id = f"{phone_number}-{date}-{time}".replace(":", "").replace("/", "")
    if 'id' in old_appointment:
        appointment_id = old_appointment['id']
        
    # Calculate end time (assume 1 hour duration if not specified)
    try:
        start_time = datetime.strptime(time, "%H:%M")
        end_time = (start_time.replace(minute=start_time.minute + 60)).strftime("%H:%M")
    except (ValueError, TypeError):
        end_time = ""
    
    # Create the new appointment object
    new_appointment = {
        'id': appointment_id,
        'userId': phone_number,
        'date': date,
        'startTime': time,
        'endTime': end_time,
        'purpose': purpose,
        'status': 'confirmed',
        'createdAt': created_at or datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    }
    
    # Add optional fields if present in the old format
    if 'userEmail' in appointment_details:
        new_appointment['userEmail'] = appointment_details['userEmail']
    
    if 'calendarEventId' in appointment_details:
        new_appointment['calendarEventId'] = appointment_details['calendarEventId']
    
    if 'calendarLink' in appointment_details:
        new_appointment['calendarLink'] = appointment_details['calendarLink']
    
    return new_appointment

def create_conversation_history(phone_numbers, conversation_table_name, dry_run=False):
    """Create conversation history entries for existing users."""
    logger.info(f"Creating conversation history for {len(phone_numbers)} users")
    
    conversation_table = dynamodb.Table(conversation_table_name)
    timestamp = datetime.utcnow().isoformat()
    
    for phone_number in phone_numbers:
        conversation_id = str(uuid.uuid4())
        
        if not dry_run:
            conversation_table.put_item(
                Item={
                    'conversationId': conversation_id,
                    'senderId': phone_number,
                    'createdAt': timestamp,
                    'updatedAt': timestamp,
                    'messageCount': 0
                }
            )
        
        logger.info(f"Created conversation history for {phone_number}")
    
    return len(phone_numbers)

def write_target_appointments(appointments, target_table_name, dry_run=False):
    """Write appointments to target table."""
    logger.info(f"Writing {len(appointments)} appointments to {target_table_name}")
    
    if dry_run:
        logger.info("DRY RUN: Would write appointments to target table")
        for appointment in appointments[:5]:
            logger.info(f"DRY RUN: Would write appointment: {json.dumps(appointment, indent=2)}")
        if len(appointments) > 5:
            logger.info(f"DRY RUN: And {len(appointments) - 5} more appointments...")
        return
    
    table = dynamodb.Table(target_table_name)
    
    # Write appointments in batches of 25 (DynamoDB batch_write_item limit)
    with table.batch_writer() as batch:
        for appointment in appointments:
            batch.put_item(Item=appointment)
    
    logger.info(f"Wrote {len(appointments)} appointments to target table")

def main():
    """Main migration function."""
    args = parse_args()
    
    if args.dry_run:
        logger.info("Performing DRY RUN - no data will be written")
    
    # Read source appointments
    source_appointments = read_source_appointments(args.source_table)
    
    # Convert appointments to new format
    target_appointments = [convert_appointment(appointment) for appointment in source_appointments]
    
    # Write appointments to target table
    write_target_appointments(target_appointments, args.target_table, args.dry_run)
    
    # Create conversation history for existing users
    unique_phone_numbers = set(appointment['userId'] for appointment in target_appointments)
    create_conversation_history(unique_phone_numbers, args.conversation_table, args.dry_run)
    
    logger.info("Migration completed successfully")

if __name__ == "__main__":
    main()
