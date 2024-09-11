# shared/terraform-modules/cloud_function/output.tf

output "function_name" {
  value       = aws_lambda_function.function.function_name
  description = "The name of the Lambda function"
}

output "function_arn" {
  value       = aws_lambda_function.function.arn
  description = "The ARN of the Lambda function"
}

output "invoke_arn" {
  value       = aws_lambda_function.function.invoke_arn
  description = "The invoke ARN of the Lambda function"
}

output "function_role_name" {
  value       = aws_iam_role.lambda_role.name
  description = "The name of the IAM role attached to the Lambda function"
}

output "function_role_arn" {
  value       = aws_iam_role.lambda_role.arn
  description = "The ARN of the IAM role attached to the Lambda function"
}