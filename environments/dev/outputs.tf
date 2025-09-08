# environments/dev/outputs.tf

output "s3_bucket_name" {
  description = "Name of the S3 bucket for feedback."
  value       = module.s3.bucket_name
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts."
  value       = module.sns.topic_arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for results."
  value       = module.dynamodb.table_name
}

output "lambda_function_name" {
  description = "Name of the Lambda function."
  value       = module.lambda_function.function_name
}
