# infrastructure/global/terraform/bedrock_agent_outputs.tf

output "bedrock_agent_id" {
  description = "The ID of the Bedrock Agent"
  value       = module.bedrock_agent.agent_id
}

output "bedrock_agent_alias_id" {
  description = "The ID of the Bedrock Agent Alias"
  value       = module.bedrock_agent.agent_alias_id
}

output "appointment_creator_lambda_arn" {
  description = "The ARN of the appointment creator Lambda function"
  value       = module.appointment_creator_lambda.function_arn
}

output "appointment_manager_lambda_arn" {
  description = "The ARN of the appointment manager Lambda function"
  value       = module.appointment_manager_lambda.function_arn
}

output "calendar_integrator_lambda_arn" {
  description = "The ARN of the calendar integrator Lambda function"
  value       = module.calendar_integrator_lambda.function_arn
}

output "conversation_history_table_name" {
  description = "The name of the DynamoDB table for conversation history"
  value       = aws_dynamodb_table.conversation_history.name
}

output "conversation_messages_table_name" {
  description = "The name of the DynamoDB table for conversation messages"
  value       = aws_dynamodb_table.conversation_messages.name
}

output "calendar_credentials_table_name" {
  description = "The name of the DynamoDB table for calendar credentials"
  value       = aws_dynamodb_table.calendar_credentials.name
}