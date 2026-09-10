resource "random_id" "bucket_random_id" {
    byte_length = 4
    keepers = {
        bucket_name = var.bucket_name
    }
}

resource "aws_s3_bucket" "portfolio_bucket" {
    bucket = "${var.bucket_name}-${random_id.bucket_random_id.hex}"
}

resource "aws_s3_bucket_website_configuration" "portfolio_bucket_website" {
    bucket = aws_s3_bucket.portfolio_bucket.id
    index_document {
        suffix = "index.html"
    }
}

resource "aws_s3_bucket_public_access_block" "portfolio_bucket_public_access" {
    bucket = aws_s3_bucket.portfolio_bucket.id

    block_public_acls       = false
    block_public_policy     = false
    ignore_public_acls      = false
    restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "portfolio_bucket_policy" {
    bucket = aws_s3_bucket.portfolio_bucket.id
    depends_on = [aws_s3_bucket_public_access_block.portfolio_bucket_public_access]
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Principal = "*"
                Action = "s3:GetObject"
                Resource = "${aws_s3_bucket.portfolio_bucket.arn}/*"
            }
        ]
    })
}