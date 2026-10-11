from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from .models import Prato
from .serializers import PratoSerializer
from .filters import PratoFilter


class PratoViewSet(ModelViewSet):
    queryset = Prato.objects.all()
    serializer_class = PratoSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = PratoFilter