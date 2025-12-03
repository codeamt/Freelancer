#!/bin/bash

# Freelancer App Cleanup Script
# Removes unnecessary files and caches

echo "🧹 Starting cleanup..."

# Remove Python cache files
echo "Removing __pycache__ directories..."
find app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "Removing .pyc files..."
find app -type f -name "*.pyc" -delete 2>/dev/null

echo "Removing .pyo files..."
find app -type f -name "*.pyo" -delete 2>/dev/null

# Remove macOS system files
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -delete 2>/dev/null

# Remove log files (if any)
echo "Removing log files..."
find app -type f -name "*.log" -delete 2>/dev/null

# Remove temporary files
echo "Removing temporary files..."
find app -type f -name "*.tmp" -delete 2>/dev/null
find app -type f -name "*~" -delete 2>/dev/null

# Remove pytest cache
echo "Removing pytest cache..."
find app -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# Remove coverage files
echo "Removing coverage files..."
find app -type f -name ".coverage" -delete 2>/dev/null
find app -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null

# Remove mypy cache
echo "Removing mypy cache..."
find app -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null

# Remove ruff cache
echo "Removing ruff cache..."
find app -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null

echo "✅ Cleanup complete!"
echo ""
echo "Summary:"
echo "- Removed Python cache files (__pycache__, .pyc, .pyo)"
echo "- Removed system files (.DS_Store)"
echo "- Removed log and temporary files"
echo "- Removed test and linter caches"
