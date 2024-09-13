import json
import boto3
import logging
from datetime import datetime, timedelta
import os
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_dynamodb_client():
    return boto3.client('dynamodb')

def get_bedrock_client():
    return boto3.client('bedrock-runtime', region_name='us-west-2')

def process_message(message):
    logger.info(f"Processing message: {message}")
    bedrock = get_bedrock_client()
    prompt = f"""Extract appointment details from this message: "{message}"

Provide the following information in JSON format:
1. date (YYYY-MM-DD)
2. time (HH:MM)
3. purpose

If any information is missing, use null."""

    try:
        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 300,
            "temperature": 0.5,
            "top_p": 0.9,
        })

        # Log the request details
        logger.info("Invoking Bedrock model with parameters:")
        logger.info(f"Model ID: 'anthropic.claude-3-sonnet-20240229-v1:0:28k'")
        logger.info(f"Request Body: {body}")

        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0:28k',  # Exact model ID
            accept='application/json',
            contentType='application/json',
            body=body
        )

        # Log the response
        response_body_raw = response['body'].read()
        logger.info(f"Raw response body: {response_body_raw}")

        response_body = json.loads(response_body_raw)
        logger.info(f"Parsed response body: {json.dumps(response_body, indent=2)}")

        # Extract the generated text
        generated_text = response_body.get('completion') or response_body.get('generated_text') or response_body.get('content')
        logger.info(f"Generated text: {generated_text}")

        if not generated_text:
            logger.error("No generated text found in the response.")
            return None

        # Parse the JSON from the generated text
        appointment_details = json.loads(generated_text)
        logger.info(f"Extracted appointment details: {appointment_details}")

        return appointment_details

    except Exception as e:
        logger.error("An error occurred while processing the message", exc_info=True)
        print(f"Error processing message: {str(e)}")
        return None

def validate_appointment(date, time):
    logger.info(f"Validating appointment with date: {date} and time: {time}")
    if not date or not time:
        return False
    try:
        appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        now = datetime.now()
        if appointment_datetime < now:
            logger.warning("Appointment date/time is in the past.")
            return False
        if appointment_datetime > now + timedelta(days=90):
            logger.warning("Appointment date/time is more than 90 days in the future.")
            return False
        return True
    except ValueError:
        logger.error("Invalid date/time format.")
        return False

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    dynamodb = get_dynamodb_client()
    table_name = os.environ['DYNAMODB_TABLE']
    logger.info(f"DynamoDB table name: {table_name}")

    try:
        body = json.loads(event.get('body', '{}'))
        logger.info(f"Parsed request body: {body}")

        phone_number = body.get('phone_number')
        message = body.get('message')

        if not phone_number or not message:
            logger.error("Phone number or message is missing.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Phone number and message are required'})
            }

        processed_message = process_message(message)

        if not processed_message:
            logger.error("Unable to process the message.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unable to process the message'})
            }

        is_valid = validate_appointment(processed_message.get('date'), processed_message.get('time'))
        logger.info(f"Is appointment valid? {is_valid}")

        item = {
            'PhoneNumber': {'S': phone_number},
            'AppointmentDate': {'S': processed_message.get('date', '')},
            'AppointmentTime': {'S': processed_message.get('time', '')},
            'Purpose': {'S': processed_message.get('purpose', '')},
            'IsValid': {'BOOL': is_valid},
            'CreatedAt': {'S': datetime.utcnow().isoformat()}
        }
        logger.info(f"Item to put into DynamoDB: {item}")

        dynamodb.put_item(TableName=table_name, Item=item)
        logger.info("Successfully put item into DynamoDB.")

        response_message = 'Appointment request processed successfully'
        if not is_valid:
            response_message += ', but the requested date/time is not valid'
            logger.warning("Appointment date/time is not valid.")

        logger.info(f"Response message: {response_message}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': response_message,
                'details': processed_message,
                'is_valid': is_valid
            })
        }
    except Exception as e:
        logger.error("An error occurred in lambda_handler", exc_info=True)
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
