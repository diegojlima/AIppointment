# infrastructure/modules/bedrock_lambda/outputs.tf

output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.function.function_name
}

output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.function.arn
}

output "function_invoke_arn" {
  description = "Invoke ARN of the Lambda function"
  value       = aws_lambda_function.function.invoke_arn
}

output "role_name" {
  description = "Name of the IAM role for the Lambda function"
  value       = aws_iam_role.lambda_role.name
}

output "role_arn" {
  description = "ARN of the IAM role for the Lambda function"
  value       = aws_iam_role.lambda_role.arn
}