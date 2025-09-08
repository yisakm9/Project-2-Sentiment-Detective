# modules/iam/outputs.tf

output "lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda function."
  value       = aws_iam_role.lambda_role.arn
}