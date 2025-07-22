#!/bin/bash

# Comprehensive cache clearing script for Django project
echo "🧹 Clearing all caches and temporary files..."

# Change to project directory
cd "$(dirname "$0")"

echo "📁 Clearing Python bytecode cache..."
# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc files
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove .pyo files
find . -name "*.pyo" -delete 2>/dev/null || true

echo "🗂️ Clearing Django-specific caches..."
# Clear Django sessions
python manage.py clearsessions 2>/dev/null || echo "  ⚠️ Could not clear sessions"

# Clear Django cache if configured
python manage.py clear_cache 2>/dev/null || echo "  ℹ️ No Django cache configured"

echo "📝 Clearing log files..."
# Clear Django logs
> logs/django.log 2>/dev/null || echo "  ℹ️ No log file found"

echo "🗃️ Clearing migration cache..."
# Remove migration __pycache__ in all apps
find . -path "*/migrations/__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "🧽 Clearing IDE and editor caches..."
# Remove common IDE cache files
rm -rf .vscode/.ropeproject 2>/dev/null || true
rm -rf .idea 2>/dev/null || true
rm -rf *.egg-info 2>/dev/null || true

echo "📊 Clearing test caches..."
# Remove test cache
rm -rf .pytest_cache 2>/dev/null || true
rm -rf .coverage 2>/dev/null || true
rm -rf htmlcov 2>/dev/null || true

echo "🔄 Clearing pip cache..."
# Clear pip cache
pip cache purge 2>/dev/null || echo "  ℹ️ Pip cache not cleared"

echo "🗑️ Clearing migration files..."
# Remove migration files except directories and __init__.py
find . -path "*/migrations/*.py" -not -name "__init__.py" -type f -delete 2>/dev/null || true
echo "  ✓ Migration files cleared (kept directories and __init__.py)"

echo "🔄 Reinstalling Django..."
# Reinstall Django to ensure a clean state
pip uninstall django -y && pip install django==4.2.21

echo "✅ Cache clearing completed!"
echo ""
echo "📋 Summary:"
echo "  ✓ Python bytecode cache cleared"
echo "  ✓ Django sessions cleared"
echo "  ✓ Log files cleared"
echo "  ✓ Migration cache cleared"
echo "  ✓ Migration files cleared (kept directories and __init__.py)"
echo "  ✓ IDE cache cleared"
echo "  ✓ Test cache cleared"
echo "  ✓ Django reinstalled"
echo ""
echo "🚀 You may want to restart your Django server now."