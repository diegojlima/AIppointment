# AIppointment - AWS Bedrock Agents Architecture

## Introduction

AIppointment is an AI-powered appointment booking system that leverages AWS Bedrock Agents for natural language understanding and WhatsApp integration for communication. This README documents the simplified architecture implementation based on AWS Bedrock Agents.

## Architecture Overview

The AIppointment system follows a serverless architecture on AWS with the following components:

- **AWS Lambda**: Core processing logic in Python 3.12
- **AWS Bedrock Agents**: Handles conversation flow and decision making
- **AWS End User Messaging**: WhatsApp integration
- **Amazon DynamoDB**: Appointment data storage
- **Google/Outlook Calendar API**: Calendar integration

The system is organized into the following core components:

1. **Main Lambda Handler**: Entry point for all requests
2. **Bedrock Agent Action Groups**:
   - AppointmentCreator: Create new appointments
   - AppointmentManager: Manage existing appointments
   - CalendarIntegrator: Integrate with external calendar systems
3. **WhatsApp Integration**: Handle messaging via AWS End User Messaging
4. **Calendar Integration**: Connect with Google Calendar and Microsoft Outlook

## Implementation Details

### AWS Bedrock Agents Integration

The system uses AWS Bedrock Agents to handle conversational AI capabilities:

1. **Agent Schema**: OpenAPI schema defining the agent capabilities
2. **Action Groups**: Lambda functions that implement specific appointment-related actions
3. **Conversation Management**: Persistent session management across messages

### AWS End User Messaging for WhatsApp

The system integrates with WhatsApp using AWS End User Messaging:

1. **Webhook Handling**: Process incoming WhatsApp messages
2. **Message Sending**: Send text and template messages to users
3. **Rich Messaging**: Support for formatted messages and templates

### Calendar Integration

The system provides flexible calendar integration:

1. **Google Calendar**: Check availability and book appointments in Google Calendar
2. **Microsoft Outlook**: Alternative calendar system integration
3. **Availability Checking**: Find available time slots for appointments

## Deployment Guide

### Prerequisites

1. AWS Account with appropriate permissions
2. WhatsApp Business Account with AWS End User Messaging set up
3. Google Cloud or Microsoft Azure account for calendar APIs

### Step 1: Set up AWS Resources

1. **Create DynamoDB Tables**:
   ```bash
   aws dynamodb create-table \
     --table-name Appointments \
     --attribute-definitions AttributeName=id,AttributeType=S \
     --key-schema AttributeName=id,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   
   aws dynamodb create-table \
     --table-name ConversationHistory \
     --attribute-definitions AttributeName=conversationId,AttributeType=S \
     --key-schema AttributeName=conversationId,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   
   aws dynamodb create-table \
     --table-name ConversationHistoryMessages \
     --attribute-definitions \
       AttributeName=messageId,AttributeType=S \
       AttributeName=conversationId,AttributeType=S \
     --key-schema \
       AttributeName=messageId,KeyType=HASH \
       AttributeName=conversationId,KeyType=RANGE \
     --billing-mode PAY_PER_REQUEST
   ```

2. **Create a Bedrock Agent**:
   - Go to AWS Bedrock console
   - Create a new agent
   - Upload the `bedrock_agent/schema/agent_schema.json` file
   - Create action groups for AppointmentCreator, AppointmentManager, and CalendarIntegrator
   - Set up the agent with Claude 3 Sonnet as the foundation model

3. **Set up AWS End User Messaging**:
   - Configure AWS End User Messaging for WhatsApp
   - Link your WhatsApp Business Account
   - Set up the webhook URL to point to your deployed Lambda function

### Step 2: Deploy Lambda Functions

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt -t ./package
   ```

2. **Package Lambda function**:
   ```bash
   cd package
   zip -r ../lambda_function.zip .
   cd ..
   zip -g lambda_function.zip functions/appointment-booking/src/*.py
   zip -r -g lambda_function.zip functions/appointment-booking/src/bedrock_agent/
   ```

3. **Deploy Lambda function**:
   ```bash
   aws lambda create-function \
     --function-name AIppointment \
     --runtime python3.12 \
     --handler functions.appointment-booking.src.main.lambda_handler \
     --role arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_ROLE \
     --zip-file fileb://lambda_function.zip \
     --environment "Variables={BEDROCK_AGENT_ID=YOUR_AGENT_ID,BEDROCK_AGENT_ALIAS_ID=YOUR_AGENT_ALIAS_ID,WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_NUMBER_ID,WHATSAPP_WEBHOOK_VERIFY_TOKEN=YOUR_VERIFY_TOKEN,DEFAULT_CALENDAR_PROVIDER=GOOGLE}"
   ```

4. **Set up API Gateway**:
   ```bash
   aws apigateway create-rest-api --name AIppointmentAPI
   ```

### Step 3: Configure Calendar Integration

1. **Google Calendar**:
   - Create a service account in Google Cloud Console
   - Download the service account JSON credentials
   - Store credentials in AWS Secrets Manager
   - Set the appropriate environment variables in your Lambda function

2. **Microsoft Outlook**:
   - Register an application in Azure Active Directory
   - Create a client secret
   - Store credentials in AWS Secrets Manager
   - Set the appropriate environment variables in your Lambda function

## Usage Example

### Setting Up AWS Bedrock Agent

1. **Create the agent**:
   - Go to AWS Bedrock console
   - Create a new agent named "AIppointment"
   - Upload the `agent_schema.json` file
   - Set up action groups to match the schema

2. **Set up agent instructions**:
   ```
   You are an appointment scheduling assistant integrated with WhatsApp.
   Your job is to help users schedule, reschedule, and cancel appointments.

   Key tasks you can perform:
   1. Check availability for a specific date
   2. Create new appointments
   3. View existing appointments
   4. Reschedule appointments
   5. Cancel appointments

   When talking to users:
   - Be friendly and conversational
   - Ask for clarification when needed
   - Confirm details before making changes
   - Offer alternative time slots if requested times are unavailable
   - Send confirmation messages with appointment details

   Available time slots are hourly from 9 AM to 5 PM, Monday through Friday.
   Appointments are 1 hour by default unless specified otherwise.
   ```

### Testing the Integration

1. **Send a WhatsApp message to your business number**:
   ```
   I need a doctor's appointment next Tuesday at 2 PM
   ```

2. **The system will**:
   - Process the message through AWS End User Messaging
   - Invoke the Bedrock Agent to understand the intent and extract appointment details
   - Use the AppointmentCreator action group to check availability and create the appointment
   - Respond with a confirmation message

## Monitoring and Troubleshooting

1. **AWS CloudWatch Logs**:
   - Monitor Lambda function logs
   - Check for errors in the Bedrock Agent invocation

2. **DynamoDB Tables**:
   - Check the Appointments table for created appointments
   - Review ConversationHistory and ConversationHistoryMessages for message flow

## Next Steps

1. **Enhanced WhatsApp Integration**:
   - Implement template messages for better formatting
   - Add interactive buttons for appointment confirmation
   - Support for multimedia messages

2. **Advanced Calendar Integration**:
   - Implement two-way synchronization
   - Add support for recurring appointments
   - Integrate with more calendar providers

3. **Analytics and Monitoring**:
   - Implement usage analytics
   - Set up monitoring and alerting
   - Create dashboards for appointment metrics

## References

1. [AWS Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
2. [AWS End User Messaging for WhatsApp](https://aws.amazon.com/end-user-messaging/whatsapp/)
3. [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
4. [Microsoft Graph API for Outlook](https://learn.microsoft.com/en-us/graph/api/resources/calendar?view=graph-rest-1.0)
