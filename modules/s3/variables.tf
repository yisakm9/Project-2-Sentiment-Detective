# modules/s3/variables.tf

variable "project_name" {
  description = "The name of the project, used for resource naming and tagging."
  type        = string
}

variable "object_expiration_days" {
  description = "Number of days after which to expire feedback files in the S3 bucket."
  type        = number
  default     = 30
}

variable "environment_tags" {
  description = "A map of tags to apply to all resources for a specific environment."
  type        = map(string)
  default     = {}
}