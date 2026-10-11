from rest_framework import serializers

from .models import Prato


class PratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prato
        fields = ("id", "nome", "preco")