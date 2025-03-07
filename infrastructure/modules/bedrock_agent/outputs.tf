# infrastructure/modules/bedrock_agent/outputs.tf

output "agent_id" {
  description = "The ID of the Bedrock Agent"
  value       = aws_bedrockagent_agent.appointment_agent.id
}

output "agent_alias_id" {
  description = "The ID of the Bedrock Agent Alias"
  value       = aws_bedrockagent_agent_alias.agent_alias.id
}

output "schema_bucket_name" {
  description = "The name of the S3 bucket containing the OpenAPI schema"
  value       = aws_s3_bucket.schema_bucket.bucket
}

output "schema_bucket_arn" {
  description = "The ARN of the S3 bucket containing the OpenAPI schema"
  value       = aws_s3_bucket.schema_bucket.arn
}

output "agent_role_arn" {
  description = "The ARN of the IAM role for the Bedrock Agent"
  value       = aws_iam_role.bedrock_agent_role.arn
}

output "agent_role_name" {
  description = "The name of the IAM role for the Bedrock Agent"
  value       = aws_iam_role.bedrock_agent_role.name
}