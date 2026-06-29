data "aws_caller_identity" "current" {}

# AWS-managed CloudFront policies we'll reuse.
data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}
data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}
data "aws_cloudfront_origin_request_policy" "all_viewer" {
  name = "Managed-AllViewerExceptHostHeader"
}

# ---------------------------------------------------------------------------
# Private S3 bucket that stores the built frontend files. Not public — only
# CloudFront may read it. Bucket names are globally unique, so we suffix the
# account ID.
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "this" {
  bucket = "${var.project}-frontend-${data.aws_caller_identity.current.account_id}"
  tags   = { Name = "${var.project}-frontend" }
}

# Block ALL public access to the bucket.
resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Origin Access Control: the modern way to let ONLY CloudFront read the bucket.
resource "aws_cloudfront_origin_access_control" "this" {
  name                              = "${var.project}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ---------------------------------------------------------------------------
# The CloudFront distribution (CDN). Two origins:
#   - S3 for the frontend (default)
#   - the ALB for /api/* (so the API is reachable over HTTPS, same domain)
# ---------------------------------------------------------------------------
resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100" # cheapest: US, Canada, Europe
  comment             = "${var.project} frontend + API"

  # Origin 1: the private S3 bucket (frontend files)
  origin {
    origin_id                = "s3-frontend"
    domain_name              = aws_s3_bucket.this.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.this.id
  }

  # Origin 2: the ALB (backend API), reached over plain HTTP
  origin {
    origin_id   = "alb-api"
    domain_name = var.alb_dns_name
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default: serve the SPA from S3, force HTTPS, cache aggressively.
  default_cache_behavior {
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = data.aws_cloudfront_cache_policy.optimized.id
  }

  # /api/* : forward to the ALB, no caching, pass through everything.
  ordered_cache_behavior {
    path_pattern             = "/api/*"
    target_origin_id         = "alb-api"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer.id
  }

  # Single Page App routing: any missing path returns index.html so the
  # React app can handle the route instead of showing an S3 error.
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Use the free *.cloudfront.net certificate (HTTPS out of the box).
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = { Name = "${var.project}-cdn" }
}

# Bucket policy: allow this specific CloudFront distribution to read objects.
data "aws_iam_policy_document" "s3" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.this.arn}/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.this.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id
  policy = data.aws_iam_policy_document.s3.json
}
