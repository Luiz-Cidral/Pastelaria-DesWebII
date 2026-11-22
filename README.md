# Pastelaria

Sistema para uma pastelaria. O cliente consulta o cardápio e pode fazer um pedido com pastéis, bebidas ou os dois. A equipe administra os produtos, os ingredientes, o estoque e os pedidos.

O backend foi feito com Django e Django REST Framework. As páginas do cliente e do painel administrativo foram feitas com Vue.js, HTML, CSS e JavaScript.

## Funcionalidades

- Ver pratos e bebidas, inclusive quando estiverem indisponíveis.
- Pesquisar, filtrar e ordenar os itens do cardápio.
- Criar pedidos com pratos, bebidas ou ambos.
- Cadastrar e editar pratos, bebidas e ingredientes no painel administrativo.
- Acompanhar e atualizar o andamento dos pedidos.
- Conferir o estoque necessário antes de concluir um pedido.
- Marcar pratos como indisponíveis quando faltam ingredientes.

## O que é necessário

- Python 3.14 ou superior.
- `uv` para instalar as dependências Python.
- Node.js 22.18 ou superior (ou 24.12 ou superior) e npm.
- Git para baixar o projeto.

## Instalação e execução

### 1. Baixe o projeto

```bash
git clone https://github.com/Luiz-Cidral/Pastelaria-DesWebII.git
cd Pastelaria-DesWebII
```

### 2. Inicie o backend

Na pasta principal, instale as dependências e prepare o banco local:

```bash
uv sync
uv run python manage.py migrate
```

Para criar um usuário que possa entrar no painel administrativo:

```bash
uv run python manage.py createsuperuser
```

Inicie o Django:

```bash
uv run python manage.py runserver
```

O backend ficará em `http://127.0.0.1:8000/`.

### 3. Inicie o frontend

Abra outro terminal e execute:

```bash
cd frontend
npm ci
npm run dev
```

O site ficará em `http://localhost:5173/`. Deixe o backend rodando: durante o desenvolvimento, o frontend encaminha as chamadas da API para o Django.

## Páginas

Com os dois servidores ligados, acesse:

- Início: `http://localhost:5173/`
- Cardápio: `http://localhost:5173/cardapio`
- Painel administrativo do site: `http://localhost:5173/admin`
- Django Admin: `http://127.0.0.1:8000/admin/`
- Documentação da API: `http://127.0.0.1:8000/api/docs/`
- Documentação alternativa: `http://127.0.0.1:8000/api/redoc/`

O painel administrativo do site foi construído em Vue. O Django Admin é outra interface, fornecida pelo próprio Django.

## API REST

A API usa Django REST Framework e trabalha com dados em JSON. O recurso principal, pratos, permite listar, consultar um item, cadastrar, atualizar e excluir. Bebidas e ingredientes também podem ser gerenciados pela API. Os pedidos podem ser criados, consultados e atualizados pela equipe.

| Endereço | Uso |
|---|---|
| `/api/pratos/` | Listar ou cadastrar pratos |
| `/api/pratos/{id}/` | Consultar, atualizar ou excluir um prato |
| `/api/bebidas/` | Listar ou cadastrar bebidas |
| `/api/bebidas/{id}/` | Consultar, atualizar ou excluir uma bebida |
| `/api/ingredientes/` | Listar ou cadastrar ingredientes |
| `/api/ingredientes/{id}/` | Consultar, atualizar ou excluir um ingrediente |
| `/api/pedidos/` | Listar pedidos ou criar um pedido |
| `/api/pedidos/{id}/` | Consultar ou atualizar o status de um pedido |
| `/api/itens-pedido/` | Consultar os itens dos pedidos |

Alterações de pratos, bebidas e ingredientes exigem login administrativo. Clientes podem consultar o cardápio e criar pedidos. Somente a equipe autenticada pode consultar e atualizar pedidos.

## Busca e filtros

Os parâmetros podem ser combinados na URL. Por exemplo, para mostrar pastéis doces disponíveis:

```text
http://127.0.0.1:8000/api/pratos/?categoria=doce&disponivel=true
```

Para procurar por “queijo”, ordenar do mais caro para o mais barato e mostrar cinco itens por página:

```text
http://127.0.0.1:8000/api/pratos/?search=queijo&ordering=-preco&page=1&page_size=5
```

Parâmetros disponíveis para pratos:

- `categoria`: `tradicional`, `especial`, `doce` ou `vegetariano`.
- `disponivel`: `true` ou `false`.
- `preco_minimo` e `preco_maximo`.
- `search`: pesquisa pelo nome ou pela descrição.
- `ordering`: ordena por `nome` ou `preco`. Use `-preco` para mostrar os maiores preços primeiro.
- `page` e `page_size`: escolhem a página e a quantidade de itens. O limite é 100 itens por página.

Bebidas também aceitam `disponivel=true` ou `disponivel=false`, além de `preco_minimo`, `preco_maximo`, `estoque_minimo` e `estoque_maximo`. Bebidas indisponíveis continuam no cardápio com um aviso e não podem ser adicionadas ao pedido. Ingredientes aceitam `estoque_minimo` e `estoque_maximo`. Os três recursos permitem busca textual e ordenação por seus campos disponíveis.

## Pedidos e estoque

Um pedido pode conter pratos e bebidas. Cada item deve ter um produto e uma quantidade. Use os IDs cadastrados no sistema:

```json
{
  "itens": [
    { "prato": 1, "quantidade": 2 },
    { "bebida": 1, "quantidade": 1 }
  ]
}
```

O pedido começa com status `pendente`. O preço é obtido do cadastro do produto, portanto não deve ser enviado pelo cliente. A equipe pode alterar o status para `em_preparo`, `pronto`, `entregue` ou `cancelado`.

Quando o pedido passa para `pronto`, o sistema verifica se há estoque suficiente de bebidas e dos ingredientes usados nos pratos. Se faltar estoque, o pedido não é concluído e nenhuma quantidade é descontada parcialmente. A baixa acontece apenas uma vez por pedido. Quando o estoque de uma bebida chega a zero, ela continua visível no cardápio como indisponível; depois de repor o estoque, a equipe pode marcá-la como disponível novamente.

Se o estoque de um ingrediente ficar abaixo da quantidade necessária para a receita de um prato, o sistema marca o prato como indisponível.

## Dados do sistema

O banco local é SQLite e é acessado pelo ORM do Django. Os models representam:

- `Prato`: nome, preço, categoria, descrição e disponibilidade.
- `Ingrediente`: nome e quantidade em estoque.
- `ReceitaIngrediente`: ingredientes e quantidades usados em cada prato.
- `Bebida`: nome, preço e quantidade em estoque.
- `Pedido`: data, status e informação sobre a baixa de estoque.
- `ItemPedido`: produto e quantidade de cada linha do pedido.

As migrações que criam e alteram essas tabelas ficam em `pratos/migrations/`. Para preparar o banco local, use `uv run python manage.py migrate`.

## Testes

Os testes do backend estão em `pratos/tests.py`. Para executá-los:

```bash
uv run python manage.py test pratos
```

## Publicação

O projeto foi publicado na Vercel: [https://pastelaria-deswebii.vercel.app/](https://pastelaria-deswebii.vercel.app/)


## Repositório

[Pastelaria no GitHub](https://github.com/Luiz-Cidral/Pastelaria-DesWebII)
