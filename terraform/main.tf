terraform {
  backend "s3" {
    bucket       = "ysak-terraform-state-bucket"
    key          = "voicevault/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}

# Terraform Configuration 
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0" 
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Random Suffix for bucket
resource "random_id" "suffix" {
  byte_length = 4
}

# S3 Bucket for Feedback
resource "aws_s3_bucket" "feedback" {
  bucket = "sentiment-detective-feedback-${random_id.suffix.hex}"

  tags = merge(
    var.environment_tags,
    {
      Project = "SentimentDetective"
    }
  ) 
}

resource "aws_s3_bucket_public_access_block" "feedback_block" {
  bucket                  = aws_s3_bucket.feedback.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "feedback_lifecycle" {
  bucket = aws_s3_bucket.feedback.id

  rule {
    id     = "cleanup-old-feedback"
    status = "Enabled"

    filter {
      prefix = "" # Applies to all objects
    }

    expiration {
      days = 30
    }
  }
}

# DynamoDB Table
resource "aws_dynamodb_table" "analysis_results" {
  name         = "sentiment_analysis_results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Project = "SentimentDetective"
  }
}

# SNS Topic & Subscription
resource "aws_sns_topic" "alerts" {
  name = "sentiment-detective-alerts"

  tags = {
    Project = "SentimentDetective"
  }
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_endpoint 
}

# IAM Role & Policies
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
}

resource "aws_iam_policy_attachment" "lambda_basic" {
  name       = "lambda-basic-execution"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom_policy" {
  name = "lambda-sentiment-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ],
        Resource = aws_dynamodb_table.analysis_results.arn
      },
      {
        Effect = "Allow",
        Action = [
          "bedrock:InvokeModel"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "cloudwatch:PutMetricData"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "sns:Publish"
        ],
        Resource = aws_sns_topic.alerts.arn
      },
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource = [
          aws_s3_bucket.feedback.arn,
          "${aws_s3_bucket.feedback.arn}/*"
        ]
      }
    ]
  })
}

# In terraform/main.tf

resource "aws_lambda_function" "analysis" {
  function_name = "sentiment-detective-analyzer"
  runtime       = "python3.11"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 60

  # --- CORRECTED CODE ---
  # The GitHub workflow creates this zip file and moves it here for Terraform to find.
  filename         = "lambda_package.zip" 
  source_code_hash = filebase64sha256("lambda_package.zip")
  # --- END OF CORRECTION ---

  environment {
    variables = {
      DDB_TABLE_NAME  = aws_dynamodb_table.analysis_results.name
      SNS_TOPIC_ARN   = aws_sns_topic.alerts.arn
      FEEDBACK_BUCKET = aws_s3_bucket.feedback.bucket
    }
  }

  tags = {
    Project = "SentimentDetective"
  }

  # --- DELETE THIS LINE ---
  # depends_on = [
  #   null_resource.lambda_build
  # ]
  # --- END OF DELETION ---
}

# CloudWatch Logs Retention
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.analysis.function_name}"
  retention_in_days = var.log_retention_days
}

# S3 -> Lambda Notification

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.analysis.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.feedback.arn
}

resource "aws_s3_bucket_notification" "feedback_events" {
  bucket = aws_s3_bucket.feedback.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.analysis.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}


# CloudWatch Alarm

resource "aws_cloudwatch_metric_alarm" "negative_sentiment_spike" {
  alarm_name          = "negative-sentiment-spike"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  period              = 300
  threshold           = var.alarm_threshold 
  statistic           = "Sum"
  namespace           = "SentimentDetective"
  metric_name         = "NegativeSentimentCount"
  treat_missing_data  = "notBreaching"

  alarm_description = "Triggers when negative sentiment spikes beyond threshold in 5 min"
  actions_enabled   = true
  alarm_actions     = [aws_sns_topic.alerts.arn]

  tags = {
    Project = "SentimentDetective"
  }
}

# Outputs

output "s3_bucket_name" {
  value = aws_s3_bucket.feedback.bucket
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.analysis_results.name
}

output "lambda_function_name" {
  value = aws_lambda_function.analysis.function_name
}

