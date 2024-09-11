# shared/terraform-modules/cloud_function/variables.tf

variable "function_name" {
  type = string
}

variable "handler" {
  type = string
}

variable "runtime" {
  type = string
}

variable "source_dir" {
  type = string
}

variable "environment_variables" {
  type = map(string)
}

variable "dynamodb_table_arn" {
  type = string
}

variable "api_gateway_id" {
  type = string
}

variable "api_gateway_execution_arn" {
  type = string
}

variable "route_key" {
  type = string
}