# environments/dev/main.tf

# Module for S3 Bucket
module "s3" {
  source                 = "../../modules/s3"
  project_name           = "SentimentDetective"
  object_expiration_days = 30 # As per the original main.tf
  environment_tags       = var.environment_tags
}

# Module for DynamoDB Table
module "dynamodb" {
  source           = "../../modules/dynamodb"
  project_name     = "SentimentDetective"
  environment_tags = var.environment_tags
}

# Module for SNS Topic and Subscription
module "sns" {
  source               = "../../modules/sns"
  project_name         = "SentimentDetective"
  alert_email_endpoint = var.alert_email_endpoint
  environment_tags     = var.environment_tags
}

# Module for IAM Role and Policies
module "iam" {
  source             = "../../modules/iam"
  project_name       = "SentimentDetective"
  s3_bucket_arn      = module.s3.bucket_arn
  dynamodb_table_arn = module.dynamodb.table_arn
  sns_topic_arn      = module.sns.topic_arn
  environment_tags   = var.environment_tags
}

# Module for the Lambda Function
module "lambda_function" {
  source           = "../../modules/lambda_function"
  project_name     = "SentimentDetective"
  iam_role_arn     = module.iam.lambda_role_arn
  zip_file_path    = "../../../lambda_package.zip" # Path relative to this main.tf
  environment_variables = {
    DDB_TABLE_NAME = module.dynamodb.table_name
    SNS_TOPIC_ARN  = module.sns.topic_arn
  }
  log_retention_days = var.log_retention_days
  environment_tags   = var.environment_tags
}

# Module for the CloudWatch Alarm
module "cloudwatch" {
  source           = "../../modules/cloudwatch"
  project_name     = "SentimentDetective"
  alarm_threshold  = var.alarm_threshold
  sns_topic_arn    = module.sns.topic_arn
  environment_tags = var.environment_tags
}

# --- Glue Resources ---
# These resources connect the modules together.

# Grant S3 permission to invoke the Lambda function
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_function.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = module.s3.bucket_arn
}

# Create the S3 event notification to trigger the Lambda function
resource "aws_s3_bucket_notification" "feedback_events" {
  bucket = module.s3.bucket_id

  lambda_function {
    lambda_function_arn = module.lambda_function.function_arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}