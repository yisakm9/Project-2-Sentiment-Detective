# modules/s3/main.tf

# Create a random suffix to ensure the S3 bucket name is globally unique
resource "random_id" "suffix" {
  byte_length = 4
}

# Create the S3 bucket for storing feedback files
resource "aws_s3_bucket" "feedback" {
  # The bucket name is made lowercase and includes the project name and random suffix
  bucket = lower("${var.project_name}-feedback-${random_id.suffix.hex}")

  tags = merge(
    var.environment_tags,
    {
      Project = var.project_name
    }
  )
}

# Block all public access to the bucket
resource "aws_s3_bucket_public_access_block" "feedback_block" {
  bucket                  = aws_s3_bucket.feedback.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Configure a lifecycle rule to automatically delete old feedback files
resource "aws_s3_bucket_lifecycle_configuration" "feedback_lifecycle" {
  bucket = aws_s3_bucket.feedback.id

  rule {
    id     = "cleanup-old-feedback"
    status = "Enabled"

    filter {
      prefix = "" # Applies to all objects in the bucket
    }

    expiration {
      days = var.object_expiration_days
    }
  }
}