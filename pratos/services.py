from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Bebida, Ingrediente, ItemPedido, Pedido, Prato, ReceitaIngrediente


@transaction.atomic
def baixar_estoque_pedido(pedido):
    pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
    if pedido.estoque_baixado:
        return pedido

    itens = list(ItemPedido.objects.filter(pedido=pedido).select_related("prato", "bebida"))
    if not itens:
        raise ValidationError({"itens": "Não é possível concluir um pedido sem itens."})

    quantidades_pratos = defaultdict(int)
    quantidades_bebidas = defaultdict(int)
    pratos = {}
    for item in itens:
        if item.prato_id:
            quantidades_pratos[item.prato_id] += item.quantidade
            pratos[item.prato_id] = item.prato
        else:
            quantidades_bebidas[item.bebida_id] += item.quantidade

    quantidades_ingredientes = defaultdict(Decimal)
    receitas = ReceitaIngrediente.objects.filter(prato_id__in=quantidades_pratos).order_by("ingrediente_id")
    for receita in receitas:
        quantidades_ingredientes[receita.ingrediente_id] += receita.quantidade_gramas * quantidades_pratos[receita.prato_id]

    ingredientes = list(
        Ingrediente.objects.select_for_update().filter(pk__in=quantidades_ingredientes).order_by("pk")
    )
    bebidas = list(
        Bebida.objects.select_for_update().filter(pk__in=quantidades_bebidas).order_by("pk")
    )

    erros = {}
    for ingrediente in ingredientes:
        necessario = quantidades_ingredientes[ingrediente.pk]
        if ingrediente.estoque < necessario:
            erros.setdefault("ingredientes", []).append(
                f"Estoque insuficiente de {ingrediente.nome}: necessário {necessario} g, disponível {ingrediente.estoque} g."
            )
    for bebida in bebidas:
        necessario = quantidades_bebidas[bebida.pk]
        if bebida.estoque < necessario:
            erros.setdefault("bebidas", []).append(
                f"Estoque insuficiente de {bebida.nome}: necessário {necessario}, disponível {bebida.estoque}."
            )
    if erros:
        raise ValidationError(erros)

    for ingrediente in ingredientes:
        ingrediente.estoque -= quantidades_ingredientes[ingrediente.pk]
        ingrediente.save(update_fields=("estoque",))
    for bebida in bebidas:
        bebida.estoque -= quantidades_bebidas[bebida.pk]
        bebida.save(update_fields=("estoque",))

    pedido.estoque_baixado = True
    pedido.save(update_fields=("estoque_baixado",))
    return pedido

def atualizar_disponibilidade_pratos(prato_ids=None, ingrediente_ids=None):
    pratos = Prato.objects.all()
    if prato_ids is not None:
        pratos = pratos.filter(pk__in=prato_ids)
    if ingrediente_ids is not None:
        pratos = pratos.filter(itens_receita__ingrediente_id__in=ingrediente_ids).distinct()

    for prato in pratos.prefetch_related("itens_receita__ingrediente"):
        if not prato.disponivel:
            continue
        falta_ingrediente = any(
            item.ingrediente.estoque < item.quantidade_gramas
            for item in prato.itens_receita.all()
        )
        if falta_ingrediente:
            Prato.objects.filter(pk=prato.pk, disponivel=True).update(disponivel=False)
            prato.disponivel = False

