from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from pratos.views import BebidaViewSet, IngredienteViewSet, ItemPedidoViewSet, PedidoViewSet, PratoViewSet, admin_csrf, admin_login, admin_logout, admin_session

router = DefaultRouter()
router.register("pratos", PratoViewSet, basename="prato")
router.register("ingredientes", IngredienteViewSet, basename="ingrediente")
router.register("bebidas", BebidaViewSet, basename="bebida")
router.register("pedidos", PedidoViewSet, basename="pedido")
router.register("itens-pedido", ItemPedidoViewSet, basename="item-pedido")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/admin/csrf/", admin_csrf),
    path("api/admin/login/", admin_login),
    path("api/admin/logout/", admin_logout),
    path("api/admin/sessao/", admin_session),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

