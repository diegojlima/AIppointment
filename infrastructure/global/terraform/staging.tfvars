# Staging environment configuration for AIppointment
environment = "staging"
aws_region = "us-west-2"

# WhatsApp integration
whatsapp_phone_number_id = "your-whatsapp-phone-number-id" # Replace with actual value in AWS Parameter Store
whatsapp_webhook_verify_token = "staging-verification-token" # Replace with actual value in AWS Parameter Store

# Bedrock Agent
foundation_model_id = "anthropic.claude-3-haiku-20240307-v1:0"

# DynamoDB configurations
dynamodb_billing_mode = "PAY_PER_REQUEST" # Use on-demand capacity for staging

# API Gateway configurations
api_gateway_stage_name = "staging"

# Lambda configurations
lambda_memory_size = 256
lambda_timeout = 30
