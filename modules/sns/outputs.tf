# modules/sns/outputs.tf

output "topic_arn" {
  description = "The ARN of the SNS alerts topic."
  value       = aws_sns_topic.alerts.arn
}