# global-infra/terraform/variables.tf

variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "us-west-2"
}

# You can add more variables here if needed, for example:
# variable "lambda_timeout" {
#   description = "The timeout for the Lambda function in seconds"
#   type        = number
#   default     = 30
# }

# variable "lambda_memory_size" {
#   description = "The memory size for the Lambda function in MB"
#   type        = number
#   default     = 128
# }