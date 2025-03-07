# infrastructure/modules/bedrock_agent/variables.tf

variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "aippointment"
}

variable "environment" {
  description = "The deployment environment (e.g. dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "schema_path" {
  description = "The path to the OpenAPI schema file"
  type        = string
  default     = "../../../functions/appointment-booking/src/bedrock_agent/schema/agent_schema.json"
}

variable "foundation_model_id" {
  description = "The ARN of the foundation model to use for the agent"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "agent_instruction" {
  description = "The instruction for the Bedrock Agent"
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

variable "appointment_creator_lambda_arn" {
  description = "The ARN of the appointment creator Lambda function"
  type        = string
}

variable "appointment_manager_lambda_arn" {
  description = "The ARN of the appointment manager Lambda function"
  type        = string
}

variable "calendar_integrator_lambda_arn" {
  description = "The ARN of the calendar integrator Lambda function"
  type        = string
}

variable "lambda_function_arns" {
  description = "List of Lambda function ARNs that the Bedrock Agent can invoke"
  type        = list(string)
}