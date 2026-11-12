from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from pratos.views import BebidaViewSet, IngredienteViewSet, ItemPedidoViewSet, PedidoViewSet, PratoViewSet

router = DefaultRouter()
router.register("pratos", PratoViewSet, basename="prato")
router.register("ingredientes", IngredienteViewSet, basename="ingrediente")
router.register("bebidas", BebidaViewSet, basename="bebida")
router.register("pedidos", PedidoViewSet, basename="pedido")
router.register("itens-pedido", ItemPedidoViewSet, basename="item-pedido")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
