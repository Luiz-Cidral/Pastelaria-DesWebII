from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from pratos.views import PratoViewSet

router = DefaultRouter()
router.register("pratos", PratoViewSet, basename="prato")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]