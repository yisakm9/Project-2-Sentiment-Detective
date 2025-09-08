# modules/dynamodb/main.tf

resource "aws_dynamodb_table" "analysis_results" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = merge(
    var.environment_tags,
    {
      Project = var.project_name
    }
  )
}