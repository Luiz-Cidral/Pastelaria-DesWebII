from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import Bebida, Ingrediente, ItemPedido, Pedido, Prato


class IngredienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingrediente
        fields = ("id", "nome", "estoque")

    def validate_nome(self, value):
        nome_limpo = value.strip()
        if len(nome_limpo) < 2:
            raise serializers.ValidationError("O nome deve possuir pelo menos 2 caracteres.")
        return nome_limpo

    def validate_estoque(self, value):
        if value < 0:
            raise serializers.ValidationError("O estoque não pode ser negativo.")
        return value


class PratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prato
        fields = ("id", "nome", "preco", "ingredientes", "disponivel", "descricao", "categoria")

    def validate_nome(self, value):
        nome_limpo = value.strip()
        if len(nome_limpo) < 2:
            raise serializers.ValidationError("O nome deve possuir pelo menos 2 caracteres.")
        return nome_limpo

    def validate_preco(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value

    def validate_descricao(self, value):
        if value is not None and len(value.strip()) > 500:
            raise serializers.ValidationError("A descrição não pode ultrapassar 500 caracteres.")
        return value


class BebidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bebida
        fields = ("id", "nome", "preco", "estoque")

    def validate_nome(self, value):
        nome_limpo = value.strip()
        if len(nome_limpo) < 2:
            raise serializers.ValidationError("O nome deve possuir pelo menos 2 caracteres.")
        return nome_limpo

    def validate_preco(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value

    def validate_estoque(self, value):
        if value < 0:
            raise serializers.ValidationError("O estoque não pode ser negativo.")
        return value


class ItemPedidoSerializer(serializers.ModelSerializer):
    quantidade = serializers.IntegerField(min_value=1)
    prato = serializers.PrimaryKeyRelatedField(queryset=Prato.objects.all(), required=False, allow_null=True)
    bebida = serializers.PrimaryKeyRelatedField(queryset=Bebida.objects.all(), required=False, allow_null=True)
    preco_unitario = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = ("id", "prato", "bebida", "quantidade", "preco_unitario")
        read_only_fields = ("id", "preco_unitario")

    def validate(self, attrs):
        prato = attrs.get("prato")
        bebida = attrs.get("bebida")
        if (prato is None) == (bebida is None):
            raise serializers.ValidationError("Informe exatamente um produto: prato ou bebida.")
        return attrs

    def create(self, validated_data):
        produto = validated_data.get("prato") or validated_data.get("bebida")
        validated_data["preco_unitario"] = produto.preco
        return super().create(validated_data)


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True)

    class Meta:
        model = Pedido
        fields = ("id", "data", "status", "itens")
        read_only_fields = ("id", "data")

    def validate_itens(self, value):
        if not value:
            raise serializers.ValidationError("O pedido precisa conter pelo menos um item.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        itens_data = validated_data.pop("itens")
        pedido = Pedido.objects.create(**validated_data)
        for item_data in itens_data:
            produto = item_data.get("prato") or item_data.get("bebida")
            ItemPedido.objects.create(pedido=pedido, preco_unitario=produto.preco, **item_data)
        return pedido

    def update(self, instance, validated_data):
        if "itens" in validated_data:
            raise serializers.ValidationError({"itens": "Os itens do pedido não podem ser alterados depois da criação."})
        return super().update(instance, validated_data)


