#!/bin/bash
# Script to import existing AWS resources into Terraform state

cd infrastructure/global/terraform

echo "Importing DynamoDB tables..."
terraform import aws_dynamodb_table.calendar_credentials appointment-system-calendar-credentials
terraform import aws_dynamodb_table.conversation_history appointment-system-conversation-history
terraform import aws_dynamodb_table.conversation_messages appointment-system-conversation-messages
terraform import aws_dynamodb_table.appointments appointment-system-appointments
terraform import aws_dynamodb_table.terraform_state_lock terraform-state-lock

echo "Importing S3 buckets..."
terraform import aws_s3_bucket.terraform_state delima-aippointment-terraform-state
terraform import module.bedrock_agent.aws_s3_bucket.schema_bucket appointment-system-bedrock-schema-dev

echo "Importing IAM role..."
terraform import module.bedrock_agent.aws_iam_role.bedrock_agent_role appointment-system-bedrock-agent-role-dev

echo "Importing CloudWatch Log Groups..."
terraform import module.appointment_booking_lambda.module.lambda_function.aws_cloudwatch_log_group.lambda[0] /aws/lambda/appointment-system-booking
terraform import module.appointment_creator_lambda.module.lambda_function.aws_cloudwatch_log_group.lambda[0] /aws/lambda/appointment-system-appointment-creator
terraform import module.appointment_manager_lambda.module.lambda_function.aws_cloudwatch_log_group.lambda[0] /aws/lambda/appointment-system-appointment-manager
terraform import module.calendar_integrator_lambda.module.lambda_function.aws_cloudwatch_log_group.lambda[0] /aws/lambda/appointment-system-calendar-integrator

echo "Resources imported into Terraform state"
