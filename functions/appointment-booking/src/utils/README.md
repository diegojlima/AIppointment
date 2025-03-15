# Google Calendar Integration Utilities

This directory contains utility functions for Google Calendar integration using environment variables.

## Environment Variable Setup

Instead of storing the Google service account credentials in AWS Parameter Store or Secrets Manager, this implementation uses environment variables directly in the Lambda configuration.

### Required Environment Variables

Add these environment variables directly to your Lambda function configuration in AWS:

```
# Google Calendar Service Account Credentials
GOOGLE_CALENDAR_TYPE=service_account
GOOGLE_CALENDAR_PROJECT_ID=your-project-id
GOOGLE_CALENDAR_PRIVATE_KEY_ID=your-private-key-id
GOOGLE_CALENDAR_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nYour private key with \n for line breaks\n-----END PRIVATE KEY-----\n
GOOGLE_CALENDAR_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
GOOGLE_CALENDAR_CLIENT_ID=your-client-id
GOOGLE_CALENDAR_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GOOGLE_CALENDAR_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_CALENDAR_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GOOGLE_CALENDAR_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com
GOOGLE_CALENDAR_UNIVERSE_DOMAIN=googleapis.com

# Optional: Calendar ID (default is 'primary')
# GOOGLE_CALENDAR_ID=primary
```

### Deployment

For deployment, set the environment variables in your Lambda function configuration either through the AWS Console or using infrastructure as code (Terraform).

## Utility Functions

### `google_credentials.py`

This utility reconstructs the Google service account credentials dictionary from environment variables. The returned dictionary can be used with the Google API client for authentication.

## Security Considerations

1. Never commit the `.env` file to version control
2. Add `.env` to your `.gitignore` file
3. For production deployments, set environment variables securely through your deployment platform
