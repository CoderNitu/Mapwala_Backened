# devices/urls.py
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet

router = DefaultRouter()

router.register(r'', DeviceViewSet, basename="device")


urlpatterns = router.urls
