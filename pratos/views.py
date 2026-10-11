from rest_framework.viewsets import ModelViewSet

from .models import Prato
from .serializers import PratoSerializer


class PratoViewSet(ModelViewSet):
    queryset = Prato.objects.all()
    serializer_class = PratoSerializer