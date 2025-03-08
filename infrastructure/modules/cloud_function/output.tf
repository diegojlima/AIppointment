# Updated infrastructure/modules/cloud_function/output.tf

output "function_name" {
  value       = module.lambda_function.lambda_function_name
  description = "The name of the Lambda function"
}

output "function_arn" {
  value       = module.lambda_function.lambda_function_arn
  description = "The ARN of the Lambda function"
}

output "invoke_arn" {
  value       = module.lambda_function.lambda_function_invoke_arn
  description = "The invoke ARN of the Lambda function"
}

output "function_role_name" {
  value       = module.lambda_function.lambda_role_name
  description = "The name of the IAM role attached to the Lambda function"
}

output "function_role_arn" {
  value       = module.lambda_function.lambda_role_arn
  description = "The ARN of the IAM role attached to the Lambda function"
}