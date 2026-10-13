from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter


from .models import Prato, Ingrediente, Bebida
from .serializers import PratoSerializer
from .filters import PratoFilter


class PratoViewSet(ModelViewSet):
    queryset = Prato.objects.all()
    serializer_class = PratoSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = PratoFilter
    ordering_fields = ("nome", "preco", "descricao")
    ordering = ("id",)
    search_fields = ("nome", "descricao")
  