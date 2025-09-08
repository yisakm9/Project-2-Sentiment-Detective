# modules/cloudwatch/variables.tf

variable "alarm_name" {
  description = "The name for the CloudWatch alarm."
  type        = string
  default     = "negative-sentiment-spike"
}

variable "alarm_threshold" {
  description = "The number of negative sentiment events needed to trigger the alarm."
  type        = number
}

variable "sns_topic_arn" {
  description = "The ARN of the SNS topic to send alarm notifications to."
  type        = string
}

variable "project_name" {
  description = "The name of the project, used for tagging and the metric namespace."
  type        = string
}

variable "environment_tags" {
  description = "A map of tags to apply to all resources for a specific environment."
  type        = map(string)
  default     = {}
}