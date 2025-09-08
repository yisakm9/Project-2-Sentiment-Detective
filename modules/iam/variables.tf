# modules/iam/variables.tf

variable "project_name" {
  description = "The name of the project, used for resource naming and tagging."
  type        = string
  default     = "SentimentDetective"
}

variable "dynamodb_table_arn" {
  description = "The ARN of the DynamoDB table for analysis results."
  type        = string
}

variable "sns_topic_arn" {
  description = "The ARN of the SNS topic for high-urgency alerts."
  type        = string
}

variable "s3_bucket_arn" {
  description = "The ARN of the S3 bucket where feedback files are stored."
  type        = string
}

variable "environment_tags" {
  description = "A map of tags to apply to all resources for a specific environment."
  type        = map(string)
  default     = {}
}