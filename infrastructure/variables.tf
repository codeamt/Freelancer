variable "project" { type = string, default = "freelancer" }
variable "env"     { type = string, default = "prod" }
variable "aws_region" { type = string, default = "us-east-1" }

variable "app_bucket" { type = string, default = "" }
variable "log_retention_days" { type = number, default = 14 }

# Lightsail configuration
variable "enable_lightsail"  { type = bool,   default = true }
variable "lightsail_power"   { type = string, default = "nano" }
variable "lightsail_scale"   { type = number, default = 1 }
variable "container_image"   { type = string, default = "app:latest" }

# Runtime config
variable "redis_url"        { type = string, default = "redis://localhost:6379/0" }
variable "database_url"     { type = string, default = "postgresql+asyncpg://postgres:postgres@db:5432/fastapp" }
variable "mongo_url"        { type = string, default = "mongodb://mongo:27017" }
variable "duckdb_path"      { type = string, default = "/data/analytics.duckdb" }

# Secrets
variable "stripe_api_key" { type = string, default = "sk_test_placeholder" }
variable "smtp_password"  { type = string, default = "demo-password" }