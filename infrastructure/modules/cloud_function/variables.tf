# Updated infrastructure/modules/cloud_function/variables.tf

variable "function_name" {
  type        = string
  description = "The name of the Lambda function"
}

variable "description" {
  type        = string
  description = "Description of the Lambda function"
  default     = "Lambda function created by Terraform"
}

variable "handler" {
  type        = string
  description = "The handler for the Lambda function"
}

variable "runtime" {
  type        = string
  description = "The runtime for the Lambda function"
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

variable "publish" {
  type        = bool
  description = "Whether to publish creation/change as new Lambda function version"
  default     = false
}

variable "create_package" {
  type        = bool
  description = "Whether to create a Lambda package from source_path"
  default     = false
}

variable "source_path" {
  type        = string
  description = "The source directory containing the Lambda function code"
  default     = null
}

variable "lambda_zip_file" {
  type        = string
  description = "Path to a pre-packaged Lambda function zip file"
  default     = null
}

variable "environment_variables" {
  type        = map(string)
  description = "Environment variables for the Lambda function"
  default     = {}
}

variable "dynamodb_table_arn" {
  type        = string
  description = "The ARN of the DynamoDB table"
}

variable "api_gateway_id" {
  type        = string
  description = "The ID of the API Gateway"
  default     = null
}

variable "api_gateway_execution_arn" {
  type        = string
  description = "The execution ARN of the API Gateway"
  default     = null
}

variable "route_key" {
  type        = string
  description = "The route key for the API Gateway route"
  default     = null
}