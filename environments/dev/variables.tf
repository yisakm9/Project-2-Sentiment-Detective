# environments/dev/variables.tf

variable "alert_email_endpoint" {
  description = "The email address to send high-urgency SNS alerts to."
  type        = string
}

variable "alarm_threshold" {
  description = "The number of negative sentiment events needed to trigger the CloudWatch alarm."
  type        = number
}

variable "log_retention_days" {
  description = "Number of days to keep Lambda logs."
  type        = number
}

variable "environment_tags" {
  description = "A map of tags to apply to all resources for a specific environment."
  type        = map(string)
}
