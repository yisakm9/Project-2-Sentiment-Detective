# modules/cloudwatch/outputs.tf

output "alarm_arn" {
  description = "The ARN of the CloudWatch alarm."
  value       = aws_cloudwatch_metric_alarm.negative_sentiment_spike.arn
}

output "alarm_name" {
  description = "The name of the CloudWatch alarm."
  value       = aws_cloudwatch_metric_alarm.negative_sentiment_spike.alarm_name
}