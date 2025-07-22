"""
Celery configuration for Lab Management System.
"""

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

app = Celery("lab_management")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Explicitly import tasks after Django is configured
try:
    import django

    django.setup()
    import fcm_notifications.tasks.notification_tasks
except Exception as e:
    print(f"Warning: Could not import FCM tasks: {e}")


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
