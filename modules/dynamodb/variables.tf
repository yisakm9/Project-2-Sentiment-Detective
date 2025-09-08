# modules/dynamodb/variables.tf

variable "table_name" {
  description = "The name of the DynamoDB table."
  type        = string
  default     = "sentiment_analysis_results"
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