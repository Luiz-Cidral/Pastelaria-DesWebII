from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Bebida, Ingrediente, Pedido, Prato, ReceitaIngrediente


class PastelariaAPITests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="funcionario",
            password="senha-de-teste",
            is_staff=True,
        )
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=usuario)
        self.public_client = APIClient()

    def criar_prato(self, nome, preco, categoria=Prato.Categoria.TRADICIONAL, **opcoes):
        return Prato.objects.create(
            nome=nome,
            preco=preco,
            categoria=categoria,
            **opcoes,
        )

    def test_pratos_permitem_crud_completo_para_funcionario(self):
        dados = {
            "nome": "Pastel de queijo",
            "preco": "12.50",
            "categoria": "tradicional",
            "descricao": "Queijo derretido",
            "disponivel": True,
            "receitas": [],
        }

        resposta_criacao = self.admin_client.post("/api/pratos/", dados, format="json")
        self.assertEqual(resposta_criacao.status_code, status.HTTP_201_CREATED)
        prato_id = resposta_criacao.data["id"]

        resposta_lista = self.admin_client.get("/api/pratos/")
        self.assertEqual(resposta_lista.status_code, status.HTTP_200_OK)
        self.assertIn(prato_id, [item["id"] for item in resposta_lista.data["results"]])

        resposta_detalhe = self.admin_client.get(f"/api/pratos/{prato_id}/")
        self.assertEqual(resposta_detalhe.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta_detalhe.data["nome"], "Pastel de queijo")

        dados_atualizados = {
            **resposta_detalhe.data,
            "nome": "Pastel de queijo especial",
            "preco": "15.00",
        }
        resposta_atualizacao = self.admin_client.put(
            f"/api/pratos/{prato_id}/",
            dados_atualizados,
            format="json",
        )
        self.assertEqual(resposta_atualizacao.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta_atualizacao.data["nome"], "Pastel de queijo especial")

        resposta_exclusao = self.admin_client.delete(f"/api/pratos/{prato_id}/")
        self.assertEqual(resposta_exclusao.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Prato.objects.filter(pk=prato_id).exists())

    def test_escrita_de_pratos_exige_funcionario(self):
        resposta = self.public_client.post(
            "/api/pratos/",
            {"nome": "Pastel de carne", "preco": "12.00", "categoria": "tradicional"},
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Prato.objects.count(), 0)

    def test_preco_invalido_e_rejeitado(self):
        resposta = self.admin_client.post(
            "/api/pratos/",
            {"nome": "Pastel inválido", "preco": "0", "categoria": "tradicional"},
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("preco", resposta.data)

    def test_filtro_busca_ordenacao_e_paginacao_de_pratos(self):
        queijo = self.criar_prato(
            "Pastel de queijo",
            "10.00",
            descricao="Recheio de queijo",
            categoria=Prato.Categoria.DOCE,
        )
        carne = self.criar_prato(
            "Pastel de carne",
            "15.00",
            descricao="Carne temperada",
            categoria=Prato.Categoria.ESPECIAL,
        )
        frango = self.criar_prato(
            "Pastel de frango",
            "12.00",
            descricao="Frango com requeijão",
        )

        resposta_filtro = self.public_client.get(
            "/api/pratos/",
            {"categoria": "doce", "preco_maximo": "11"},
        )
        self.assertEqual(resposta_filtro.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in resposta_filtro.data["results"]], [queijo.id])

        resposta_busca = self.public_client.get("/api/pratos/", {"search": "frango"})
        self.assertEqual(resposta_busca.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in resposta_busca.data["results"]], [frango.id])

        resposta_ordenacao = self.public_client.get("/api/pratos/", {"ordering": "-preco"})
        self.assertEqual(
            [item["id"] for item in resposta_ordenacao.data["results"]],
            [carne.id, frango.id, queijo.id],
        )

        resposta_paginacao = self.public_client.get(
            "/api/pratos/",
            {"ordering": "nome", "page": "2", "page_size": "1"},
        )
        self.assertEqual(resposta_paginacao.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta_paginacao.data["page"], 2)
        self.assertEqual(resposta_paginacao.data["page_size"], 1)
        self.assertEqual(resposta_paginacao.data["total_pages"], 3)

    def test_prato_fica_indisponivel_quando_falta_ingrediente(self):
        ingrediente = Ingrediente.objects.create(nome="Queijo", estoque="50.00")
        prato = self.criar_prato("Pastel de queijo", "12.00")

        ReceitaIngrediente.objects.create(
            prato=prato,
            ingrediente=ingrediente,
            quantidade_gramas="100.00",
        )

        prato.refresh_from_db()
        self.assertFalse(prato.disponivel)

    def test_estoque_so_e_baixado_quando_pedido_fica_pronto_e_apenas_uma_vez(self):
        ingrediente = Ingrediente.objects.create(nome="Queijo", estoque="500.00")
        prato = self.criar_prato("Pastel de queijo", "12.00")
        ReceitaIngrediente.objects.create(
            prato=prato,
            ingrediente=ingrediente,
            quantidade_gramas="100.00",
        )
        bebida = Bebida.objects.create(nome="Suco", preco="8.00", estoque=5)

        resposta_pedido = self.public_client.post(
            "/api/pedidos/",
            {"itens": [{"prato": prato.id, "quantidade": 2}, {"bebida": bebida.id, "quantidade": 1}]},
            format="json",
        )
        self.assertEqual(resposta_pedido.status_code, status.HTTP_201_CREATED)
        pedido_id = resposta_pedido.data["id"]
        self.assertEqual(resposta_pedido.data["status"], Pedido.Status.PENDENTE)
        ingrediente.refresh_from_db()
        bebida.refresh_from_db()
        self.assertEqual(str(ingrediente.estoque), "500.00")
        self.assertEqual(bebida.estoque, 5)

        resposta_pronto = self.admin_client.patch(
            f"/api/pedidos/{pedido_id}/",
            {"status": Pedido.Status.PRONTO},
            format="json",
        )
        self.assertEqual(resposta_pronto.status_code, status.HTTP_200_OK)
        self.assertTrue(resposta_pronto.data["estoque_baixado"])
        ingrediente.refresh_from_db()
        bebida.refresh_from_db()
        self.assertEqual(str(ingrediente.estoque), "300.00")
        self.assertEqual(bebida.estoque, 4)

        resposta_repetida = self.admin_client.patch(
            f"/api/pedidos/{pedido_id}/",
            {"status": Pedido.Status.PRONTO},
            format="json",
        )
        self.assertEqual(resposta_repetida.status_code, status.HTTP_200_OK)
        ingrediente.refresh_from_db()
        bebida.refresh_from_db()
        self.assertEqual(str(ingrediente.estoque), "300.00")
        self.assertEqual(bebida.estoque, 4)

    def test_estoque_insuficiente_impede_concluir_pedido_sem_baixa_parcial(self):
        ingrediente = Ingrediente.objects.create(nome="Queijo", estoque="150.00")
        prato = self.criar_prato("Pastel de queijo", "12.00")
        ReceitaIngrediente.objects.create(
            prato=prato,
            ingrediente=ingrediente,
            quantidade_gramas="100.00",
        )
        bebida = Bebida.objects.create(nome="Suco", preco="8.00", estoque=5)
        resposta_pedido = self.public_client.post(
            "/api/pedidos/",
            {"itens": [{"prato": prato.id, "quantidade": 2}, {"bebida": bebida.id, "quantidade": 2}]},
            format="json",
        )
        self.assertEqual(resposta_pedido.status_code, status.HTTP_201_CREATED)

        Ingrediente.objects.filter(pk=ingrediente.pk).update(estoque="100.00")
        resposta_pronto = self.admin_client.patch(
            f"/api/pedidos/{resposta_pedido.data['id']}/",
            {"status": Pedido.Status.PRONTO},
            format="json",
        )

        self.assertEqual(resposta_pronto.status_code, status.HTTP_400_BAD_REQUEST)
        pedido = Pedido.objects.get(pk=resposta_pedido.data["id"])
        self.assertEqual(pedido.status, Pedido.Status.PENDENTE)
        self.assertFalse(pedido.estoque_baixado)
        ingrediente.refresh_from_db()
        bebida.refresh_from_db()
        self.assertEqual(str(ingrediente.estoque), "100.00")
        self.assertEqual(bebida.estoque, 5)

