# modules/lambda_function/main.tf

resource "aws_lambda_function" "analysis" {
  function_name = var.function_name
  runtime       = var.runtime
  handler       = var.handler
  role          = var.iam_role_arn
  timeout       = var.timeout

  # The filename path is passed in from the root module.
  # This makes the module flexible and independent of the project's file structure.
  filename         = var.zip_file_path
  source_code_hash = filebase64sha256(var.zip_file_path)

  environment {
    variables = var.environment_variables
  }

  tags = merge(
    var.environment_tags,
    {
      Project = var.project_name
    }
  )
}

# Create a CloudWatch Log Group for the Lambda function
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.analysis.function_name}"
  retention_in_days = var.log_retention_days
}