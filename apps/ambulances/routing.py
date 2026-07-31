from django.urls import path

from .consumers import AmbulanceRequestConsumer

websocket_urlpatterns = [
    path('ws/requests/<int:request_id>/', AmbulanceRequestConsumer.as_asgi()),
]