# Global infrastructure variables

variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "The environment to deploy to (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "aippointment"
}

# WhatsApp integration variables
variable "whatsapp_phone_number_id" {
  description = "WhatsApp phone number ID for the Business API"
  type        = string
  default     = ""
}

variable "whatsapp_webhook_verify_token" {
  description = "Verification token for WhatsApp webhook"
  type        = string
  default     = ""
  sensitive   = true
}

# Bedrock Agent variables
variable "foundation_model_id" {
  description = "ID of the foundation model to use for the Bedrock Agent"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "agent_instruction" {
  description = "Instruction for the Bedrock Agent"
  type        = string
  default     = <<-EOT
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
}

# DynamoDB variables
variable "dynamodb_billing_mode" {
  description = "Billing mode for DynamoDB tables (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_read_capacity" {
  description = "Read capacity units for DynamoDB tables (only used with PROVISIONED billing mode)"
  type        = number
  default     = 5
}

variable "dynamodb_write_capacity" {
  description = "Write capacity units for DynamoDB tables (only used with PROVISIONED billing mode)"
  type        = number
  default     = 5
}

# API Gateway variables
variable "api_gateway_stage_name" {
  description = "Name of the API Gateway stage"
  type        = string
  default     = "dev"
}

variable "api_gateway_logging_enabled" {
  description = "Whether to enable logging for the API Gateway"
  type        = bool
  default     = true
}

# Lambda variables
variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 30
}
