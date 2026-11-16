import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAdminUser
from rest_framework.viewsets import ModelViewSet

from .filters import BebidaFilter, IngredienteFilter, PratoFilter
from .models import Bebida, Ingrediente, ItemPedido, Pedido, Prato
from .serializers import BebidaSerializer, IngredienteSerializer, ItemPedidoSerializer, PedidoSerializer, PratoSerializer


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_staff)


class IsAdminOrCreateOrder(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True
        return request.method == "POST" and getattr(view, "action", None) == "create"


@require_GET
@ensure_csrf_cookie
def admin_csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


@require_GET
def admin_session(request):
    if request.user.is_authenticated and request.user.is_staff:
        return JsonResponse({"usuario": request.user.username})
    return JsonResponse({"detail": "Acesso administrativo necessário."}, status=401)


@require_POST
@csrf_protect
def admin_login(request):
    try:
        dados = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Dados de login inválidos."}, status=400)

    usuario = authenticate(
        request,
        username=str(dados.get("usuario", "")).strip(),
        password=str(dados.get("senha", "")),
    )
    if usuario is None or not usuario.is_staff:
        return JsonResponse({"detail": "Usuário ou senha inválidos."}, status=401)

    login(request, usuario)
    return JsonResponse({"usuario": usuario.username, "csrfToken": get_token(request)})


@require_POST
@csrf_protect
def admin_logout(request):
    logout(request)
    return JsonResponse({"ok": True})


class PratoViewSet(ModelViewSet):
    queryset = Prato.objects.prefetch_related("ingredientes", "itens_receita__ingrediente").all()
    serializer_class = PratoSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = PratoFilter
    ordering_fields = ("nome", "preco", "descricao")
    ordering = ("id",)
    search_fields = ("nome", "descricao")


class IngredienteViewSet(ModelViewSet):
    queryset = Ingrediente.objects.all()
    serializer_class = IngredienteSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = IngredienteFilter
    ordering_fields = ("nome", "estoque")
    ordering = ("id",)
    search_fields = ("nome",)


class BebidaViewSet(ModelViewSet):
    queryset = Bebida.objects.all()
    serializer_class = BebidaSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = BebidaFilter
    ordering_fields = ("nome", "preco", "estoque")
    ordering = ("id",)
    search_fields = ("nome",)


class PedidoViewSet(ModelViewSet):
    queryset = Pedido.objects.prefetch_related("itens__prato", "itens__bebida").all()
    serializer_class = PedidoSerializer
    permission_classes = (IsAdminOrCreateOrder,)
    http_method_names = ("get", "post", "patch", "head", "options")


class ItemPedidoViewSet(ModelViewSet):
    queryset = ItemPedido.objects.select_related("pedido", "prato", "bebida").all()
    serializer_class = ItemPedidoSerializer
    permission_classes = (IsAdminUser,)
    http_method_names = ("get", "head", "options")
