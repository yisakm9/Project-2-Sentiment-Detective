# modules/iam/main.tf

# IAM Role for the Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "sentiment-detective-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = merge(
    var.environment_tags,
    {
      Project = var.project_name
    }
  )
}

# Attach the basic Lambda execution policy for CloudWatch Logs
resource "aws_iam_policy_attachment" "lambda_basic" {
  name       = "lambda-basic-execution"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Define and attach a custom policy with specific permissions for other services
resource "aws_iam_role_policy" "lambda_custom_policy" {
  name = "lambda-sentiment-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "dynamodb:PutItem"
        ],
        Resource = var.dynamodb_table_arn
      },
      {
        Effect   = "Allow",
        Action   = [
          "bedrock:InvokeModel"
        ],
        Resource = "*" # Scoped down in a real-world scenario if possible
      },
      {
        Effect   = "Allow",
        Action   = [
          "cloudwatch:PutMetricData"
        ],
        Resource = "*" # put_metric_data does not support resource-level permissions
      },
      {
        Effect   = "Allow",
        Action   = [
          "sns:Publish"
        ],
        Resource = var.sns_topic_arn
      },
      {
        Effect   = "Allow",
        Action   = [
          "s3:GetObject"
        ],
        Resource = "${var.s3_bucket_arn}/*" # Allow access to objects within the bucket
      }
    ]
  })
}