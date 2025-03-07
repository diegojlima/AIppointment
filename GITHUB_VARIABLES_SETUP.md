# Setting Up GitHub Variables and Secrets for AIppointment

This document describes how to set up the necessary GitHub variables and secrets for the AIppointment project.

## Overview

The AIppointment project uses GitHub Actions for CI/CD and relies on GitHub variables and secrets to store sensitive information and configuration values. This approach avoids hardcoding sensitive data in the repository and allows for different configurations across environments.

## GitHub Variables

GitHub variables are used for non-sensitive configuration values. They are visible in logs and can be used across workflows.

### Required Variables

1. `WHATSAPP_PHONE_NUMBER_ID`
   - Description: The WhatsApp phone number ID for the Business API
   - Example: `123456789012345`

2. `PROJECT_NAME` (optional - defaults to "aippointment")
   - Description: The name of the project used for resource naming
   - Example: `aippointment`

### Environment-Specific Variables

You can also create environment-specific variables for different deployment environments (dev, staging, prod).

## GitHub Secrets

GitHub secrets are used for sensitive information. They are encrypted and only exposed to GitHub Actions during workflow runs.

### Required Secrets

1. `AWS_ACCESS_KEY_ID`
   - Description: AWS access key for Terraform deployment
   - Example: `AKIA...`

2. `AWS_SECRET_ACCESS_KEY`
   - Description: AWS secret key for Terraform deployment
   - Example: `wJa...`

3. `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
   - Description: Verification token for WhatsApp webhook
   - Example: `some-random-string-here`

## Setting Up Variables and Secrets

### Repository Variables

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Select the "Variables" tab
4. Click on "New repository variable"
5. Enter the name and value of the variable
6. Click "Add variable"

### Repository Secrets

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Select the "Secrets" tab
4. Click on "New repository secret"
5. Enter the name and value of the secret
6. Click "Add secret"

### Environment Variables and Secrets

If you want to use different values for different environments:

1. Go to your GitHub repository
2. Click on "Settings" > "Environments"
3. Click "New environment" and name it (e.g., "staging", "production")
4. Click on the environment name
5. Add environment secrets and variables as needed
6. Configure environment protection rules if necessary

## Using Variables and Secrets in Workflows

Variables are referenced in workflows using the following syntax:
```yaml
${{ vars.VARIABLE_NAME }}
```

Secrets are referenced in workflows using the following syntax:
```yaml
${{ secrets.SECRET_NAME }}
```

Environment-specific variables and secrets are only available when the workflow is configured to use that environment:
```yaml
jobs:
  deploy:
    environment: production
    runs-on: ubuntu-latest
    steps:
      - name: Use environment-specific variables
        run: echo "Using ${{ vars.ENVIRONMENT_SPECIFIC_VARIABLE }}"
```

## Recommended Variable and Secret Values

### Development Environment

- `WHATSAPP_PHONE_NUMBER_ID`: Your development WhatsApp phone number ID
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`: A simple token for development (e.g., `dev-token`)

### Staging Environment

- `WHATSAPP_PHONE_NUMBER_ID`: Your staging WhatsApp phone number ID
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`: A more complex token for staging (e.g., `staging-token-2023`)

### Production Environment

- `WHATSAPP_PHONE_NUMBER_ID`: Your production WhatsApp phone number ID
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`: A strong, randomly generated token (e.g., `prod-token-a1b2c3d4e5f6`)

## Security Considerations

- **Never** commit sensitive information directly to the repository
- Rotate AWS credentials and webhook tokens periodically
- Use different values for different environments
- Restrict access to GitHub secrets to authorized team members only
