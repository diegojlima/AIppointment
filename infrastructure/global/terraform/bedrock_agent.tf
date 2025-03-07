# infrastructure/global/terraform/bedrock_agent.tf

# Lambda function for appointment creator action group
module "appointment_creator_lambda" {
  source = "../../modules/cloud_function"

  function_name = "${local.project_name}-appointment-creator"
  handler       = "bedrock_agent.appointment_creator.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256
  
  # Use the specific zip file for this action group
  lambda_zip_file = "../../../functions/appointment-booking/appointment_creator_lambda.zip"
  
  environment_variables = {
    DYNAMODB_TABLE = aws_dynamodb_table.appointments.name
    LOG_LEVEL      = "INFO"
  }

  dynamodb_table_arn = aws_dynamodb_table.appointments.arn
}

# Lambda function for appointment manager action group
module "appointment_manager_lambda" {
  source = "../../modules/cloud_function"

  function_name = "${local.project_name}-appointment-manager"
  handler       = "bedrock_agent.appointment_manager.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256
  
  # Use the specific zip file for this action group
  lambda_zip_file = "../../../functions/appointment-booking/appointment_manager_lambda.zip"
  
  environment_variables = {
    DYNAMODB_TABLE = aws_dynamodb_table.appointments.name
    LOG_LEVEL      = "INFO"
  }

  dynamodb_table_arn = aws_dynamodb_table.appointments.arn
}

# Lambda function for calendar integrator action group
module "calendar_integrator_lambda" {
  source = "../../modules/cloud_function"

  function_name = "${local.project_name}-calendar-integrator"
  handler       = "bedrock_agent.calendar_integrator.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256
  
  # Use the specific zip file for this action group
  lambda_zip_file = "../../../functions/appointment-booking/calendar_integrator_lambda.zip"
  
  environment_variables = {
    DYNAMODB_TABLE              = aws_dynamodb_table.appointments.name
    LOG_LEVEL                   = "INFO"
    DEFAULT_CALENDAR_PROVIDER   = "GOOGLE"
    CALENDAR_CREDENTIALS_TABLE  = aws_dynamodb_table.calendar_credentials.name
  }

  dynamodb_table_arn = aws_dynamodb_table.appointments.arn
}

# DynamoDB table for calendar credentials
resource "aws_dynamodb_table" "calendar_credentials" {
  name           = "${local.project_name}-calendar-credentials"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "provider"
  range_key      = "userId"

  attribute {
    name = "provider"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  tags = {
    Environment = local.environment
    Project     = local.project_name
  }
}

# DynamoDB table for conversation history
resource "aws_dynamodb_table" "conversation_history" {
  name           = "${local.project_name}-conversation-history"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "conversationId"

  attribute {
    name = "conversationId"
    type = "S"
  }

  attribute {
    name = "senderId"
    type = "S"
  }

  global_secondary_index {
    name            = "SenderIdIndex"
    hash_key        = "senderId"
    projection_type = "ALL"
  }

  tags = {
    Environment = local.environment
    Project     = local.project_name
  }
}

# DynamoDB table for conversation messages
resource "aws_dynamodb_table" "conversation_messages" {
  name           = "${local.project_name}-conversation-messages"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "messageId"
  range_key      = "conversationId"

  attribute {
    name = "messageId"
    type = "S"
  }

  attribute {
    name = "conversationId"
    type = "S"
  }

  tags = {
    Environment = local.environment
    Project     = local.project_name
  }
}

# Bedrock Agent for appointment booking
module "bedrock_agent" {
  source = "../../modules/bedrock_agent"

  project_name  = local.project_name
  environment   = local.environment
  
  # Path to the OpenAPI schema
  schema_path   = "../../../functions/appointment-booking/src/bedrock_agent/schema/agent_schema.json"
  
  # Claude 3 Haiku model
  foundation_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
  
  # Customize the agent instruction if needed
  agent_instruction = <<-EOT
    You are an appointment scheduling assistant integrated with WhatsApp. 
    Your primary job is to help users schedule, reschedule, and cancel appointments.
    
    Key tasks you can perform:
    1. Check availability for a specific date
    2. Create new appointments
    3. View existing appointments
    4. Reschedule appointments
    5. Cancel appointments
    
    When talking to users:
    - Be friendly and conversational
    - Ask for clarification when needed
    - Confirm details before making changes
    - Offer alternative time slots if requested times are unavailable
    - Send confirmation messages with appointment details
    
    Available time slots are hourly from 9 AM to 5 PM, Monday through Friday.
    Appointments are 1 hour by default unless specified otherwise.
    
    Use the available action groups to perform calendar operations and appointment management.
  EOT
  
  # Lambda function ARNs for the action groups
  appointment_creator_lambda_arn = module.appointment_creator_lambda.function_arn
  appointment_manager_lambda_arn = module.appointment_manager_lambda.function_arn
  calendar_integrator_lambda_arn = module.calendar_integrator_lambda.function_arn
  
  lambda_function_arns = [
    module.appointment_creator_lambda.function_arn,
    module.appointment_manager_lambda.function_arn,
    module.calendar_integrator_lambda.function_arn
  ]
}