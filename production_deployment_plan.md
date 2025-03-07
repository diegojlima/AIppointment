# AIppointment Production Deployment Plan

This document outlines the detailed steps for deploying the AIppointment AWS Bedrock Agents architecture to production.

## Pre-Deployment Preparation

### 1. Verify Staging Deployment

- [ ] Ensure all functionality works correctly in the staging environment
- [ ] Verify AWS Bedrock Agent responds correctly to user queries
- [ ] Test appointment creation, rescheduling, and cancellation
- [ ] Validate WhatsApp integration with real messages
- [ ] Test calendar integration with both Google Calendar and Outlook

### 2. Set Up GitHub Variables and Secrets

- [ ] Set up the following GitHub variables in the repository settings:
  - `WHATSAPP_PHONE_NUMBER_ID`: The WhatsApp phone number ID for the Business API
  - Environment variables for different environments (dev, staging, prod)

- [ ] Set up the following GitHub secrets in the repository settings:
  - `AWS_ACCESS_KEY_ID`: AWS access key for Terraform deployment
  - `AWS_SECRET_ACCESS_KEY`: AWS secret key for Terraform deployment
  - `WHATSAPP_WEBHOOK_VERIFY_TOKEN`: Verification token for WhatsApp webhook

### 3. Back Up Existing Data

- [ ] Take a backup of the existing DynamoDB tables
- [ ] Verify backup integrity
- [ ] Store backup in a secure location

## Deployment Steps

### 1. Database Migration

- [ ] Run the data migration script in dry-run mode:
  ```bash
  python migrate_appointments_data.py --source-table AIppointment-appointments --target-table AIppointment-appointments-new --conversation-table AIppointment-conversation-history --dry-run
  ```

- [ ] Verify migration output for correctness
- [ ] Run the actual migration:
  ```bash
  python migrate_appointments_data.py --source-table AIppointment-appointments --target-table AIppointment-appointments-new --conversation-table AIppointment-conversation-history
  ```

### 2. Infrastructure Deployment

- [ ] Create a pull request to merge the `feature/bedrock-agent-infra` branch into `main`
- [ ] Review the GitHub Actions workflow execution
- [ ] Verify all tests pass
- [ ] Check the Terraform plan for any issues
- [ ] Approve the pull request to deploy to production

### 3. Environment Variable Storage

After deployment, the GitHub Actions workflow will set the following environment variables, which can be accessed in subsequent jobs:

- `BEDROCK_AGENT_ID`: The AWS Bedrock Agent ID
- `BEDROCK_AGENT_ALIAS_ID`: The AWS Bedrock Agent Alias ID
- `CONVERSATION_HISTORY_TABLE`: The DynamoDB table name for conversation history

Consider storing these values as GitHub variables for future deployments.

### 4. API Gateway Configuration

- [ ] The Terraform deployment will handle API Gateway configuration
- [ ] Verify API Gateway routes are correctly configured
- [ ] Test the API Gateway endpoints

### 5. Configure WhatsApp Integration

- [ ] Update WhatsApp Business account with new webhook URL (from API Gateway)
- [ ] Verify webhook with the verification token
- [ ] Test sending and receiving messages

## Post-Deployment Verification

### 1. Functional Testing

- [ ] Verify appointment creation works end-to-end
- [ ] Test appointment retrieval
- [ ] Test appointment rescheduling
- [ ] Test appointment cancellation
- [ ] Verify calendar integration

### 2. Performance Testing

- [ ] Test system performance under load
- [ ] Verify response times remain within acceptable limits
- [ ] Check DynamoDB throughput is adequate

### 3. Monitoring Setup

- [ ] Set up CloudWatch dashboards
- [ ] Configure alarms for critical metrics
- [ ] Set up logging for all components
- [ ] Configure error notifications

## Rollback Plan

In case of critical issues during deployment:

### 1. Infrastructure Rollback

- [ ] Revert the merge to `main` by creating a new pull request
- [ ] Manually revert the changes in AWS if necessary (update API Gateway routes, etc.)

### 2. Data Rollback

- [ ] If data migration caused issues, restore from backup
- [ ] Verify data integrity after restore

## Post-Deployment Tasks

- [ ] Update documentation
- [ ] Notify users of new capabilities
- [ ] Monitor system for any issues
- [ ] Schedule follow-up review session

## Deployment Schedule

- **Deployment Date**: [TBD]
- **Deployment Time**: [TBD] (Recommended: off-peak hours)
- **Expected Duration**: 2-3 hours
- **Deployment Team**: [List team members]
- **Emergency Contact**: [Name and contact information]
