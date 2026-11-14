<script setup>
import { onMounted, ref } from 'vue'

const pratos = ref([])
const carregando = ref(true)
const erro = ref(false)

async function carregarPratos() {
  try {
    const resposta = await fetch('/api/pratos/')

    if (!resposta.ok) {
      throw new Error('Não foi possível carregar os pratos.')
    }

    const dados = await resposta.json()
    const lista = Array.isArray(dados) ? dados : dados.results || []
    pratos.value = lista.filter((prato) => prato.disponivel)
  } catch {
    erro.value = true
  } finally {
    carregando.value = false
  }
}

function formatarPreco(preco) {
  return Number(preco).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

onMounted(carregarPratos)
</script>

<template>
  <header class="cabecalho">
    <div class="marca">🥟 Pastel Mania</div>

    <nav>
      <ul>
        <li class="atual"><a href="#inicio">Início</a></li>
        <li><a href="#cardapio">Cardápio</a></li>
        <li><a href="#sobre">Sobre</a></li>
      </ul>
    </nav>
  </header>

  <main>
    <section id="inicio" class="banner">
      <div class="banner-texto">
        <h1>Bem-vindo à</h1>
        <span>Pastel Mania!</span>
        <p>Pastéis saborosos, preparados com carinho para você.</p>
        <a class="botao" href="#cardapio">Confira nosso cardápio</a>
      </div>

      <img src="/Pastel-de-feira.jpg" alt="Pastéis dourados em uma cesta" />
    </section>

    <section id="cardapio" class="white-itens">
      <h2>Nossos pratos</h2>

      <p v-if="carregando" class="mensagem">Carregando o cardápio...</p>
      <p v-else-if="erro" class="mensagem">
        Não foi possível carregar os pratos.
      </p>
      <p v-else-if="pratos.length === 0" class="mensagem">
        Nenhum prato disponível no momento.
      </p>

      <ul v-else>
        <li v-for="prato in pratos.slice(0, 3)" :key="prato.id">
          <div class="imagem-prato" aria-hidden="true">🥟</div>
          <h3>{{ prato.nome }}</h3>
          <p class="descricao">
            {{ prato.descricao || 'Preparado com ingredientes selecionados.' }}
          </p>
          <strong>{{ formatarPreco(prato.preco) }}</strong>
        </li>
      </ul>
    </section>

    <section id="sobre" class="sobre">
      <h2>Sobre a Pastel Mania</h2>
      <p>
        Uma pastelaria feita para reunir pessoas e deixar o dia mais gostoso.
        Venha conhecer nosso cardápio!
      </p>
    </section>
  </main>

  <footer class="rodape">Pastel Mania — feito com carinho.</footer>
</template>

