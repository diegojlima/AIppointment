# Production environment configuration for AIppointment
environment = "production"
aws_region  = "us-west-2"

# WhatsApp integration
whatsapp_phone_number_id        = "{{ssm:/AIppointment/Production/WhatsAppPhoneNumberId}}"            # Retrieved from AWS Parameter Store
whatsapp_webhook_verify_token   = "{{ssm:/AIppointment/Production/WhatsAppWebhookVerificationToken}}" # Retrieved from AWS Parameter Store

# Bedrock Agent
foundation_model_id = "anthropic.claude-3-haiku-20240307-v1:0"

# DynamoDB configurations
dynamodb_billing_mode               = "PROVISIONED" # Use provisioned capacity for production
dynamodb_read_capacity              = 10
dynamodb_write_capacity             = 10
dynamodb_autoscaling_enabled        = true
dynamodb_autoscaling_min_read_capacity  = 5
dynamodb_autoscaling_max_read_capacity  = 50
dynamodb_autoscaling_min_write_capacity = 5
dynamodb_autoscaling_max_write_capacity = 50

# API Gateway configurations
api_gateway_stage_name              = "production"
api_gateway_logging_enabled         = true
api_gateway_throttling_rate_limit   = 1000
api_gateway_throttling_burst_limit  = 500

# Lambda configurations
lambda_memory_size             = 512
lambda_timeout                 = 30
lambda_reserved_concurrency    = 50
lambda_provisioned_concurrency = 5 # For critical functions