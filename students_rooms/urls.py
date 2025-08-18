from __future__ import annotations

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RoomViewSet, StudentViewSet, CombinedViewSet


router = DefaultRouter()
router.register(r"rooms", RoomViewSet, basename="room")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"combined", CombinedViewSet, basename="combined")


urlpatterns = [
    path("", include(router.urls)),
]


