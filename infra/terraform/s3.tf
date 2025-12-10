# S3 Bucket for File Storage
resource "aws_s3_bucket" "storage" {
  count  = var.enable_s3_storage ? 1 : 0
  bucket = "${var.project_name}-storage-${var.environment}-${random_id.bucket_suffix[0].hex}"

  tags = {
    Name = "${var.project_name}-storage"
  }
}

# Random ID for S3 bucket name uniqueness
resource "random_id" "bucket_suffix" {
  count       = var.enable_s3_storage ? 1 : 0
  byte_length = 4
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "storage" {
  count  = var.enable_s3_storage ? 1 : 0
  bucket = aws_s3_bucket.storage[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "storage" {
  count  = var.enable_s3_storage ? 1 : 0
  bucket = aws_s3_bucket.storage[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "storage" {
  count  = var.enable_s3_storage ? 1 : 0
  bucket = aws_s3_bucket.storage[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "storage" {
  count  = var.enable_s3_storage ? 1 : 0
  bucket = aws_s3_bucket.storage[0].id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

