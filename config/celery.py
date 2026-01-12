"""
Celery configuration for PostPro.
"""

import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery app
app = Celery('postpro')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')


# Periodic Tasks Schedule
from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-rss-feeds-every-15-min': {
        'task': 'apps.automation.tasks.check_rss_feeds_task',
        'schedule': crontab(minute='*/15'),  # Runs every 15 minutes
    },
}
