# scripts/minio_bootstrap.sh — Advanced MinIO Bootstrap Script with Full Lifecycle Management & Logging

#!/usr/bin/env bash
set -euo pipefail

# --- Logging Setup -----------------------------------------------------------
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/minio_bootstrap_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "🪵 Logging to $LOG_FILE"

# --- Config -----------------------------------------------------------------
MINIO_ALIAS="local"
MINIO_URL="${MINIO_URL:-http://localhost:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-minioadmin}"
APP_BUCKET="${APP_BUCKET:-fastapp-dev-assets}"
MODE="${1:-}" # optional --presign, --cleanup-only, or --reset-bucket flag

# --- Ensure MinIO client is installed ----------------------------------------
if ! command -v mc >/dev/null 2>&1; then
  echo "❌ MinIO client (mc) not found. Installing..."
  curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc
  chmod +x /usr/local/bin/mc
  echo "✅ Installed MinIO client."
fi

# --- Configure MinIO host ----------------------------------------------------
mc alias set "$MINIO_ALIAS" "$MINIO_URL" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" >/dev/null

echo "🔧 Configured MinIO alias: $MINIO_ALIAS → $MINIO_URL"

# --- Helper functions --------------------------------------------------------
function ensure_bucket_exists() {
  if mc ls "$MINIO_ALIAS/$APP_BUCKET" >/dev/null 2>&1; then
    echo "✅ Bucket '$APP_BUCKET' already exists."
  else
    echo "🚀 Creating bucket '$APP_BUCKET'..."
    mc mb "$MINIO_ALIAS/$APP_BUCKET"
    echo "📦 Bucket created successfully."
  fi
  mc version enable "$MINIO_ALIAS/$APP_BUCKET" >/dev/null
  echo "✅ Versioning enabled for $APP_BUCKET"
}

function cleanup_test_files() {
  echo "🧹 Removing test files from bucket '$APP_BUCKET'..."
  mc rm --force --recursive "$MINIO_ALIAS/$APP_BUCKET/test_upload.txt" || true
  mc rm --force --recursive "$MINIO_ALIAS/$APP_BUCKET/big_test.bin" || true
  echo "✅ Cleanup complete."
}

function reset_bucket() {
  echo "⚠️  Resetting entire bucket '$APP_BUCKET' (including versioned objects)..."
  mc rm --force --recursive --versions "$MINIO_ALIAS/$APP_BUCKET" || true
  echo "🧩 Recreating bucket..."
  mc rb --force "$MINIO_ALIAS/$APP_BUCKET" || true
  mc mb "$MINIO_ALIAS/$APP_BUCKET"
  mc version enable "$MINIO_ALIAS/$APP_BUCKET"
  echo "✅ Bucket '$APP_BUCKET' reset and reinitialized."
}

function generate_presigned_urls() {
  echo "🔗 Generating presigned URLs for testing..."
  TEST_FILE="test_upload.txt"
  DOWNLOAD_FILE="downloaded.txt"
  echo "Hello FastApp! $(date)" > "$TEST_FILE"

  echo "📤 Uploading test file..."
  mc cp "$TEST_FILE" "$MINIO_ALIAS/$APP_BUCKET/$TEST_FILE"

  echo "🕓 Creating presigned upload URL (valid 1h)..."
  UPLOAD_URL=$(mc share upload --expire=1h "$MINIO_ALIAS/$APP_BUCKET/$TEST_FILE" | grep -o 'http[^"]*' | head -n 1)
  echo "UPLOAD URL: $UPLOAD_URL"

  echo "🕓 Creating presigned download URL (valid 1h)..."
  DOWNLOAD_URL=$(mc share download --expire=1h "$MINIO_ALIAS/$APP_BUCKET/$TEST_FILE" | grep -o 'http[^"]*' | head -n 1)
  echo "DOWNLOAD URL: $DOWNLOAD_URL"

  echo "💡 Testing presigned upload and download..."
  curl -s -T "$TEST_FILE" "$UPLOAD_URL"
  wget -q "$DOWNLOAD_URL" -O "$DOWNLOAD_FILE"

  if diff "$TEST_FILE" "$DOWNLOAD_FILE" >/dev/null; then
    echo "✅ Integrity check passed: uploaded and downloaded files match."
  else
    echo "❌ Integrity check failed: files differ!"
  fi

  echo "📦 Generating 6MB test file for multipart upload..."
  dd if=/dev/urandom of=big_test.bin bs=1M count=6 status=none

  echo "🧩 Uploading large file to trigger multipart upload..."
  mc cp big_test.bin "$MINIO_ALIAS/$APP_BUCKET/big_test.bin"

  echo "🕓 Creating presigned download URL for multipart file (valid 1h)..."
  BIG_DOWNLOAD_URL=$(mc share download --expire=1h "$MINIO_ALIAS/$APP_BUCKET/big_test.bin" | grep -o 'http[^"]*' | head -n 1)
  wget -q "$BIG_DOWNLOAD_URL" -O big_downloaded.bin

  if diff big_test.bin big_downloaded.bin >/dev/null; then
    echo "✅ Multipart integrity check passed: large file roundtrip successful."
  else
    echo "❌ Multipart integrity check failed: file mismatch detected."
  fi

  rm -f "$TEST_FILE" "$DOWNLOAD_FILE" big_test.bin big_downloaded.bin
  echo "✅ Cleaned up test files."
  echo "✅ Presigned URL generation, multipart test, and validation complete."
}

# --- Main Execution Flow ----------------------------------------------------
ensure_bucket_exists

case "$MODE" in
  --cleanup-only)
    cleanup_test_files
    ;;
  --reset-bucket)
    reset_bucket
    ;;
  --presign)
    generate_presigned_urls
    ;;
  *)
    echo "ℹ️  No special mode selected. Bucket ensured and ready."
    ;;
esac

# --- Display bucket info -----------------------------------------------------
echo "🌐 Accessible via: $MINIO_URL/$APP_BUCKET"
mc ls "$MINIO_ALIAS"

echo "✅ MinIO bootstrap complete."
echo "📘 Full log saved to: $LOG_FILE"