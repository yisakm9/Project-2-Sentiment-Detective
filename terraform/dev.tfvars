# Variables for the Development Environment

# Send high-urgency alerts to a developer's email for testing.
alert_email_endpoint = "yisakmesifin@gmail.com"

# Set a very low threshold to make it easy to trigger the alarm during testing.
alarm_threshold = 2

# Set a shorter log retention period for dev to save on costs.
log_retention_days = 7

# Apply specific tags to all resources to identify them as part of the 'dev' environment.
environment_tags = {
  Environment = "Development"
}