# ./functions/appointment-booking/src/main.py

import json
import boto3
from datetime import datetime, timedelta
import os
import traceback

def get_dynamodb_client():
    return boto3.client('dynamodb')

def get_bedrock_client():
    return boto3.client('bedrock-runtime', region_name='us-west-2')

def process_message(message):
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
            # Include any other parameters required by the model
        })

        response = bedrock.invoke_model(
            modelId='anthropic.claude-v2',
            accept='application/json',
            contentType='application/json',
            body=body
        )

        response_body = json.loads(response.get('body').read())
        print(f"Response body: {response_body}")

        # Adjust the key based on actual response structure
        generated_text = response_body.get('completion') or response_body.get('generated_text') or response_body.get('content')

        # Parse the JSON from the generated text
        return json.loads(generated_text)

    except Exception as e:
        traceback.print_exc()
        print(f"Error processing message: {str(e)}")
        return None

def validate_appointment(date, time):
    if not date or not time:
        return False
    try:
        appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        now = datetime.now()
        if appointment_datetime < now:
            return False
        if appointment_datetime > now + timedelta(days=90):
            return False
        return True
    except ValueError:
        return False

def lambda_handler(event, context):
    dynamodb = get_dynamodb_client()
    table_name = os.environ['DYNAMODB_TABLE']

    try:
        body = json.loads(event.get('body', '{}'))
        phone_number = body.get('phone_number')
        message = body.get('message')

        if not phone_number or not message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Phone number and message are required'})
            }

        processed_message = process_message(message)

        if not processed_message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unable to process the message'})
            }

        is_valid = validate_appointment(processed_message.get('date'), processed_message.get('time'))

        item = {
            'PhoneNumber': {'S': phone_number},
            'AppointmentDate': {'S': processed_message.get('date', '')},
            'AppointmentTime': {'S': processed_message.get('time', '')},
            'Purpose': {'S': processed_message.get('purpose', '')},
            'IsValid': {'BOOL': is_valid},
            'CreatedAt': {'S': datetime.utcnow().isoformat()}
        }

        dynamodb.put_item(TableName=table_name, Item=item)

        response_message = 'Appointment request processed successfully'
        if not is_valid:
            response_message += ', but the requested date/time is not valid'

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': response_message,
                'details': processed_message,
                'is_valid': is_valid
            })
        }
    except Exception as e:
        traceback.print_exc()
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
