from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
# celery.py-da qo'shish

app.conf.worker_prefetch_multiplier = 1  # RAM yeyishhini kamaytirish
app.conf.worker_max_tasks_per_child = 1000  # Memory leaks oldini olish


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.beat_schedule = {
    "deactivate-old-online-drivers-every-hour": {
        "task": "bot_app.tasks.deactivate_drivers_tasks.deactivate_old_online_drivers",
        "schedule": crontab(minute=59),  # har soat boshida
        "args": (6,),
    },
}
