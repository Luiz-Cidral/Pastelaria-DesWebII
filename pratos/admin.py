from django.contrib import admin

from .models import Prato, Ingrediente, Bebida


@admin.register(Prato)
class PratoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "preco", "categoria", "disponivel")
    search_fields = ("nome", "descricao")
    list_filter = ("categoria", "disponivel")
    filter_horizontal = ("ingredientes",)

@admin.register(Ingrediente)
class IngredienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "estoque")
    search_fields = ("nome",)
    list_filter = ("estoque",)


@admin.register(Bebida)
class BebidaAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "preco", "estoque")
    search_fields = ("nome",)
    list_filter = ("estoque",)
