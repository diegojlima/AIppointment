# Updated cloud_function module to use terraform-aws-lambda
# Infrastructure modules/cloud_function/main.tf

# Add a random string for uniqueness in resource names
resource "random_string" "policy_suffix" {
  length  = 8
  special = false
  upper   = false
}

module "lambda_function" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 5.0.0"

  function_name = var.function_name
  description   = var.description
  handler       = var.handler
  runtime       = var.runtime
  timeout       = var.timeout
  memory_size   = var.memory_size
  publish       = var.publish

  # Add unique suffix to policy names
  role_name         = "${var.function_name}-role-${random_string.policy_suffix.result}"

  # Source path or existing package options
  create_package         = var.create_package
  local_existing_package = var.lambda_zip_file
  source_path            = var.source_path
  artifacts_dir          = "${path.root}/.terraform/lambda_builds/"

  # Environment variables
  environment_variables = var.environment_variables

  # IAM role configuration
  create_role              = true
  attach_policy_statements = true
  policy_statements = {
    dynamodb = {
      effect = "Allow",
      actions = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      resources = [var.dynamodb_table_arn]
    },
    bedrock = {
      effect = "Allow",
      actions = [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels",
        "bedrock-runtime:Converse",
        "bedrock-runtime:ConverseStream"
      ],
      resources = ["*"]
    },
    logs = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["arn:aws:logs:*:*:*"]
    }
  }

  # Lambda permissions and API Gateway integration
  allowed_triggers = var.api_gateway_execution_arn != null ? {
    api_gateway = {
      service    = "apigateway"
      source_arn = "${var.api_gateway_execution_arn}/*/*"
    }
  } : {}

  tags = {
    Environment = "production"
    Terraform   = "true"
  }
}

# Only create API Gateway integration if needed
# Commented out due to planning issues with count
# resource "aws_apigatewayv2_integration" "lambda_integration" {
#   count              = var.api_gateway_id != null && var.route_key != null ? 1 : 0
#   api_id             = var.api_gateway_id
#   integration_type   = "AWS_PROXY"
#   integration_uri    = module.lambda_function.lambda_function_invoke_arn
#   integration_method = "POST"
# }

# resource "aws_apigatewayv2_route" "lambda_route" {
#   count     = var.api_gateway_id != null && var.route_key != null ? 1 : 0
#   api_id    = var.api_gateway_id
#   route_key = var.route_key
#   target    = "integrations/${aws_apigatewayv2_integration.lambda_integration[0].id}"
# }