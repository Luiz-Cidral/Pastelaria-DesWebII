from django.contrib import admin

from .models import Bebida, Ingrediente, ItemPedido, Pedido, Prato, ReceitaIngrediente
from .services import baixar_estoque_pedido


class ReceitaIngredienteInline(admin.TabularInline):
    model = ReceitaIngrediente
    extra = 1


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ("preco_unitario",)

    def has_add_permission(self, request, obj=None):
        return not (obj and obj.estoque_baixado)

    def has_change_permission(self, request, obj=None):
        return not (obj and obj.estoque_baixado)

    def has_delete_permission(self, request, obj=None):
        return not (obj and obj.estoque_baixado)


@admin.register(Prato)
class PratoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "preco", "categoria", "disponivel")
    search_fields = ("nome", "descricao")
    list_filter = ("categoria", "disponivel")
    inlines = [ReceitaIngredienteInline]


@admin.register(Ingrediente)
class IngredienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "estoque")
    search_fields = ("nome",)
    list_filter = ("estoque",)


@admin.register(Bebida)
class BebidaAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "preco", "estoque", "disponivel")
    search_fields = ("nome",)
    list_filter = ("disponivel", "estoque")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "data", "status", "estoque_baixado")
    list_filter = ("status", "estoque_baixado")
    readonly_fields = ("data", "estoque_baixado")
    inlines = [ItemPedidoInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if form.instance.status == Pedido.Status.PRONTO:
            baixar_estoque_pedido(form.instance)

