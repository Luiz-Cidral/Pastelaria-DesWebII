from django.db.models.signals import post_delete, post_migrate, post_save
from django.dispatch import receiver

from .models import Ingrediente, Prato, ReceitaIngrediente
from .services import atualizar_disponibilidade_pratos


@receiver(post_save, sender=Ingrediente)
def verificar_pratos_apos_alterar_ingrediente(sender, instance, **kwargs):
    atualizar_disponibilidade_pratos(ingrediente_ids=[instance.pk])


@receiver(post_save, sender=ReceitaIngrediente)
@receiver(post_delete, sender=ReceitaIngrediente)
def verificar_prato_apos_alterar_receita(sender, instance, **kwargs):
    atualizar_disponibilidade_pratos(prato_ids=[instance.prato_id])


@receiver(post_save, sender=Prato)
def verificar_disponibilidade_apos_salvar_prato(sender, instance, **kwargs):
    atualizar_disponibilidade_pratos(prato_ids=[instance.pk])
    instance.refresh_from_db(fields=("disponivel",))


@receiver(post_migrate)
def atualizar_disponibilidade_apos_migracoes(sender, **kwargs):
    if sender.label == "pratos":
        atualizar_disponibilidade_pratos()
