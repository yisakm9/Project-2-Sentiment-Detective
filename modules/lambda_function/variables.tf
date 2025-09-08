# modules/lambda_function/variables.tf

variable "function_name" {
  description = "The name of the Lambda function."
  type        = string
  default     = "sentiment-detective-analyzer"
}

variable "iam_role_arn" {
  description = "The ARN of the IAM role for the Lambda function."
  type        = string
}

variable "runtime" {
  description = "The runtime environment for the Lambda function."
  type        = string
  default     = "python3.11"
}

variable "handler" {
  description = "The function entrypoint in your code."
  type        = string
  default     = "lambda_function.lambda_handler"
}

variable "timeout" {
  description = "The timeout for the Lambda function in seconds."
  type        = number
  default     = 60
}

variable "zip_file_path" {
  description = "The local path to the Lambda function's deployment package (zip file)."
  type        = string
}

variable "environment_variables" {
  description = "A map of environment variables for the Lambda function."
  type        = map(string)
  default     = {}
}

variable "log_retention_days" {
  description = "Number of days to retain the Lambda function's logs."
  type        = number
}

variable "project_name" {
  description = "The name of the project, used for tagging."
  type        = string
}

variable "environment_tags" {
  description = "A map of tags to apply to all resources for a specific environment."
  type        = map(string)
  default     = {}
}