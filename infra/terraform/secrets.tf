# Secrets Manager Secret for Application Secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.project_name}-secrets-${var.environment}"
  description = "Application secrets for ${var.project_name}"

  tags = {
    Name = "${var.project_name}-secrets"
  }
}

# Secrets Manager Secret Version
resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    SECRET_KEY         = var.secret_key != "" ? var.secret_key : random_password.secret_key[0].result
    OPENAI_API_KEY     = var.openai_api_key
    AWS_ACCESS_KEY_ID  = var.enable_s3_storage ? aws_iam_access_key.s3_user[0].id : ""
    AWS_SECRET_ACCESS_KEY = var.enable_s3_storage ? aws_iam_access_key.s3_user[0].secret : ""
  })
}

# Random Password for Secret Key (if not provided)
resource "random_password" "secret_key" {
  count   = var.secret_key == "" ? 1 : 0
  length  = 32
  special = true
}

# IAM User for S3 Access (if S3 is enabled)
resource "aws_iam_user" "s3_user" {
  count = var.enable_s3_storage ? 1 : 0
  name  = "${var.project_name}-s3-user"

  tags = {
    Name = "${var.project_name}-s3-user"
  }
}

# IAM Access Key for S3 User
resource "aws_iam_access_key" "s3_user" {
  count = var.enable_s3_storage ? 1 : 0
  user  = aws_iam_user.s3_user[0].name
}

# IAM User Policy for S3 Access
resource "aws_iam_user_policy" "s3_user" {
  count = var.enable_s3_storage ? 1 : 0
  name  = "${var.project_name}-s3-policy"
  user  = aws_iam_user.s3_user[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.storage[0].arn,
          "${aws_s3_bucket.storage[0].arn}/*"
        ]
      }
    ]
  })
}

