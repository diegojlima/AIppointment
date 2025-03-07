# infrastructure/modules/bedrock_lambda/main.tf

resource "aws_lambda_function" "function" {
  filename         = var.lambda_zip_file
  source_code_hash = filebase64sha256(var.lambda_zip_file)
  function_name    = var.function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = var.handler
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = var.environment_variables
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy" "dynamodb_access" {
  name = "dynamodb_access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      Resource = var.dynamodb_table_arn
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_access" {
  name = "bedrock_access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels",
        "bedrock-runtime:InvokeModel",
        "bedrock-agent-runtime:InvokeAgent"
      ]
      Resource = "*"
    }]
  })
}

# Add additional policies for calendar integration
resource "aws_iam_role_policy" "calendar_access" {
  count = var.enable_calendar_integration ? 1 : 0
  name  = "calendar_access"
  role  = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = "*"
    }]
  })
}