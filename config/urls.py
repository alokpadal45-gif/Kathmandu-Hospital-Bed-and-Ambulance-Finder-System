"""
Root URL configuration.

Each app owns its own urls.py; this file just mounts them under a sensible
prefix. Include statements are added incrementally as each app is built
(Steps 2-9) — commented placeholders show what's coming so the file's
final shape is clear from Step 1.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # path('accounts/', include('apps.accounts.urls', namespace='accounts')),   # Step 2
    # path('hospitals/', include('apps.hospitals.urls', namespace='hospitals')), # Step 3
    # path('ambulances/', include('apps.ambulances.urls', namespace='ambulances')), # Step 4
    # path('api/', include('apps.api.urls')),                                   # Step 5
    # path('', include('apps.dashboard.urls', namespace='dashboard')),          # Step 7-9
]

# Serve user-uploaded media locally in development only.
# In production this is handled by the web server (nginx) instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
