# AIppointment CDK Infrastructure

This directory contains the AWS CDK implementation of the infrastructure for the AIppointment project, migrated from Terraform.

## Infrastructure Components

The CDK implementation includes the following AWS resources:

- **DynamoDB Tables**:
  - Appointments Table
  - Calendar Credentials Table
  - Conversation History Table
  - Conversation Messages Table

- **API Gateway**:
  - HTTP API for booking appointments
  - WhatsApp webhook endpoints

- **Lambda Functions**:
  - Main Lambda function for handling requests
  - Specialized Lambda functions for Bedrock Agent action groups:
    - AppointmentCreator
    - AppointmentManager
    - CalendarIntegrator

- **Bedrock Agent**:
  - Custom resource implementation for Bedrock Agent
  - Action Groups with API schema
  - Agent Alias

- **S3 Bucket**:
  - Storage for OpenAPI schema

## Migration from Terraform

This implementation is a direct migration from the original Terraform infrastructure, with the following changes:

1. Switched from Terraform modules to CDK constructs
2. Implemented Bedrock Agent resources using a custom resource (since there's no native L2 construct yet)
3. Maintained the same resource naming and configuration

## Prerequisites

- Python 3.8 or higher
- AWS CDK CLI
- AWS Account with Bedrock access

## Setup Instructions

1. Create a virtual environment:
```
$ python3 -m venv .venv
```

2. Activate the virtual environment:
```
$ source .venv/bin/activate
```

3. Install requirements:
```
$ pip install -r requirements.txt
```

4. Bootstrap CDK in your AWS account (if not already done):
```
$ cdk bootstrap
```

5. Deploy the infrastructure:
```
$ cdk deploy
```

## Migration Notes

### Custom Resources

Due to the lack of L2 constructs for Amazon Bedrock Agents at the time of migration, we've implemented a custom resource provider Lambda function to create and manage the Bedrock Agent. This approach allows us to mirror the functionality provided by the Terraform AWS provider.

### Bedrock Agent Schema

The OpenAPI schema for the Bedrock Agent is stored in an S3 bucket, just like in the original Terraform implementation. The schema file is uploaded from the local filesystem to the S3 bucket during deployment.

### Lambda Functions

The Lambda functions are created directly from the source code in the `functions/appointment-booking/src` directory, rather than using pre-packaged ZIP files. This simplifies the build process but requires that the source code be available during deployment.

## Future Improvements

1. Replace the custom resource implementation with native CDK constructs once they become available
2. Add infrastructure for WhatsApp integration with AWS End User Messaging
3. Implement CI/CD pipeline for automated deployment
4. Add cross-stack references for better modularity
5. Implement environment-specific configurations (dev, staging, prod)
