# AWS Credentials and Environment Variables Handling

This document explains how AWS credentials and environment variables are handled in the AIppointment project.

## Overview

The AIppointment project follows best practices for handling AWS credentials and environment variables. It uses:

1. **GitHub Actions Secrets** for sensitive information like AWS credentials
2. **GitHub Variables** for non-sensitive configuration
3. **Environment-specific variables** for different deployment environments (dev, staging, prod)
4. **Mock credentials for tests** to prevent accidental AWS calls during testing

## CI/CD Pipeline Configuration

The GitHub Actions workflow (`/.github/workflows/appointment-booking-bedrock.yml`) is configured to:

1. Use mock AWS credentials during testing to prevent real AWS calls
2. Use GitHub secrets for AWS credentials during deployment
3. Pass environment variables to the tests to provide the necessary context

### Testing Environment

For tests, the following mock environment variables are set:

```yaml
env:
  # Testing environment variables
  AWS_REGION: us-west-2
  BEDROCK_AGENT_ID: test-agent-id
  BEDROCK_AGENT_ALIAS_ID: test-agent-alias-id
  DYNAMODB_TABLE: test-appointments
  CONVERSATION_HISTORY_TABLE: test-conversation-history
  WHATSAPP_WEBHOOK_VERIFY_TOKEN: test-webhook-token
  # Set mock AWS credentials for tests to prevent real AWS calls
  AWS_ACCESS_KEY_ID: test-access-key
  AWS_SECRET_ACCESS_KEY: test-secret-key
  # Disable boto3 loading credentials from ~/.aws/credentials
  AWS_CONFIG_FILE: /dev/null
  AWS_SHARED_CREDENTIALS_FILE: /dev/null
```

These values are used only during the test job and prevent any real AWS calls.

### Deployment Environment

For deployment, the workflow uses:

1. AWS credentials from GitHub secrets via the `aws-actions/configure-aws-credentials` action
2. Environment-specific variables based on the branch (dev, staging, prod)

## Local Development

For local development:

1. Configure your AWS credentials using the AWS CLI (`aws configure`)
2. Use environment variables for local testing:

```bash
# For testing with mock credentials
export AWS_REGION=us-west-2
export BEDROCK_AGENT_ID=test-agent-id
export BEDROCK_AGENT_ALIAS_ID=test-agent-alias-id
export DYNAMODB_TABLE=test-appointments
export CONVERSATION_HISTORY_TABLE=test-conversation-history
export WHATSAPP_WEBHOOK_VERIFY_TOKEN=test-webhook-token

# Run tests with moto to mock AWS services
python -m pytest functions/appointment-booking/tests/
```

## Avoiding Accidental AWS Calls

To avoid accidental AWS calls using your job credentials during local development:

1. Always use the mock credentials for testing
2. Use the Moto library to mock AWS services during tests
3. Set up a separate AWS profile for this project, if necessary

You can set up a separate AWS profile using:

```bash
aws configure --profile aippointment
```

And then use it for this project:

```bash
export AWS_PROFILE=aippointment
```

## Terraform State Management

Terraform state is managed in an S3 bucket, which requires AWS credentials with the appropriate permissions. To avoid using your job credentials for Terraform operations:

1. Create a separate AWS profile for Terraform operations
2. Use the `--var-file` flag to specify environment-specific variables
3. Run Terraform commands with the correct profile:

```bash
AWS_PROFILE=aippointment terraform apply -var-file=staging.tfvars
```

## GitHub Actions Configuration

The repository should have the following GitHub secrets and variables configured:

### Secrets (sensitive)

- `AWS_ACCESS_KEY_ID`: AWS access key for Terraform deployment
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for Terraform deployment
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`: Verification token for WhatsApp webhook

### Variables (non-sensitive)

- `WHATSAPP_PHONE_NUMBER_ID`: WhatsApp phone number ID for the Business API

See the `GITHUB_VARIABLES_SETUP.md` file for detailed instructions on setting up these variables.
