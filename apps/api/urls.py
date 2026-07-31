from rest_framework.routers import DefaultRouter

from .views import AmbulanceRequestViewSet, AmbulanceViewSet, HospitalViewSet

router = DefaultRouter()
router.register('hospitals', HospitalViewSet, basename='hospital')
router.register('ambulances', AmbulanceViewSet, basename='ambulance')
router.register('requests', AmbulanceRequestViewSet, basename='ambulance-request')

urlpatterns = router.urls