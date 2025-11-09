terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# --- S3 for assets -----------------------------------------------------------
resource "random_id" "bucket_suffix" {
  byte_length = 3
}

resource "aws_s3_bucket" "assets" {
  bucket = var.app_bucket == "" ? "${var.project}-assets-${random_id.bucket_suffix.hex}" : var.app_bucket
  tags = {
    Project = var.project
    Env     = var.env
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket                  = aws_s3_bucket.assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration { status = "Enabled" }
}

# --- ECR for container images -----------------------------------------------
resource "aws_ecr_repository" "app" {
  name                 = "${var.project}-repo"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
  tags = { Project = var.project }
}

# Optional lifecycle policy: keep only 10 latest images
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name
  policy = <<POLICY
  {
    "rules": [
      {
        "rulePriority": 1,
        "description": "Keep last 10 images",
        "selection": {
          "tagStatus": "any",
          "countType": "imageCountMoreThan",
          "countNumber": 10
        },
        "action": { "type": "expire" }
      }
    ]
  }
  POLICY
}

# --- Secrets Manager ---------------------------------------------------------
resource "aws_secretsmanager_secret" "stripe_api_key" {
  name = "/freelancer/${var.env}/stripe_api_key"
  description = "Stripe secret key for Freelancer"
}

resource "aws_secretsmanager_secret_version" "stripe_api_key_ver" {
  secret_id     = aws_secretsmanager_secret.stripe_api_key.id
  secret_string = var.stripe_api_key
}

resource "aws_secretsmanager_secret" "smtp_password" {
  name = "/freelancer/${var.env}/smtp_password"
  description = "SMTP password for transactional emails"
}

resource "aws_secretsmanager_secret_version" "smtp_password_ver" {
  secret_id     = aws_secretsmanager_secret.smtp_password.id
  secret_string = var.smtp_password
}

# --- CloudWatch & SSM -------------------------------------------------------
resource "aws_cloudwatch_log_group" "app" {
  name              = "/freelancer/${var.env}"
  retention_in_days = var.log_retention_days
  tags = { Project = var.project }
}

resource "aws_ssm_parameter" "bucket_url" {
  name  = "/freelancer/${var.env}/AWS_BUCKET_URL"
  type  = "String"
  value = "https://${aws_s3_bucket.assets.bucket}.s3.${var.aws_region}.amazonaws.com"
}

# --- Lightsail Container Service (optional) ---------------------------------
resource "aws_lightsail_container_service" "freelancer" {
  count = var.enable_lightsail ? 1 : 0
  name  = "${var.project}-${var.env}"
  power = var.lightsail_power
  scale = var.lightsail_scale
  tags  = { Project = var.project, Env = var.env }
}

resource "aws_lightsail_container_service_deployment_version" "freelancer" {
  count                    = var.enable_lightsail ? 1 : 0
  container_service_name   = aws_lightsail_container_service.freelancer[0].name
  containers = {
    app = {
      image        = var.container_image
      ports        = { "8000" = "HTTP" }
      environment  = {
        APP_ENV          = var.env
        AWS_REGION       = var.aws_region
        AWS_BUCKET_URL   = aws_ssm_parameter.bucket_url.value
        REDIS_URL        = var.redis_url
        DATABASE_URL     = var.database_url
        MONGO_URL        = var.mongo_url
        DUCKDB_PATH      = var.duckdb_path
      }
      command      = ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    }
  }
  public_endpoint {
    container_name = "app"
    container_port = 8000
    health_check {
      healthy_threshold   = 2
      unhealthy_threshold = 2
      timeout_seconds     = 5
      interval_seconds    = 10
      path                = "/healthz"
    }
  }
}

# --- Outputs ----------------------------------------------------------------
output "s3_bucket" {
  value = aws_s3_bucket.assets.bucket
}

output "s3_bucket_url" {
  value = aws_ssm_parameter.bucket_url.value
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
  description = "ECR repository endpoint for image pushes"
}

output "secretsmanager_stripe_arn" {
  value = aws_secretsmanager_secret.stripe_api_key.arn
  description = "ARN of the stored Stripe secret"
}

output "secretsmanager_smtp_arn" {
  value = aws_secretsmanager_secret.smtp_password.arn
  description = "ARN of the stored SMTP secret"
}

output "lightsail_service_name" {
  value       = try(aws_lightsail_container_service.freelancer[0].name, null)
  description = "Name of the Lightsail container service (if enabled)"
}

output "lightsail_endpoint" {
  value       = try(aws_lightsail_container_service.freelancer[0].url, null)
  description = "Public URL of the service (after first deployment)"
}
