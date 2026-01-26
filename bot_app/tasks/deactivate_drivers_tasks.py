from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from bot_app.models import Driver, DriverStatus

@shared_task
def deactivate_old_online_drivers(hours: int = 6):
    cutoff = timezone.now() - timedelta(hours=hours)
    updated = Driver.objects.filter(
        status=DriverStatus.ONLINE,
        last_online_at__lt=cutoff
    ).update(status=DriverStatus.OFFLINE)
    return updated
