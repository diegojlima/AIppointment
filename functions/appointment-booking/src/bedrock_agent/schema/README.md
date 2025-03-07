# AWS Bedrock Agent Schema

This directory contains the OpenAPI schema for configuring the AWS Bedrock Agent for the AIppointment system.

## Files

- `agent_schema.json`: The OpenAPI schema for the Bedrock Agent API.

## Configuration Steps

1. Go to the AWS Bedrock console
2. Select "Agents" from the left sidebar
3. Click "Create Agent"
4. Configure the basic settings:
   - Name: AIppointment
   - Description: AI-powered appointment booking system
   - IAM Role: Choose a role with appropriate permissions
   - Choose Claude 3 as the foundation model
5. In the "API schema" section, select "Import from file" and upload `agent_schema.json`
6. Configure the Agent instructions with the following text:

```
You are an appointment scheduling assistant integrated with WhatsApp. 
Your primary job is to help users schedule, reschedule, and cancel appointments.

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

Use the available action groups to perform calendar operations and appointment management.
```

7. Add action groups:
   - AppointmentCreator: For creating new appointments
   - AppointmentManager: For managing existing appointments
   - CalendarIntegrator: For calendar system integration

8. For each action group, configure the Lambda function that implements the action group

9. Save and deploy the Agent

## Testing the Agent

You can test the Agent in the AWS console using the built-in test interface. Try the following test messages:

1. "I need a dental checkup next Tuesday at 2 PM"
2. "Show me my appointments for this week"
3. "Reschedule my appointment on Wednesday to 3 PM"
4. "Cancel my appointment on Thursday"

## Agent Session State

The Agent maintains session state between interactions, which includes:

- userId: The user's phone number or identifier
- calendarProvider: The preferred calendar provider (GOOGLE or OUTLOOK)
- conversationId: A unique identifier for the conversation
