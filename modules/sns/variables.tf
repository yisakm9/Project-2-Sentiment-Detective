# modules/sns/variables.tf

variable "topic_name" {
  description = "The name for the SNS topic."
  type        = string
  default     = "sentiment-detective-alerts"
}

variable "alert_email_endpoint" {
  description = "The email address to subscribe to the SNS topic for alerts."
  type        = string
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