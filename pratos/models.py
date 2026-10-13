from django.db import models

class Ingrediente(models.Model):
    nome = models.CharField(max_length=100)
    estoque = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.nome} (Estoque: {self.estoque})"


class Prato(models.Model):

    class Categoria(models.TextChoices):
        TRADICIONAL = "tradicional", "Tradicional"
        ESPECIAL = "especial", "Especial"
        DOCE = "doce", "Doce"
        VEGETARIANO = "vegetariano", "Vegetariano"

    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    ingredientes = models.ManyToManyField(Ingrediente)
    disponivel = models.BooleanField(default=True)
    descricao = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=Categoria.choices, default=Categoria.TRADICIONAL)

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"


class Bebida(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    estoque = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"