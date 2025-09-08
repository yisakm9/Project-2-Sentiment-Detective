# modules/s3/outputs.tf

output "bucket_arn" {
  description = "The ARN of the feedback S3 bucket."
  value       = aws_s3_bucket.feedback.arn
}

output "bucket_id" {
  description = "The ID (name) of the feedback S3 bucket."
  value       = aws_s3_bucket.feedback.id
}

output "bucket_name" {
  description = "The name of the feedback S3 bucket."
  value       = aws_s3_bucket.feedback.bucket
}