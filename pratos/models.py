from django.db import models
from django.db.models import Q


class Ingrediente(models.Model):
    nome = models.CharField(max_length=100)
    estoque = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.nome} (Estoque: {self.estoque} g)"


class Prato(models.Model):

    class Categoria(models.TextChoices):
        TRADICIONAL = "tradicional", "Tradicional"
        ESPECIAL = "especial", "Especial"
        DOCE = "doce", "Doce"
        VEGETARIANO = "vegetariano", "Vegetariano"

    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    ingredientes = models.ManyToManyField(Ingrediente, through="ReceitaIngrediente", related_name="pratos")
    disponivel = models.BooleanField(default=True)
    descricao = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=Categoria.choices, default=Categoria.TRADICIONAL)

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"


class ReceitaIngrediente(models.Model):
    prato = models.ForeignKey(Prato, on_delete=models.CASCADE, related_name="itens_receita")
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.PROTECT, related_name="itens_receita")
    quantidade_gramas = models.DecimalField(max_digits=8, decimal_places=2, help_text="Quantidade utilizada por prato, em gramas.")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["prato", "ingrediente"], name="receita_ingrediente_unico")]

    def __str__(self):
        return f"{self.prato.nome} - {self.ingrediente.nome}: {self.quantidade_gramas} g"


class Bebida(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    estoque = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"


class Pedido(models.Model):

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EM_PREPARO = "em_preparo", "Em preparo"
        PRONTO = "pronto", "Pronto"
        ENTREGUE = "entregue", "Entregue"
        CANCELADO = "cancelado", "Cancelado"

    data = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    estoque_baixado = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return f"Pedido #{self.pk} - {self.get_status_display()}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    prato = models.ForeignKey(Prato, on_delete=models.PROTECT, related_name="itens_pedido", null=True, blank=True)
    bebida = models.ForeignKey(Bebida, on_delete=models.PROTECT, related_name="itens_pedido", null=True, blank=True)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(prato__isnull=False, bebida__isnull=True) | Q(prato__isnull=True, bebida__isnull=False)),
                name="item_pedido_exatamente_um_produto",
            ),
            models.CheckConstraint(condition=Q(quantidade__gt=0), name="item_pedido_quantidade_positiva"),
        ]

    def __str__(self):
        produto = self.prato or self.bebida
        return f"{self.quantidade} x {produto} no pedido #{self.pedido_id}"


