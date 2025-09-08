# modules/sns/main.tf

# Create the SNS Topic for sending alerts
resource "aws_sns_topic" "alerts" {
  name = var.topic_name

  tags = merge(
    var.environment_tags,
    {
      Project = var.project_name
    }
  )
}

# Create an email subscription to the SNS topic
resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_endpoint
}