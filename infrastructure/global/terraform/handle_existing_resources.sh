#!/bin/bash
# Script to handle resources that already exist
# This creates the necessary Terraform state entries for resources that already exist

echo "Checking for existing resources..."

# Function to check if a resource exists (simplistic approach)
resource_exists() {
  terraform state list | grep -q "$1"
  return $?
}

# Import DynamoDB tables if they exist
for table in "appointment-system-calendar-credentials" "appointment-system-conversation-history" "appointment-system-conversation-messages" "appointment-system-appointments" "terraform-state-lock"; do
  if ! resource_exists "aws_dynamodb_table"; then
    echo "Importing DynamoDB table: $table"
    # Identify the correct resource address for this table
    if [[ "$table" == "appointment-system-calendar-credentials" ]]; then
      terraform import aws_dynamodb_table.calendar_credentials $table || true
    elif [[ "$table" == "appointment-system-conversation-history" ]]; then
      terraform import aws_dynamodb_table.conversation_history $table || true
    elif [[ "$table" == "appointment-system-conversation-messages" ]]; then
      terraform import aws_dynamodb_table.conversation_messages $table || true
    elif [[ "$table" == "appointment-system-appointments" ]]; then
      terraform import aws_dynamodb_table.appointments $table || true
    else
      terraform import aws_dynamodb_table.terraform_state_lock $table || true
    fi
  fi
done

# Import S3 buckets if they exist
for bucket in "delima-aippointment-terraform-state" "appointment-system-bedrock-schema-dev"; do
  if ! resource_exists "aws_s3_bucket"; then
    echo "Importing S3 bucket: $bucket"
    if [[ "$bucket" == "delima-aippointment-terraform-state" ]]; then
      terraform import aws_s3_bucket.terraform_state $bucket || true
    else
      terraform import module.bedrock_agent.aws_s3_bucket.schema_bucket $bucket || true
    fi
  fi
done

# Import CloudWatch Log Groups if they exist
for log_group in "/aws/lambda/appointment-system-booking" "/aws/lambda/appointment-system-appointment-creator" "/aws/lambda/appointment-system-appointment-manager" "/aws/lambda/appointment-system-calendar-integrator"; do
  if ! resource_exists "aws_cloudwatch_log_group"; then
    echo "Importing CloudWatch Log Group: $log_group"
    if [[ "$log_group" == "/aws/lambda/appointment-system-booking" ]]; then
      terraform import module.appointment_booking_lambda.module.lambda_function.aws_cloudwatch_log_group.lambda[0] $log_group || true
    elif [[ "$log_group" == "/aws/lambda/appointment-system-appointment-creator" ]]; then
      terraform import module.appointment_creator_lambda.module.lambda_function.aws_cloudwatch_log_group.lambda[0] $log_group || true
    elif [[ "$log_group" == "/aws/lambda/appointment-system-appointment-manager" ]]; then
      terraform import module.appointment_manager_lambda.module.lambda_function.aws_cloudwatch_log_group.lambda[0] $log_group || true
    else
      terraform import module.calendar_integrator_lambda.module.lambda_function.aws_cloudwatch_log_group.lambda[0] $log_group || true
    fi
  fi
done

# Import IAM Role if it exists
if ! resource_exists "aws_iam_role"; then
  echo "Importing IAM Role: appointment-system-bedrock-agent-role-dev"
  terraform import module.bedrock_agent.aws_iam_role.bedrock_agent_role appointment-system-bedrock-agent-role-dev || true
fi

echo "Import completed"
