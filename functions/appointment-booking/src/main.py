# ./functions/appointment-booking/src/main.py
import json
import boto3
from datetime import datetime, timedelta
import os
# from langchain.prompts import ChatPromptTemplate
# from langchain.chains import LLMChain
from langchain_aws import BedrockChat

def get_dynamodb_table():
    dynamodb = boto3.client('dynamodb')
    return dynamodb

def get_llm():
    return BedrockChat(
        model_id="anthropic.claude-v2",
        model_kwargs={
            "max_tokens_to_sample": 300,
            "temperature": 0.5,
            "top_p": 0.9
        },
        region_name="us-west-2"  # Replace with your AWS region
    )

def process_message(message):
    # llm = get_llm()
    # prompt = ChatPromptTemplate.from_messages([
    #     ("system", "You are an AI assistant for a medical clinic, extracting appointment details from patient messages."),
    #     ("human", "Extract appointment details from this message: {message}\n\nProvide the following information in JSON format:\n1. date (YYYY-MM-DD)\n2. time (HH:MM)\n3. purpose\n\nIf any information is missing, use null.")
    # ])
    # chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        # result = chain.run(message=message)
        # ChatBedrock might return a string that's not JSON-formatted, so we'll try to extract JSON from it
        # json_start = result.find('{')
        # json_end = result.rfind('}') + 1
        # json_str = result[json_start:json_end]
        # return json.loads(json_str)
        return 'test'
    except Exception as e:
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
    dynamodb = get_dynamodb_table()
    table_name = os.environ['DYNAMODB_TABLE']
    
    try:
        body = json.loads(event['body'])
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
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }