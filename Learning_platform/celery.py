import os
from celery import Celery

from Learning_platform import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Learning_platform.settings')

app = Celery('Learning_platform', broker=settings.CELERY_BROKER_URL)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()