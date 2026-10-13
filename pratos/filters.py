from django_filters import rest_framework as filters

from .models import Prato, Ingrediente, Bebida


class PratoFilter(filters.FilterSet):
    preco_minimo = filters.NumberFilter(field_name="preco", lookup_expr="gte")
    preco_maximo = filters.NumberFilter(field_name="preco", lookup_expr="lte")
    disponivel = filters.BooleanFilter(field_name = "disponivel")
    categoria = filters.ChoiceFilter(field_name="categoria", choices=Prato.Categoria.choices)

    class Meta:
        model = Prato
        fields = ("preco_minimo", "preco_maximo", "disponivel", "categoria")

class BebidaFilter(filters.FilterSet):

    preco_minimo = filters.NumberFilter(field_name="preco", lookup_expr="gte")
    preco_maximo = filters.NumberFilter(field_name="preco", lookup_expr="lte")

    estoque_minimo = filters.NumberFilter(field_name="estoque", lookup_expr="gte")
    estoque_maximo = filters.NumberFilter(field_name="estoque", lookup_expr="lte")

    class Meta:
        model = Bebida
        fields = ("preco_minimo", "preco_maximo", "estoque_minimo", "estoque_maximo")

class IngredienteFilter(filters.FilterSet):

    estoque_minimo = filters.NumberFilter(field_name="estoque", lookup_expr="gte")
    estoque_maximo = filters.NumberFilter(field_name="estoque", lookup_expr="lte")

    class Meta:
        model = Bebida
        fields = ("estoque_minimo", "estoque_maximo")