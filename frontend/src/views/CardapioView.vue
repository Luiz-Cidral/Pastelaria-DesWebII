<script setup>
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const pratos = ref([])
const bebidas = ref([])
const carrinho = ref([])
const carregando = ref(true)
const erro = ref('')
const enviandoPedido = ref(false)
const mensagemPedido = ref('')
const busca = ref('')
const categoria = ref('')
const ordenacao = ref('nome')

async function carregarCardapio() {
  carregando.value = true
  erro.value = ''

  const parametrosPratos = new URLSearchParams({ page_size: '100', ordering: ordenacao.value })
  const parametrosBebidas = new URLSearchParams({ page_size: '100', ordering: ordenacao.value })
  if (busca.value.trim()) {
    parametrosPratos.set('search', busca.value.trim())
    parametrosBebidas.set('search', busca.value.trim())
  }
  if (categoria.value) parametrosPratos.set('categoria', categoria.value)

  try {
    const [respostaPratos, respostaBebidas] = await Promise.all([
      fetch(`/api/pratos/?${parametrosPratos}`),
      fetch(`/api/bebidas/?${parametrosBebidas}`),
    ])

    if (!respostaPratos.ok || !respostaBebidas.ok) {
      throw new Error('Não foi possível carregar o cardápio.')
    }

    const dadosPratos = await respostaPratos.json()
    const dadosBebidas = await respostaBebidas.json()

    pratos.value = Array.isArray(dadosPratos) ? dadosPratos : dadosPratos.results || []
    bebidas.value = Array.isArray(dadosBebidas) ? dadosBebidas : dadosBebidas.results || []
  } catch {
    erro.value = 'Não foi possível carregar o cardápio. Tente novamente.'
  } finally {
    carregando.value = false
  }
}

function quantidadeSelecionada(tipo, produto) {
  const item = carrinho.value.find((item) => item.tipo === tipo && item.produto.id === produto.id)
  return item ? item.quantidade : 0
}

function alterarQuantidade(tipo, produto, alteracao) {
  const quantidadeAtual = quantidadeSelecionada(tipo, produto)
  const novaQuantidade = quantidadeAtual + alteracao

  if (novaQuantidade < 0) return
  if (tipo === 'prato' && !produto.disponivel) return
  if (tipo === 'bebida' && alteracao > 0 && (!produto.disponivel || produto.estoque === 0)) return
  if (tipo === 'bebida' && novaQuantidade > produto.estoque) return

  const itemExistente = carrinho.value.find((item) => item.tipo === tipo && item.produto.id === produto.id)

  if (itemExistente) {
    if (novaQuantidade === 0) {
      carrinho.value = carrinho.value.filter((item) => item !== itemExistente)
    } else {
      itemExistente.quantidade = novaQuantidade
    }
  } else if (novaQuantidade > 0) {
    carrinho.value.push({ tipo, produto, quantidade: novaQuantidade })
  }

  mensagemPedido.value = ''
}

const quantidadeTotal = computed(() =>
  carrinho.value.reduce((total, item) => total + item.quantidade, 0),
)

const valorTotal = computed(() =>
  carrinho.value.reduce((total, item) => total + Number(item.produto.preco) * item.quantidade, 0),
)

function formatarPreco(preco) {
  return Number(preco).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

async function finalizarPedido() {
  if (carrinho.value.length === 0) return

  enviandoPedido.value = true
  mensagemPedido.value = ''

  const itens = carrinho.value.map((item) => ({
    [item.tipo]: item.produto.id,
    quantidade: item.quantidade,
  }))

  try {
    const respostaCSRF = await fetch('/api/admin/csrf/', { credentials: 'include' })
    const dadosCSRF = await respostaCSRF.json()
    const resposta = await fetch('/api/pedidos/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': dadosCSRF.csrfToken,
      },
      body: JSON.stringify({ itens }),
    })

    const resultado = await resposta.json()
    if (!resposta.ok) throw new Error('Não foi possível registrar o pedido.')

    mensagemPedido.value = `Pedido #${resultado.id} enviado com sucesso!`
    carrinho.value = []
  } catch {
    mensagemPedido.value = 'Não foi possível enviar o pedido. Confira se a API está disponível.'
  } finally {
    enviandoPedido.value = false
  }
}

function atualizarUrl() {
  const query = {}
  if (busca.value.trim()) query.search = busca.value.trim()
  if (categoria.value) query.categoria = categoria.value
  if (ordenacao.value !== 'nome') query.ordering = ordenacao.value
  router.replace({ path: '/cardapio', query })
}

function limparFiltros() {
  router.replace({ path: '/cardapio', query: {} })
}

watch(
  () => route.query,
  (query) => {
    busca.value = typeof query.search === 'string' ? query.search : ''
    categoria.value = typeof query.categoria === 'string' ? query.categoria : ''
    ordenacao.value = typeof query.ordering === 'string' ? query.ordering : 'nome'
    carregarCardapio()
  },
  { immediate: true },
)
</script>

<template>
  <header class="cabecalho">
    <RouterLink class="marca" to="/">🥟 Pastel Mania</RouterLink>

    <nav aria-label="Navegação principal">
      <ul>
        <li><RouterLink to="/#inicio">Início</RouterLink></li>
        <li class="atual"><RouterLink to="/cardapio">Cardápio</RouterLink></li>
        <li><RouterLink to="/#sobre">Sobre</RouterLink></li>
        <li><RouterLink to="/admin">Admin</RouterLink></li>
      </ul>
    </nav>
  </header>

  <main class="pagina-cardapio">
    <section class="titulo-cardapio">
      <p class="sobretitulo">ESCOLHA SEUS FAVORITOS</p>
      <h1>Nosso cardápio</h1>
      <p>Escolha seus pastéis e bebidas para montar o pedido.</p>
    </section>

    <p v-if="carregando" class="mensagem">Carregando o cardápio...</p>
    <p v-else-if="erro" class="mensagem mensagem-erro">{{ erro }}</p>

    <form v-else class="filtros-cardapio" @submit.prevent="atualizarUrl">
      <label class="campo-busca">
        <span>Pesquisar no cardápio</span>
        <input v-model="busca" type="search" placeholder="Ex.: queijo, carne, suco..." />
      </label>
      <label>
        <span>Categoria dos pastéis</span>
        <select v-model="categoria">
          <option value="">Todas</option>
          <option value="tradicional">Tradicional</option>
          <option value="especial">Especial</option>
          <option value="doce">Doce</option>
          <option value="vegetariano">Vegetariano</option>
        </select>
      </label>
      <label>
        <span>Ordenar por</span>
        <select v-model="ordenacao">
          <option value="nome">Nome: A–Z</option>
          <option value="-nome">Nome: Z–A</option>
          <option value="preco">Menor preço</option>
          <option value="-preco">Maior preço</option>
        </select>
      </label>
      <div class="acoes-filtro">
        <button class="botao botao-finalizar" type="submit">Pesquisar</button>
        <button class="botao-limpar-filtros" type="button" @click="limparFiltros">Limpar</button>
      </div>
    </form>

    <div v-if="!carregando && !erro" class="conteudo-cardapio">
      <div class="lista-cardapio">
        <section class="grupo-produtos">
          <h2>Pastéis</h2>
          <div class="grade-produtos">
            <article v-for="prato in pratos" :key="`prato-${prato.id}`" class="produto-card">
              <img :src="'/Pastel-de-feira.jpg'" :alt="`Foto de ${prato.nome}`" />
              <div class="produto-informacoes">
                <span class="produto-categoria">{{ prato.categoria }}</span>
                <h3>{{ prato.nome }}</h3>
                <p>{{ prato.descricao || 'Preparado com ingredientes selecionados.' }}</p>
                <strong>{{ formatarPreco(prato.preco) }}</strong>
                <span v-if="!prato.disponivel" class="produto-indisponivel">Indisponível</span>
                <div class="controle-quantidade">
                  <button type="button" :disabled="quantidadeSelecionada('prato', prato) === 0" @click="alterarQuantidade('prato', prato, -1)">−</button>
                  <span>{{ quantidadeSelecionada('prato', prato) }}</span>
                  <button type="button" :disabled="!prato.disponivel" @click="alterarQuantidade('prato', prato, 1)">+</button>
                </div>
              </div>
            </article>
          </div>
          <p v-if="pratos.length === 0" class="mensagem">Nenhum pastel encontrado com esses filtros.</p>
        </section>

        <section class="grupo-produtos">
          <h2>Bebidas</h2>
          <div class="grade-produtos">
            <article v-for="bebida in bebidas" :key="`bebida-${bebida.id}`" class="produto-card produto-bebida">
              <div class="imagem-bebida" aria-hidden="true">🥤</div>
              <div class="produto-informacoes">
                <span class="produto-categoria">Bebida</span>
                <h3>{{ bebida.nome }}</h3>
                <p>{{ bebida.estoque }} em estoque</p>
                <strong>{{ formatarPreco(bebida.preco) }}</strong>
                <span v-if="!bebida.disponivel || bebida.estoque === 0" class="produto-indisponivel">Indisponível</span>
                <div class="controle-quantidade">
                  <button type="button" :disabled="quantidadeSelecionada('bebida', bebida) === 0" @click="alterarQuantidade('bebida', bebida, -1)">−</button>
                  <span>{{ quantidadeSelecionada('bebida', bebida) }}</span>
                  <button type="button" :disabled="!bebida.disponivel || bebida.estoque === 0 || quantidadeSelecionada('bebida', bebida) >= bebida.estoque" @click="alterarQuantidade('bebida', bebida, 1)">+</button>
                </div>
              </div>
            </article>
          </div>
          <p v-if="bebidas.length === 0" class="mensagem">Nenhuma bebida encontrada com esses filtros.</p>
        </section>
      </div>

      <aside class="resumo-pedido">
        <h2>Seu pedido</h2>
        <p>{{ quantidadeTotal }} {{ quantidadeTotal === 1 ? 'item' : 'itens' }}</p>
        <ul v-if="carrinho.length">
          <li v-for="item in carrinho" :key="`${item.tipo}-${item.produto.id}`">
            <span>{{ item.quantidade }} × {{ item.produto.nome }}</span>
            <strong>{{ formatarPreco(Number(item.produto.preco) * item.quantidade) }}</strong>
          </li>
        </ul>
        <p v-else class="pedido-vazio">Adicione pratos ou bebidas ao pedido.</p>
        <div class="resumo-total">
          <span>Total</span>
          <strong>{{ formatarPreco(valorTotal) }}</strong>
        </div>
        <button class="botao botao-finalizar" type="button" :disabled="!carrinho.length || enviandoPedido" @click="finalizarPedido">
          {{ enviandoPedido ? 'Enviando...' : 'Finalizar pedido' }}
        </button>
        <p v-if="mensagemPedido" class="mensagem-pedido" role="status">{{ mensagemPedido }}</p>
      </aside>
    </div>
  </main>

  <footer class="rodape">Pastel Mania — feito com carinho.<a class="rodape-github" href="https://github.com/Luiz-Cidral/Pastelaria-DesWebII" target="_blank" rel="noopener noreferrer"><img src="/github.svg" alt="" aria-hidden="true" /><span>GitHub</span></a></footer>
</template>















