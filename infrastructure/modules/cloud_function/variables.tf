# shared/terraform-modules/cloud_function/variables.tf

variable "function_name" {
  type        = string
  description = "The name of the Lambda function"
}

variable "handler" {
  type        = string
  description = "The handler for the Lambda function"
}

variable "runtime" {
  type        = string
  description = "The runtime for the Lambda function"
}

variable "source_dir" {
  type        = string
  description = "The source directory containing the Lambda function code"
}

variable "environment_variables" {
  type        = map(string)
  description = "Environment variables for the Lambda function"
  default     = {}
}

variable "timeout" {
  type        = number
  description = "The timeout for the Lambda function in seconds"
  default     = 30
}

variable "memory_size" {
  type        = number
  description = "The memory size for the Lambda function in MB"
  default     = 128
}

variable "dynamodb_table_arn" {
  type        = string
  description = "The ARN of the DynamoDB table"
}

variable "api_gateway_id" {
  type        = string
  description = "The ID of the API Gateway"
}

variable "api_gateway_execution_arn" {
  type        = string
  description = "The execution ARN of the API Gateway"
}

variable "route_key" {
  type        = string
  description = "The route key for the API Gateway route"
}