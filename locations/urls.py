from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DistrictViewSet, StateViewSet

router = DefaultRouter()
router.register(r"states", StateViewSet, basename="state")
router.register(r"districts", DistrictViewSet, basename="district")

urlpatterns = [
    path("", include(router.urls)),
]
