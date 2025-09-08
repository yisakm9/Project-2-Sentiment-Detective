# modules/cloudwatch/main.tf

resource "aws_cloudwatch_metric_alarm" "negative_sentiment_spike" {
  alarm_name          = var.alarm_name
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  period              = 300 # 5 minutes
  threshold           = var.alarm_threshold
  statistic           = "Sum"
  namespace           = var.project_name # Using the project name as the namespace
  metric_name         = "NegativeSentimentCount"
  treat_missing_data  = "notBreaching"

  alarm_description = "Triggers when negative sentiment count spikes beyond the threshold in a 5-minute period."
  actions_enabled   = true
  alarm_actions     = [var.sns_topic_arn]

  tags = merge(
    var.environment_tags,
    {
      Project = var.project_name
    }
  )
}