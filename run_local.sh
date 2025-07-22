#!/bin/bash

# Local Development Runner for Lab Management System
# This script runs all services locally for development

echo "🚀 Starting Lab Management System (Local Development)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if Redis is running
echo "📡 Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   macOS: brew services start redis"
    echo "   Ubuntu: sudo systemctl start redis-server"
    echo "   Or run: redis-server"
    exit 1
fi
echo "✅ Redis is running"

# Generate and run migrations
echo "🗄️ Making database migrations..."
python manage.py makemigrations

echo "🗄️ Running database migrations..."
python manage.py migrate

# Seed users
echo "👥 Seeding users..."
python manage.py seed_users || echo "⚠️ User seeding skipped (users may already exist)"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start Celery Beat (Scheduler) in background
echo "⏰ Starting Celery Beat (Scheduler)..."
celery -A api beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &
BEAT_PID=$!

# Wait a moment for beat to start
sleep 2

# Start Celery Worker in background
echo "👷 Starting Celery Worker..."
celery -A api worker --loglevel=info --concurrency=2 &
WORKER_PID=$!

# Wait a moment for worker to start
sleep 2

# Start Face Recognition Worker in background
echo "🤖 Starting Face Recognition Worker..."
python manage.py runworker fr_requests &
FACE_WORKER_PID=$!

# Wait a moment for face worker to start
sleep 2

# Start main Django server with Daphne
echo "🌐 Starting Django server with Daphne..."
echo "📱 Backend will be available at: http://localhost:8899"
echo "📊 Admin panel: http://localhost:8899/admin"
echo "📋 API docs: http://localhost:8899/api/v1/docs"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Start Daphne (main server) and capture its PID
daphne -b 0.0.0.0 -p 8899 api.asgi:application &
DAPHNE_PID=$!

# Wait for daphne to start
sleep 2

# Function to stop all processes
cleanup() {
    echo "🛑 Stopping all processes..."
    # Kill specific processes by PID
    if [ ! -z "$BEAT_PID" ]; then
        kill $BEAT_PID 2>/dev/null
    fi
    if [ ! -z "$WORKER_PID" ]; then
        kill $WORKER_PID 2>/dev/null
    fi
    if [ ! -z "$FACE_WORKER_PID" ]; then
        kill $FACE_WORKER_PID 2>/dev/null
    fi
    if [ ! -z "$DAPHNE_PID" ]; then
        kill $DAPHNE_PID 2>/dev/null
    fi
    # Fallback: kill by pattern (more specific)
    pkill -f "celery.*beat" 2>/dev/null
    pkill -f "celery.*worker" 2>/dev/null
    pkill -f "runworker.*fr_requests" 2>/dev/null
    pkill -f "daphne.*8899" 2>/dev/null
    echo "✅ All processes stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for daphne to finish (or be killed)
wait $DAPHNE_PID

# If we get here, daphne has exited, so cleanup other processes
cleanup 