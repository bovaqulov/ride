# tasks.py
from celery import shared_task
from ..models import PassengerTravel
from ..services.driver_service import DriverService

@shared_task
def notify_driver_bot(travel_id):
    try:
        travel = PassengerTravel.objects.get(pk=travel_id)
        DriverService().notify(travel)
    except PassengerTravel.DoesNotExist:
        print(f"Travel with id {travel_id} does not exist")