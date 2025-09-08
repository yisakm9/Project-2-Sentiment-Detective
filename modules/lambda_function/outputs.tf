# modules/lambda_function/outputs.tf

output "function_name" {
  description = "The name of the created Lambda function."
  value       = aws_lambda_function.analysis.function_name
}

output "function_arn" {
  description = "The ARN of the created Lambda function."
  value       = aws_lambda_function.analysis.arn
}