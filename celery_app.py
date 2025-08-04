import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_system.settings')

app = Celery('hospital_system')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'send-medication-reminders': {
        'task': 'notifications.tasks.send_medication_reminders',
        'schedule': 300.0,  # Every 5 minutes
    },
    'check-missed-medications': {
        'task': 'notifications.tasks.check_missed_medications',
        'schedule': 3600.0,  # Every hour
    },
    'generate-daily-schedule': {
        'task': 'notifications.tasks.generate_daily_medication_schedule',
        'schedule': 86400.0,  # Every 24 hours
    },
}

app.conf.timezone = 'UTC'