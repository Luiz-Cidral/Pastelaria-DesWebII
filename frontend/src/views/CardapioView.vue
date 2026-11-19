<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

const pratos = ref([])
const bebidas = ref([])
const carrinho = ref([])
const carregando = ref(true)
const erro = ref('')
const enviandoPedido = ref(false)
const mensagemPedido = ref('')

async function carregarCardapio() {
  try {
    const [respostaPratos, respostaBebidas] = await Promise.all([
      fetch('/api/pratos/'),
      fetch('/api/bebidas/'),
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

onMounted(carregarCardapio)
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

    <div v-else class="conteudo-cardapio">
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
          <p v-if="pratos.length === 0" class="mensagem">Nenhum prato cadastrado.</p>
        </section>

        <section class="grupo-produtos">
          <h2>Bebidas</h2>
          <div class="grade-produtos">
            <article v-for="bebida in bebidas" :key="`bebida-${bebida.id}`" class="produto-card produto-bebida">
              <div class="imagem-bebida" aria-hidden="true">🥤</div>
              <div class="produto-informacoes">
                <span class="produto-categoria">Bebida</span>
                <h3>{{ bebida.nome }}</h3>
                <p>{{ bebida.estoque > 0 ? `${bebida.estoque} disponíveis` : 'Fora de estoque' }}</p>
                <strong>{{ formatarPreco(bebida.preco) }}</strong>
                <div class="controle-quantidade">
                  <button type="button" :disabled="quantidadeSelecionada('bebida', bebida) === 0" @click="alterarQuantidade('bebida', bebida, -1)">−</button>
                  <span>{{ quantidadeSelecionada('bebida', bebida) }}</span>
                  <button type="button" :disabled="bebida.estoque === 0 || quantidadeSelecionada('bebida', bebida) >= bebida.estoque" @click="alterarQuantidade('bebida', bebida, 1)">+</button>
                </div>
              </div>
            </article>
          </div>
          <p v-if="bebidas.length === 0" class="mensagem">Nenhuma bebida cadastrada.</p>
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

  <footer class="rodape">Pastel Mania — feito com carinho.</footer>
</template>





