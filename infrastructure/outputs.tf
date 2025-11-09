output "bucket" {
  value       = aws_s3_bucket.assets.bucket
  description = "S3 bucket name for assets"
}

output "bucket_url" {
  value       = "https://${aws_s3_bucket.assets.bucket}.s3.${var.aws_region}.amazonaws.com"
  description = "Direct bucket URL"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.app.repository_url
  description = "ECR repository URL"
}

output "stripe_secret_arn" {
  value       = aws_secretsmanager_secret.stripe_api_key.arn
  description = "ARN of the Stripe API key secret"
}

output "smtp_secret_arn" {
  value       = aws_secretsmanager_secret.smtp_password.arn
  description = "ARN of the SMTP password secret"
}