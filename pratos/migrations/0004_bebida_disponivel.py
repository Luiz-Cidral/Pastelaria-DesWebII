from django.db import migrations, models


def marcar_bebidas_sem_estoque_indisponiveis(apps, schema_editor):
    Bebida = apps.get_model("pratos", "Bebida")
    Bebida.objects.filter(estoque__lte=0).update(disponivel=False)


class Migration(migrations.Migration):
    dependencies = [
        ("pratos", "0003_pedido_estoque_baixado"),
    ]

    operations = [
        migrations.AddField(
            model_name="bebida",
            name="disponivel",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(
            marcar_bebidas_sem_estoque_indisponiveis,
            migrations.RunPython.noop,
        ),
    ]