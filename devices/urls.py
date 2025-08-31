# devices/urls.py
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet,UnitOfMeasurementViewSet

router = DefaultRouter()
router.register(r'', DeviceViewSet, basename="devices")
router.register(r'', UnitOfMeasurementViewSet, basename='unit-of-measurement')

urlpatterns = router.urls
