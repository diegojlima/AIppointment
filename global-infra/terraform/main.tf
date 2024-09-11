# global-infra/terraform/main.tf

resource "aws_dynamodb_table" "appointments" {
  name           = "${local.project_name}-appointments"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PhoneNumber"
  range_key      = "AppointmentDateTime"

  attribute {
    name = "PhoneNumber"
    type = "S"
  }

  attribute {
    name = "AppointmentDateTime"
    type = "S"
  }

  tags = {
    Environment = local.environment
    Project     = local.project_name
  }
}

resource "aws_apigatewayv2_api" "appointment_api" {
  name          = "${local.project_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "appointment_api" {
  api_id = aws_apigatewayv2_api.appointment_api.id
  name   = local.environment
  auto_deploy = true
}