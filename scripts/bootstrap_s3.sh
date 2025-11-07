#!/usr/bin/env bash
# Cloud Resource Bootstrap Script
set -e

# --- Configuration -----------------------------------------------------------
APP_BUCKET="${APP_BUCKET:-fastapp-assets}"
REGION="${AWS_REGION:-us-east-1}"

# --- AWS S3 Bucket Check ------------------------------------------------------
if aws s3api head-bucket --bucket "$APP_BUCKET" 2>/dev/null; then
  echo "✅ S3 bucket '$APP_BUCKET' already exists"
else
  echo "🚀 Creating S3 bucket: $APP_BUCKET"
  aws s3api create-bucket --bucket "$APP_BUCKET" --region "$REGION" --create-bucket-configuration LocationConstraint="$REGION"
  echo "✅ Bucket created"
fi

# --- Write URL to .env if not present ----------------------------------------
BUCKET_URL="https://${APP_BUCKET}.s3.${REGION}.amazonaws.com"
if ! grep -q "AWS_BUCKET_URL" .env 2>/dev/null; then
  echo "AWS_BUCKET_URL=${BUCKET_URL}" >> .env
  echo "✅ Added AWS_BUCKET_URL to .env"
else
  echo "ℹ️  AWS_BUCKET_URL already exists in .env"
fi

# --- Verify Connection -------------------------------------------------------
echo "🌐 Verifying S3 connectivity..."
aws s3 ls s3://$APP_BUCKET

echo "✅ Bootstrap complete for region $REGION"