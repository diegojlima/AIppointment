# AIppointment

An AI-powered appointment booking system that integrates with messaging platforms like WhatsApp Business to provide natural language appointment scheduling.

## Overview

AIppointment acts as an intelligent assistant that enables users to book appointments through conversational interfaces. The system uses natural language processing to extract appointment details from user messages, validates the requested times, and manages the appointment booking process.

### Key Features

- **Natural Language Understanding**: Extract appointment details from free-form text using Claude 3 on AWS Bedrock
- **Multi-channel Support**: Architecture designed for WhatsApp Business and other messaging platforms
- **Intelligent Conversation**: AWS Bedrock Agents for natural conversation flows
  - Appointment booking and validation
  - Conflict resolution for scheduling conflicts
  - Disambiguation of unclear inputs
  - Rescheduling and cancellation workflows
  - Appointment lookup and reminders
- **Modular Action Groups**: Specialized handlers for different functionality domains
  - AppointmentCreator for booking new appointments
  - AppointmentManager for handling existing appointments
  - CalendarIntegrator for calendar system integration
- **WhatsApp Business Integration**: Direct connection to WhatsApp Business API
- **Intent Classification**: Route messages based on detected user intent
- **Calendar Integration**: Connects with Google Calendar and Microsoft Outlook
  - Real-time availability checking
  - Appointment booking in external calendars
  - Conflict detection and resolution

## System Architecture

The system follows a serverless architecture pattern built on AWS services:

- **AWS Lambda**: Core processing logic
- **Amazon API Gateway**: RESTful API endpoint
- **AWS Bedrock (Claude 3)**: Natural language understanding
- **Amazon DynamoDB**: Appointment data storage
- **Terraform & AWS SAM**: Infrastructure as code
- **GitHub Actions**: CI/CD pipeline

### Component Overview

1. **Input Adapter**: Normalizes inputs from various channels
2. **AWS Bedrock Agent**: Manages conversation flow and understands user intents
3. **Action Groups**: Specialized handlers for different appointment operations
4. **Calendar Integration**: Connects with external calendar systems (Google, Outlook)
5. **WhatsApp Integration**: Direct integration with WhatsApp via AWS End User Messaging
6. **DynamoDB Storage**: Persistent storage for appointments and conversation history

## Getting Started

### Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured locally
- Python 3.12+
- Terraform
- Git

### Local Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AIppointment.git
   cd AIppointment
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

4. Run tests:
   ```
   pytest
   ```

### Deployment

#### Manual Deployment

1. Package the Lambda function:
   ```
   cd functions/appointment-booking
   ./build_lambda.sh
   ```

2. Deploy using Terraform:
   ```
   cd infrastructure/global/terraform
   terraform init
   terraform apply
   ```

#### CI/CD Pipeline

The project includes a GitHub Actions workflow that automatically deploys changes when code is pushed to the main branch (requires setup):

1. Code is pushed to the main branch
2. GitHub Actions workflow is triggered
3. Lambda function is packaged
4. Terraform applies infrastructure changes
5. New version is deployed to AWS

## API Documentation

### Endpoint: `/book-appointment`

**Method**: POST

**Request Body**:
```json
{
  "phone_number": "+1234567890",
  "message": "I need an appointment tomorrow at 2pm for a checkup",
  "channel": "whatsapp",
  "session_id": "ABC123"
}
```

**Response**:
```json
{
  "message": "Appointment request processed successfully",
  "details": {
    "date": "2023-09-18",
    "time": "14:00",
    "purpose": "checkup"
  },
  "is_valid": true,
  "calendar": {
    "synced": true,
    "provider": "google",
    "event_id": "abc123xyz",
    "event_link": "https://calendar.google.com/calendar/event?id=abc123xyz"
  }
}
```

## Project Roadmap

- [x] Core appointment extraction and booking
- [x] AWS infrastructure setup
- [x] AWS Bedrock Agents integration
- [x] WhatsApp Business API integration
- [x] Well-defined OpenAPI schema for agent understanding
- [x] Calendar system integration (Google Calendar, Outlook)
- [x] Robust integration testing for end-to-end flows
- [x] Abstract interfaces for calendar service providers
- [ ] Appointment reminders and notifications
- [ ] Enhanced error handling and recovery
- [ ] Multi-language support
- [ ] User management system

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.