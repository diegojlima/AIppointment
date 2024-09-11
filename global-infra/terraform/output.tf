# global-infra/terraform/output.tf

output "dynamodb_table_name" {
  value = aws_dynamodb_table.appointments.name
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.appointments.arn
}

output "api_gateway_id" {
  value = aws_apigatewayv2_api.appointment_api.id
}

output "api_gateway_execution_arn" {
  value = aws_apigatewayv2_api.appointment_api.execution_arn
}