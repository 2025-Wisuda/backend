#!/usr/bin/env python3

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import execute_from_command_line


class DockerSetup:
    def __init__(self):
        self.processes = []

    def run_command(self, command, description):
        """Run a command and handle output"""
        print(f"📋 {description}...")
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            if result.stdout.strip():
                print(f"✅ {description} completed")
            return True
        except subprocess.CalledProcessError as e:
            if "already exists" in str(e.stderr).lower():
                print(f"⚠️ {description} skipped (already exists)")
                return True
            print(f"❌ {description} failed: {e.stderr}")
            return False

    def run_django_command(self, command, description):
        """Run Django management command"""
        print(f"📋 {description}...")
        try:
            execute_from_command_line(["manage.py"] + command.split())
            print(f"✅ {description} completed")
            return True
        except Exception as e:
            print(f"❌ {description} failed: {e}")
            return False

    def create_superuser(self):
        """Create superuser via management command"""
        print("🔑 Creating superuser admin...")
        try:
            # Use shell command for proper superuser creation
            command = [
                "python",
                "manage.py",
                "shell",
                "-c",
                """
import os
from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser if doesn't exist
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@lab.ac.id',
        password='admin123'
    )
    admin.group = 'Kepala Laboratorium'
    admin.save()
    print('✅ Superuser admin created: admin/admin123')
else:
    admin = User.objects.get(username='admin')
    if not admin.is_superuser:
        admin.is_superuser = True
        admin.is_staff = True
        admin.set_password('admin123')
        admin.group = 'Kepala Laboratorium'
        admin.save()
        print('✅ User admin upgraded to superuser: admin/admin123')
    else:
        print('✅ Superuser admin already exists: admin/admin123')
""",
            ]

            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("✅ Superuser creation completed")
            return True
        except Exception as e:
            print(f"❌ Superuser creation failed: {e}")
            return False

    def start_background_service(self, command, name):
        """Start a background service with correct env vars"""
        print(f"🚀 Starting {name}...")
        try:
            # Force correct env for celery/redis - use backend-redis-1 container name
            env = os.environ.copy()
            env.setdefault("CELERY_BROKER_URL", "redis://backend-redis-1:6379/0")
            env.setdefault("REDIS_URL", "redis://backend-redis-1:6379/0")
            env.setdefault("REDIS_HOST", "backend-redis-1")
            env.setdefault("REDIS_PORT", "6379")
            process = subprocess.Popen(command, shell=True, env=env)
            self.processes.append((process, name))
            time.sleep(3)  # Wait for service to start

            if process.poll() is None:  # Still running
                print(f"✅ {name} started (PID: {process.pid})")
                return True
            else:
                print(f"❌ {name} failed to start")
                return False
        except Exception as e:
            print(f"❌ {name} start failed: {e}")
            return False

    def cleanup(self, signum=None, frame=None):
        """Stop all background processes"""
        print("\n🛑 Stopping all processes...")
        for process, name in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"⚠️ {name} killed (forced)")
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")

        print("✅ All processes stopped")
        sys.exit(0)

    def setup_database(self):
        """Setup database with migrations and seeding"""
        steps = [
            ("makemigrations --noinput", "Making migrations"),
            ("migrate --noinput", "Running migrations"),
            ("seed_users", "Seeding users"),
        ]

        for command, description in steps:
            if not self.run_django_command(command, description):
                return False

        return self.create_superuser()

    def setup_static_files(self):
        """Collect static files"""
        return self.run_django_command(
            "collectstatic --noinput", "Collecting static files"
        )

    def start_services(self):
        """Start all background services"""
        services = [
            (
                "celery -A api beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler",
                "Celery Beat",
            ),
            ("celery -A api worker --loglevel=info --concurrency=2", "Celery Worker"),
            ("python manage.py runworker fr_requests", "Face Recognition Worker"),
        ]

        for command, name in services:
            if not self.start_background_service(command, name):
                return False

        return True

    def start_main_server(self):
        """Start main Daphne server"""
        print("🌐 Starting Django server with Daphne...")
        print("📱 Backend available at: http://0.0.0.0:8899")
        print("📊 Admin panel: http://0.0.0.0:8899/admin (admin/admin123)")
        print("🛑 Press Ctrl+C to stop all services\n")

        try:
            # Start Daphne in foreground
            subprocess.run(
                ["daphne", "-b", "0.0.0.0", "-p", "8899", "api.asgi:application"]
            )
        except KeyboardInterrupt:
            self.cleanup()

    def run(self):
        """Main setup and run process"""
        print("🚀 Starting Lab Management Backend Setup...")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

        # Database setup
        if not self.setup_database():
            print("❌ Database setup failed")
            return False

        # Static files
        if not self.setup_static_files():
            print("❌ Static files setup failed")
            return False

        print("✅ Setup completed! Starting all services...")

        # Start background services
        if not self.start_services():
            print("❌ Services startup failed")
            self.cleanup()
            return False

        # Start main server (blocking)
        self.start_main_server()


if __name__ == "__main__":
    setup = DockerSetup()
    setup.run()
