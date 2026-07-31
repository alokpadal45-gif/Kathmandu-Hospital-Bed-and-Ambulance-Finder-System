# this is what daphne actually serves. routes http requests to normal
# django views and websocket connections to channels consumers.

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# has to be called before importing anything that touches django models
# (the routing imports below pull in consumers, which import models)
django_asgi_app = get_asgi_application()

from apps.ambulances.routing import websocket_urlpatterns as ambulance_ws_urlpatterns  # noqa: E402
from apps.hospitals.routing import websocket_urlpatterns as hospital_ws_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(hospital_ws_urlpatterns + ambulance_ws_urlpatterns)
    ),
})