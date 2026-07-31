# each app has its own urls.py, this file just includes them all under a
# prefix. commented out ones get uncommented as each app gets built

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    # path('hospitals/', include('apps.hospitals.urls', namespace='hospitals')), # not needed yet - hospitals are managed through /admin/ and /api/
    # path('ambulances/', include('apps.ambulances.urls', namespace='ambulances')), # Step 4 - request creation goes through dashboard app instead
    path('api/', include('apps.api.urls')),
    path('', include('apps.dashboard.urls', namespace='dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)