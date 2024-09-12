# global-infra/terraform/main.tf

provider "aws" {
  region = var.aws_region
}

resource "aws_dynamodb_table" "appointments" {
  name           = "${local.project_name}-appointments"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PhoneNumber"
  range_key      = "CreatedAt"  # Changed from AppointmentDateTime to match Lambda function

  attribute {
    name = "PhoneNumber"
    type = "S"
  }

  attribute {
    name = "CreatedAt"
    type = "S"
  }

  tags = {
    Environment = local.environment
    Project     = local.project_name
  }
}
resource "aws_dynamodb_table" "terraform_state_lock" {
  name           = "terraform-state-lock"
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "Terraform State Lock Table"
  }
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "delima-appointment-state-tf"
  tags = {
    Name = "Terraform State Bucket"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state_versioning" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_apigatewayv2_api" "appointment_api" {
  name          = "${local.project_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "appointment_api" {
  api_id      = aws_apigatewayv2_api.appointment_api.id
  name        = local.environment
  auto_deploy = true
}

module "appointment_booking_lambda" {
  source = "../../modules/cloud_function"

  function_name    = "${local.project_name}-booking"
  handler          = "main.lambda_handler"
  runtime          = "python3.9"
  source_dir       = "../../functions/appointment-booking/src"
  
  environment_variables = {
    DYNAMODB_TABLE = aws_dynamodb_table.appointments.name
  }

  dynamodb_table_arn        = aws_dynamodb_table.appointments.arn
  api_gateway_id            = aws_apigatewayv2_api.appointment_api.id
  api_gateway_execution_arn = aws_apigatewayv2_api.appointment_api.execution_arn
  route_key                 = "POST /book-appointment"

  # Add these if you want to override the defaults in the module
  # timeout     = 30
  # memory_size = 128
}