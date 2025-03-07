# infrastructure/modules/bedrock_lambda/variables.tf

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "lambda_zip_file" {
  description = "Path to the Lambda function zip file"
  type        = string
}

variable "handler" {
  description = "Handler for the Lambda function"
  type        = string
}

variable "runtime" {
  description = "Runtime for the Lambda function"
  type        = string
  default     = "python3.12"
}

variable "timeout" {
  description = "Timeout for the Lambda function (in seconds)"
  type        = number
  default     = 30
}

variable "memory_size" {
  description = "Memory size for the Lambda function (in MB)"
  type        = number
  default     = 256
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table that the Lambda function interacts with"
  type        = string
}

variable "enable_calendar_integration" {
  description = "Whether to enable calendar integration policies"
  type        = bool
  default     = false
}