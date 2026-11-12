from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from .filters import BebidaFilter, IngredienteFilter, PratoFilter
from .models import Bebida, Ingrediente, ItemPedido, Pedido, Prato
from .serializers import BebidaSerializer, IngredienteSerializer, ItemPedidoSerializer, PedidoSerializer, PratoSerializer


class PratoViewSet(ModelViewSet):
    queryset = Prato.objects.prefetch_related("ingredientes").all()
    serializer_class = PratoSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = PratoFilter
    ordering_fields = ("nome", "preco", "descricao")
    ordering = ("id",)
    search_fields = ("nome", "descricao")


class IngredienteViewSet(ModelViewSet):
    queryset = Ingrediente.objects.all()
    serializer_class = IngredienteSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = IngredienteFilter
    ordering_fields = ("nome", "estoque")
    ordering = ("id",)
    search_fields = ("nome",)


class BebidaViewSet(ModelViewSet):
    queryset = Bebida.objects.all()
    serializer_class = BebidaSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = BebidaFilter
    ordering_fields = ("nome", "preco", "estoque")
    ordering = ("id",)
    search_fields = ("nome",)


class PedidoViewSet(ModelViewSet):
    queryset = Pedido.objects.prefetch_related("itens__prato", "itens__bebida").all()
    serializer_class = PedidoSerializer
    http_method_names = ("get", "post", "patch", "head", "options")


class ItemPedidoViewSet(ModelViewSet):
    queryset = ItemPedido.objects.select_related("pedido", "prato", "bebida").all()
    serializer_class = ItemPedidoSerializer
    http_method_names = ("get", "head", "options")
