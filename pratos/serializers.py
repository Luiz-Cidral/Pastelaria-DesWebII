from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Bebida, Ingrediente, ItemPedido, Pedido, Prato, ReceitaIngrediente
from .services import baixar_estoque_pedido


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


class ItemReceitaSerializer(serializers.ModelSerializer):
    ingrediente = serializers.PrimaryKeyRelatedField(queryset=Ingrediente.objects.all())
    nome_ingrediente = serializers.CharField(source="ingrediente.nome", read_only=True)
    quantidade_gramas = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    class Meta:
        model = ReceitaIngrediente
        fields = ("ingrediente", "nome_ingrediente", "quantidade_gramas")


class PratoSerializer(serializers.ModelSerializer):
    receitas = ItemReceitaSerializer(source="itens_receita", many=True, required=False)

    class Meta:
        model = Prato
        fields = (
            "id",
            "nome",
            "preco",
            "ingredientes",
            "disponivel",
            "descricao",
            "categoria",
            "receitas",
        )

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

    def validate_receitas(self, value):
        ids_ingredientes = [item["ingrediente"].pk for item in value]
        if len(ids_ingredientes) != len(set(ids_ingredientes)):
            raise serializers.ValidationError("Não repita o mesmo ingrediente na receita.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        receitas = validated_data.pop("itens_receita", [])
        prato = Prato.objects.create(**validated_data)
        for item in receitas:
            ReceitaIngrediente.objects.create(prato=prato, **item)
        return prato

    @transaction.atomic
    def update(self, instance, validated_data):
        receitas = validated_data.pop("itens_receita", None)
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        instance.save()

        if receitas is not None:
            instance.itens_receita.all().delete()
            for item in receitas:
                ReceitaIngrediente.objects.create(prato=instance, **item)
        return instance


class BebidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bebida
        fields = ("id", "nome", "preco", "estoque", "disponivel")

    def validate(self, attrs):
        estoque = attrs.get("estoque", self.instance.estoque if self.instance else 0)
        disponivel = attrs.get("disponivel")
        if disponivel is True and estoque == 0:
            raise serializers.ValidationError({"disponivel": "Informe um estoque maior que zero para disponibilizar a bebida."})
        return attrs

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
        if prato is not None and not prato.disponivel:
            raise serializers.ValidationError({"prato": "Este prato está indisponível no momento."})
        if bebida is not None and not bebida.disponivel:
            raise serializers.ValidationError({"bebida": "Esta bebida está indisponível no momento."})
        return attrs


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True)
    estoque_baixado = serializers.BooleanField(read_only=True)

    class Meta:
        model = Pedido
        fields = ("id", "data", "status", "estoque_baixado", "itens")
        read_only_fields = ("id", "data")

    def validate_status(self, value):
        request = self.context.get("request")
        usuario = getattr(request, "user", None)
        if value != Pedido.Status.PENDENTE and not getattr(usuario, "is_staff", False):
            raise serializers.ValidationError("Somente a equipe pode atualizar o status do pedido.")
        return value

    def validate_itens(self, value):
        if not value:
            raise serializers.ValidationError("O pedido precisa conter pelo menos um item.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        itens_data = validated_data.pop("itens")
        status = validated_data.pop("status", Pedido.Status.PENDENTE)
        pedido = Pedido.objects.create(**validated_data)
        for item_data in itens_data:
            produto = item_data.get("prato") or item_data.get("bebida")
            ItemPedido.objects.create(pedido=pedido, preco_unitario=produto.preco, **item_data)
        if status != Pedido.Status.PENDENTE:
            pedido.status = status
            pedido.save(update_fields=("status",))
        if pedido.status == Pedido.Status.PRONTO:
            try:
                pedido = baixar_estoque_pedido(pedido)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc
        return pedido

    @transaction.atomic
    def update(self, instance, validated_data):
        if "itens" in validated_data:
            raise serializers.ValidationError({"itens": "Os itens do pedido não podem ser alterados depois da criação."})
        pedido = Pedido.objects.select_for_update().get(pk=instance.pk)
        for campo, valor in validated_data.items():
            setattr(pedido, campo, valor)
        pedido.save()
        if pedido.status == Pedido.Status.PRONTO:
            try:
                pedido = baixar_estoque_pedido(pedido)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc
        return pedido




