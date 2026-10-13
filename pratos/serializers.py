from decimal import Decimal

from rest_framework import serializers

from .models import Ingrediente, Prato, Bebida


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

    def validate_estoque(self, value):
        if value < 0:
            raise serializers.ValidationError("O estoque não pode ser negativo.")
        return value

    def validate_descricao(self, value):
        if value is not None and len(value.strip()) > 500:
            raise serializers.ValidationError("A descrição não pode ultrapassar 500 caracteres.")
        return value

class BebidaSeriaizer(serializers.ModelSerializer):
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
                raise serializers.ValidationError(
                    "O estoque não pode ser negativo."
                )
            return value