"""
ASGI config for the Kathmandu Emergency Bed and Ambulance Finder System.

This is the entry point Daphne actually serves. It routes two kinds of
traffic:
  - "http"      -> normal Django views/REST API (unchanged behaviour)
  - "websocket" -> Django Channels consumers, used for real-time features
                   like live bed/ICU/ambulance availability updates.

The websocket routing list (websocket_urlpatterns) is defined per-app and
combined here once Step 6 (real-time layer) is built. For now it's an empty
list so the server runs correctly; we will not touch this file again until
Step 6 except to import each app's routing module.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Must be called before importing anything that touches Django models,
# so app registry is ready when consumers are imported.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter([
            # Populated in Step 6, e.g.:
            # path('ws/hospitals/<int:hospital_id>/', HospitalStatusConsumer.as_asgi()),
        ])
    ),
})
