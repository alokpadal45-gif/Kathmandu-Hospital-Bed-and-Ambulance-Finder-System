from django.urls import path

from .consumers import HospitalAvailabilityConsumer

websocket_urlpatterns = [
    path('ws/hospitals/live/', HospitalAvailabilityConsumer.as_asgi()),
]