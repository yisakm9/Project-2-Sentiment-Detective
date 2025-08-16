
variable "alert_email_endpoint" {
  description = "The email address to send high-urgency SNS alerts to."
  type        = string
  # A default is good practice, but the .tfvars file will override it.
  default     = "yisakmesifin@gmail.com"
}

variable "alarm_threshold" {
  description = "The number of negative sentiment events needed to trigger the CloudWatch alarm."
  type        = number
  default     = 10
}

variable "log_retention_days" {
  description = "Number of days to keep Lambda logs."
  type        = number
  default     = 30
}

variable "environment_tags" {
  description = "A map of tags to apply to all resources for a specific environment."
  type        = map(string)
  default     = {}
}