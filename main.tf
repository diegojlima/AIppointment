# main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "global_infra" {
  source = "./global-infra/terraform"
}

module "appointment_booking" {
  source = "./modules/cloud_function"
  function_name = "appointment_booking"
  handler       = "main.lambda_handler"
  runtime       = "python3.9"
  source_dir    = "${path.module}/functions/appointment-booking/src"
  environment_variables = {
    DYNAMODB_TABLE = module.global_infra.dynamodb_table_name
  }
  dynamodb_table_arn = module.global_infra.dynamodb_table_arn
  api_gateway_id = module.global_infra.api_gateway_id
  api_gateway_execution_arn = module.global_infra.api_gateway_execution_arn
  route_key = "POST /book"
}