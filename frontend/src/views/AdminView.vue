<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

const usuario = ref('')
const csrfToken = ref('')
const nomeLogin = ref('')
const senhaLogin = ref('')
const aba = ref('pratos')
const pratos = ref([])
const filtroDisponibilidade = ref('todos')
const pratosFiltrados = computed(() => {
  if (filtroDisponibilidade.value === 'disponiveis') return pratos.value.filter((prato) => prato.disponivel)
  if (filtroDisponibilidade.value === 'indisponiveis') return pratos.value.filter((prato) => !prato.disponivel)
  return pratos.value
})
const bebidas = ref([])
const ingredientes = ref([])
const pedidos = ref([])
const filtroPedidos = ref('andamento')
const opcoesFiltroPedidos = [
  { valor: 'andamento', nome: 'Em andamento' },
  { valor: 'pendente', nome: 'Pendentes' },
  { valor: 'em_preparo', nome: 'Em preparo' },
  { valor: 'pronto', nome: 'Prontos' },
  { valor: 'entregue', nome: 'Entregues' },
  { valor: 'cancelado', nome: 'Cancelados' },
  { valor: 'todos', nome: 'Todos' },
]
const pedidosFiltrados = computed(() => {
  if (filtroPedidos.value === 'todos') return pedidos.value
  if (filtroPedidos.value === 'andamento') {
    return pedidos.value.filter((pedido) => ['pendente', 'em_preparo', 'pronto'].includes(pedido.status))
  }
  return pedidos.value.filter((pedido) => pedido.status === filtroPedidos.value)
})

function contarPedidos(filtro) {
  if (filtro === 'todos') return pedidos.value.length
  if (filtro === 'andamento') {
    return pedidos.value.filter((pedido) => ['pendente', 'em_preparo', 'pronto'].includes(pedido.status)).length
  }
  return pedidos.value.filter((pedido) => pedido.status === filtro).length
}
const carregandoPedidos = ref(false)
const erroPedidos = ref('')
const carregando = ref(false)
const erro = ref('')
const mensagem = ref('')
const formularioPrato = ref({})
const formularioBebida = ref({})
const formularioIngrediente = ref({})
const salvandoPrato = ref(false)
const salvandoBebida = ref(false)
const salvandoIngrediente = ref(false)
const excluindo = ref('')
let estoqueSincronizando = false
let intervaloEstoque = null

const statusPedidos = [
  { valor: 'pendente', nome: 'Pendente' },
  { valor: 'em_preparo', nome: 'Em preparo' },
  { valor: 'pronto', nome: 'Pronto' },
  { valor: 'entregue', nome: 'Entregue' },
  { valor: 'cancelado', nome: 'Cancelado' },
]

function novoPrato() {
  formularioPrato.value = {
    id: null,
    nome: '',
    preco: '',
    categoria: 'tradicional',
    descricao: '',
    disponivel: true,
    receitas: [{ ingrediente: '', quantidade_gramas: '' }],
  }
}

function novoIngrediente() {
  formularioIngrediente.value = { id: null, nome: '', estoque: 0 }
}

function novaBebida() {
  formularioBebida.value = { id: null, nome: '', preco: '', estoque: 0, disponivel: false }
}

function resultados(dados) {
  return Array.isArray(dados) ? dados : dados.results || []
}

function mensagemErro(dados) {
  if (dados && typeof dados.detail === 'string') return dados.detail
  if (dados && typeof dados === 'object') return Object.values(dados).flat().join(' ')
  return 'Não foi possível concluir a operação.'
}

async function requisicao(url, opcoes = {}) {
  const cabecalhos = { ...(opcoes.headers || {}) }
  const metodo = (opcoes.method || 'GET').toUpperCase()
  if (opcoes.body) cabecalhos['Content-Type'] = 'application/json'
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(metodo)) {
    cabecalhos['X-CSRFToken'] = csrfToken.value
  }

  const controle = new AbortController()
  const limiteEspera = setTimeout(() => controle.abort(), 15000)

  try {
    const resposta = await fetch(url, {
      ...opcoes,
      headers: cabecalhos,
      credentials: 'include',
      signal: controle.signal,
    })
    const texto = await resposta.text()
    let dados = null

    if (texto) {
      try {
        dados = JSON.parse(texto)
      } catch {
        dados = { detail: 'O servidor retornou uma resposta que não está em JSON.' }
      }
    }

    if (!resposta.ok) throw new Error(mensagemErro(dados))
    return dados
  } catch (falha) {
    if (falha.name === 'AbortError') {
      throw new Error('A consulta demorou mais de 15 segundos. Confira se o Django está respondendo e tente novamente.')
    }
    throw falha
  } finally {
    clearTimeout(limiteEspera)
  }
}

async function carregarTokenCSRF() {
  const dados = await requisicao('/api/admin/csrf/')
  csrfToken.value = dados.csrfToken
}

async function carregarDados() {
  carregando.value = true
  erro.value = ''

  try {
    const [dadosPratos, dadosBebidas, dadosIngredientes] = await Promise.all([
      requisicao('/api/pratos/?page_size=100'),
      requisicao('/api/bebidas/?page_size=100'),
      requisicao('/api/ingredientes/?page_size=100'),
    ])

    pratos.value = resultados(dadosPratos)
    bebidas.value = resultados(dadosBebidas)
    ingredientes.value = resultados(dadosIngredientes)
  } catch (falha) {
    erro.value = falha.message
  } finally {
    carregando.value = false
  }
}

async function carregarPedidos() {
  carregandoPedidos.value = true
  erroPedidos.value = ''

  try {
    const dados = await requisicao('/api/pedidos/?page_size=100')
    pedidos.value = resultados(dados)
      .filter((pedido) => pedido && pedido.id !== undefined)
      .map((pedido) => ({
        ...pedido,
        itens: Array.isArray(pedido.itens) ? pedido.itens : [],
        novoStatus: pedido.status,
      }))
  } catch (falha) {
    erroPedidos.value = `Não foi possível carregar os pedidos: ${falha.message}`
  } finally {
    carregandoPedidos.value = false
  }
}

async function carregarIngredientes() {
  carregando.value = true
  erro.value = ''

  try {
    const dados = await requisicao('/api/ingredientes/?page_size=100')
    ingredientes.value = resultados(dados)
  } catch (falha) {
    erro.value = `Não foi possível carregar os ingredientes: ${falha.message}`
  } finally {
    carregando.value = false
  }
}
async function sincronizarEstoque() {
  if (!usuario.value || carregando.value || estoqueSincronizando) return

  estoqueSincronizando = true
  try {
    const [dadosIngredientes, dadosBebidas] = await Promise.all([
      requisicao('/api/ingredientes/?page_size=100'),
      requisicao('/api/bebidas/?page_size=100'),
    ])
    ingredientes.value = resultados(dadosIngredientes)
    bebidas.value = resultados(dadosBebidas)
  } catch {
    // A próxima sincronização automática tentará novamente.
  } finally {
    estoqueSincronizando = false
  }
}
async function selecionarAba(nome) {
  aba.value = nome
  mensagem.value = ''
  erro.value = ''
  if (nome === 'pedidos') await carregarPedidos()
  if (nome === 'ingredientes' && usuario.value) await carregarIngredientes()
  if (nome === 'bebidas' && usuario.value) await sincronizarEstoque()
}
async function verificarSessao() {
  carregando.value = true
  try {
    await carregarTokenCSRF()
    const dados = await requisicao('/api/admin/sessao/')
    usuario.value = dados.usuario
    await carregarDados()
  } catch {
    usuario.value = ''
  } finally {
    carregando.value = false
  }
}

async function entrar() {
  erro.value = ''
  mensagem.value = ''
  carregando.value = true

  try {
    await carregarTokenCSRF()
    const dados = await requisicao('/api/admin/login/', {
      method: 'POST',
      body: JSON.stringify({ usuario: nomeLogin.value, senha: senhaLogin.value }),
    })
    usuario.value = dados.usuario
    csrfToken.value = dados.csrfToken
    senhaLogin.value = ''
    await carregarDados()
  } catch (falha) {
    erro.value = falha.message
  } finally {
    carregando.value = false
  }
}

async function sair() {
  try {
    await requisicao('/api/admin/logout/', {
      method: 'POST',
      body: JSON.stringify({}),
    })
  } finally {
    usuario.value = ''
    mensagem.value = ''
    erro.value = ''
  }
}

async function excluirRegistro(tipo, registro) {
  const nomes = {
    prato: 'este prato',
    bebida: 'esta bebida',
    ingrediente: 'este ingrediente',
  }
  const colecoes = {
    prato: { url: '/api/pratos/', registros: pratos },
    bebida: { url: '/api/bebidas/', registros: bebidas },
    ingrediente: { url: '/api/ingredientes/', registros: ingredientes },
  }
  const nome = nomes[tipo]
  const chave = `${tipo}-${registro.id}`

  if (!window.confirm(`Tem certeza que deseja excluir ${nome} "${registro.nome}"? Esta ação não pode ser desfeita.`)) return

  erro.value = ''
  mensagem.value = ''
  excluindo.value = chave

  try {
    await requisicao(`${colecoes[tipo].url}${registro.id}/`, { method: 'DELETE' })
    colecoes[tipo].registros.value = colecoes[tipo].registros.value.filter((item) => item.id !== registro.id)

    if (tipo === 'prato' && formularioPrato.value.id === registro.id) novoPrato()
    if (tipo === 'bebida' && formularioBebida.value.id === registro.id) novaBebida()
    if (tipo === 'ingrediente' && formularioIngrediente.value.id === registro.id) novoIngrediente()

    const nomesSucesso = { prato: 'Prato', bebida: 'Bebida', ingrediente: 'Ingrediente' }
    mensagem.value = tipo === 'bebida' ? 'Bebida excluída com sucesso.' : `${nomesSucesso[tipo]} excluído com sucesso.`
  } catch (falha) {
    erro.value = `Não foi possível excluir ${nome}. Ele pode estar associado a uma receita ou a um pedido. ${falha.message}`
  } finally {
    excluindo.value = ''
  }
}

function editarPrato(prato) {
  formularioPrato.value = {
    id: prato.id,
    nome: prato.nome,
    preco: prato.preco,
    categoria: prato.categoria,
    descricao: prato.descricao || '',
    disponivel: prato.disponivel,
    receitas: (prato.receitas || []).map((item) => ({
      ingrediente: item.ingrediente,
      quantidade_gramas: item.quantidade_gramas,
    })),
  }
  if (formularioPrato.value.receitas.length === 0) {
    formularioPrato.value.receitas.push({ ingrediente: '', quantidade_gramas: '' })
  }
  mensagem.value = ''
}

function adicionarIngrediente() {
  formularioPrato.value.receitas.push({ ingrediente: '', quantidade_gramas: '' })
}

function removerIngrediente(indice) {
  formularioPrato.value.receitas.splice(indice, 1)
}

async function salvarPrato() {
  erro.value = ''
  mensagem.value = ''
  const receitas = formularioPrato.value.receitas
    .filter((item) => item.ingrediente && item.quantidade_gramas)
    .map((item) => ({
      ingrediente: Number(item.ingrediente),
      quantidade_gramas: Number(item.quantidade_gramas),
    }))

  if (receitas.length === 0) {
    erro.value = 'Adicione pelo menos um ingrediente à receita.'
    return
  }

  salvandoPrato.value = true
  const prato = formularioPrato.value

  try {
    const dados = {
      nome: prato.nome,
      preco: Number(prato.preco),
      categoria: prato.categoria,
      descricao: prato.descricao,
      disponivel: prato.disponivel,
      receitas,
    }
    const url = prato.id ? `/api/pratos/${prato.id}/` : '/api/pratos/'
    await requisicao(url, {
      method: prato.id ? 'PATCH' : 'POST',
      body: JSON.stringify(dados),
    })
    await carregarDados()
    novoPrato()
    mensagem.value = 'Prato salvo com sucesso.'
  } catch (falha) {
    erro.value = falha.message
  } finally {
    salvandoPrato.value = false
  }
}

function editarBebida(bebida) {
  formularioBebida.value = { ...bebida }
  mensagem.value = ''
}

async function salvarBebida() {
  erro.value = ''
  mensagem.value = ''
  salvandoBebida.value = true
  const bebida = formularioBebida.value

  try {
    const dados = {
      nome: bebida.nome,
      preco: Number(bebida.preco),
      estoque: Number(bebida.estoque),
      disponivel: Boolean(bebida.disponivel),
    }
    const url = bebida.id ? `/api/bebidas/${bebida.id}/` : '/api/bebidas/'
    await requisicao(url, {
      method: bebida.id ? 'PATCH' : 'POST',
      body: JSON.stringify(dados),
    })
    await carregarDados()
    novaBebida()
    mensagem.value = 'Bebida salva com sucesso.'
  } catch (falha) {
    erro.value = falha.message
  } finally {
    salvandoBebida.value = false
  }
}

function editarIngrediente(ingrediente) {
  formularioIngrediente.value = { ...ingrediente }
  mensagem.value = ''
}

async function salvarIngrediente() {
  erro.value = ''
  mensagem.value = ''
  salvandoIngrediente.value = true
  const ingrediente = formularioIngrediente.value

  try {
    const dados = {
      nome: ingrediente.nome,
      estoque: Number(ingrediente.estoque),
    }
    const url = ingrediente.id ? `/api/ingredientes/${ingrediente.id}/` : '/api/ingredientes/'
    await requisicao(url, {
      method: ingrediente.id ? 'PATCH' : 'POST',
      body: JSON.stringify(dados),
    })
    await carregarDados()
    novoIngrediente()
    mensagem.value = 'Estoque do ingrediente atualizado.'
  } catch (falha) {
    erro.value = falha.message
  } finally {
    salvandoIngrediente.value = false
  }
}
function nomeItemPedido(item) {
  if (item.prato) {
    const idPrato = typeof item.prato === 'object' ? item.prato.id : item.prato
    return pratos.value.find((prato) => Number(prato.id) === Number(idPrato))?.nome || `Prato #${idPrato}`
  }

  const idBebida = typeof item.bebida === 'object' ? item.bebida.id : item.bebida
  return bebidas.value.find((bebida) => Number(bebida.id) === Number(idBebida))?.nome || `Bebida #${idBebida}`
}

function totalPedido(pedido) {
  return pedido.itens.reduce((total, item) => total + Number(item.preco_unitario) * item.quantidade, 0)
}

function formatarPreco(valor) {
  return Number(valor || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

function nomeStatus(status) {
  return statusPedidos.find((item) => item.valor === status)?.nome || status
}

async function salvarStatus(pedido) {
  erro.value = ''
  mensagem.value = ''

  try {
    await requisicao(`/api/pedidos/${pedido.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ status: pedido.novoStatus }),
    })
    pedido.status = pedido.novoStatus
    await sincronizarEstoque()
    mensagem.value = `Status do pedido #${pedido.id} atualizado para ${nomeStatus(pedido.status)}.`
  } catch (falha) {
    pedido.novoStatus = pedido.status
    erro.value = falha.message
  }
}

novoPrato()
novaBebida()
novoIngrediente()
onMounted(() => {
  verificarSessao()
  intervaloEstoque = window.setInterval(() => {
    if (aba.value === 'ingredientes' || aba.value === 'bebidas') sincronizarEstoque()
  }, 5000)
})

onUnmounted(() => {
  if (intervaloEstoque) window.clearInterval(intervaloEstoque)
})
</script>

<template>
  <main v-if="!usuario" class="admin-login-pagina">
    <RouterLink class="admin-voltar" to="/">← Voltar para a pastelaria</RouterLink>
    <form class="admin-login" @submit.prevent="entrar">
      <span class="admin-selo">P</span>
      <p class="admin-legenda">PASTEL MANIA</p>
      <h1>Área administrativa</h1>
      <p>Entre com uma conta de funcionário do Django.</p>

      <label for="usuario-admin">Usuário</label>
      <input id="usuario-admin" v-model="nomeLogin" autocomplete="username" required />

      <label for="senha-admin">Senha</label>
      <input id="senha-admin" v-model="senhaLogin" type="password" autocomplete="current-password" required />

      <p v-if="erro" class="admin-mensagem erro-admin" role="alert">{{ erro }}</p>
      <button class="botao admin-botao" type="submit" :disabled="carregando">
        {{ carregando ? 'Aguarde...' : 'Entrar' }}
      </button>
    </form>
  </main>

  <main v-else class="pagina-admin">
    <header class="admin-cabecalho">
      <div>
        <p class="admin-legenda">PASTEL MANIA</p>
        <h1>Painel administrativo</h1>
        <p>Conectado como {{ usuario }}</p>
      </div>
      <div class="admin-acoes-topo">
        <RouterLink class="admin-voltar" to="/">Voltar à loja</RouterLink>
        <button class="botao-sair" type="button" @click="sair">Sair</button>
      </div>
    </header>

    <nav class="admin-abas" aria-label="Seções administrativas">
      <button :class="{ selecionada: aba === 'pratos' }" type="button" @click="selecionarAba('pratos')">Pratos</button>
      <button :class="{ selecionada: aba === 'ingredientes' }" type="button" @click="selecionarAba('ingredientes')">Ingredientes</button>
      <button :class="{ selecionada: aba === 'bebidas' }" type="button" @click="selecionarAba('bebidas')">Bebidas</button>
      <button :class="{ selecionada: aba === 'pedidos' }" type="button" @click="selecionarAba('pedidos')">Pedidos</button>
    </nav>

    <p v-if="carregando && aba !== 'pedidos'" class="admin-mensagem">Carregando dados...</p>
    <p v-if="erro" class="admin-mensagem erro-admin" role="alert">{{ erro }}</p>
    <p v-if="mensagem" class="admin-mensagem sucesso-admin" role="status">{{ mensagem }}</p>
    <p v-if="aba === 'ingredientes' || aba === 'bebidas'" class="admin-ajuda-estoque">Estoque sincronizado automaticamente enquanto esta aba estiver aberta.</p>

    <section v-if="aba === 'pratos' && !carregando" class="admin-layout">
      <div class="admin-lista">
        <div class="admin-titulo-lista">
          <h2>Pratos cadastrados</h2>
          <select v-model="filtroDisponibilidade" class="admin-filtro-disponibilidade" aria-label="Filtrar pratos por disponibilidade">
            <option value="todos">Todos</option>
            <option value="disponiveis">Disponíveis</option>
            <option value="indisponiveis">Indisponíveis</option>
          </select>
          <button class="botao botao-pequeno" type="button" @click="novoPrato">Novo prato</button>
        </div>
        <article v-for="prato in pratosFiltrados" :key="prato.id" class="admin-registro">
          <div>
            <strong>{{ prato.nome }}</strong>
            <span>{{ prato.categoria }} · {{ prato.disponivel ? 'Disponível' : 'Indisponível' }}</span>
          </div>
          <div class="admin-acoes-registro">
            <button class="botao-editar" type="button" @click="editarPrato(prato)">Editar</button>
            <button
              class="botao-excluir"
              type="button"
              :disabled="excluindo === 'prato-' + prato.id"
              @click="excluirRegistro('prato', prato)"
            >
              {{ excluindo === 'prato-' + prato.id ? 'Excluindo...' : 'Excluir' }}
            </button>
          </div>
        </article>
        <p v-if="pratosFiltrados.length === 0" class="admin-vazio">Nenhum prato corresponde a este filtro.</p>
      </div>

      <form class="admin-formulario" @submit.prevent="salvarPrato">
        <h2>{{ formularioPrato.id ? 'Editar prato' : 'Cadastrar prato' }}</h2>
        <label for="prato-nome">Nome</label>
        <input id="prato-nome" v-model="formularioPrato.nome" required />

        <div class="admin-campos-duplos">
          <div>
            <label for="prato-preco">Preço (R$)</label>
            <input id="prato-preco" v-model="formularioPrato.preco" type="number" min="0.01" step="0.01" required />
          </div>
          <div>
            <label for="prato-categoria">Categoria</label>
            <select id="prato-categoria" v-model="formularioPrato.categoria">
              <option value="tradicional">Tradicional</option>
              <option value="especial">Especial</option>
              <option value="doce">Doce</option>
              <option value="vegetariano">Vegetariano</option>
            </select>
          </div>
        </div>

        <label for="prato-descricao">Descrição</label>
        <textarea id="prato-descricao" v-model="formularioPrato.descricao" rows="3"></textarea>
        <label class="admin-checkbox"><input v-model="formularioPrato.disponivel" type="checkbox" /> Disponível para pedidos</label>

        <div class="admin-receita-titulo">
          <div>
            <h3>Receita e ingredientes</h3>
            <p>Informe a quantidade usada em cada pastel, em gramas.</p>
          </div>
          <button class="botao-editar" type="button" @click="adicionarIngrediente">+ Ingrediente</button>
        </div>
        <div v-for="(item, indice) in formularioPrato.receitas" :key="indice" class="admin-receita-linha">
          <select v-model="item.ingrediente" aria-label="Ingrediente" required>
            <option value="">Escolha um ingrediente</option>
            <option v-for="ingrediente in ingredientes" :key="ingrediente.id" :value="ingrediente.id">
              {{ ingrediente.nome }} ({{ ingrediente.estoque }} g)
            </option>
          </select>
          <input v-model="item.quantidade_gramas" type="number" min="0.01" step="0.01" placeholder="g por prato" aria-label="Quantidade em gramas" required />
          <button class="botao-remover" type="button" aria-label="Remover ingrediente" @click="removerIngrediente(indice)">×</button>
        </div>

        <div class="admin-botoes-formulario">
          <button class="botao botao-salvar" type="submit" :disabled="salvandoPrato">
            {{ salvandoPrato ? 'Salvando...' : 'Salvar prato' }}
          </button>
          <button class="botao-cancelar" type="button" @click="novoPrato">Limpar formulário</button>
        </div>
      </form>
    </section>

    <section v-if="aba === 'ingredientes' && !carregando" class="admin-layout">
      <div class="admin-lista">
        <div class="admin-titulo-lista">
          <h2>Ingredientes cadastrados</h2>
          <button class="botao botao-pequeno" type="button" @click="novoIngrediente">Novo ingrediente</button>
        </div>
        <article v-for="ingrediente in ingredientes" :key="ingrediente.id" class="admin-registro">
          <div>
            <strong>{{ ingrediente.nome }}</strong>
            <span>{{ ingrediente.estoque }} g em estoque</span>
          </div>
          <div class="admin-acoes-registro">
            <button class="botao-editar" type="button" @click="editarIngrediente(ingrediente)">Editar estoque</button>
            <button
              class="botao-excluir"
              type="button"
              :disabled="excluindo === 'ingrediente-' + ingrediente.id"
              @click="excluirRegistro('ingrediente', ingrediente)"
            >
              {{ excluindo === 'ingrediente-' + ingrediente.id ? 'Excluindo...' : 'Excluir' }}
            </button>
          </div>
        </article>
        <p v-if="ingredientes.length === 0" class="admin-vazio">Nenhum ingrediente cadastrado.</p>
      </div>

      <form class="admin-formulario" @submit.prevent="salvarIngrediente">
        <h2>{{ formularioIngrediente.id ? 'Atualizar ingrediente' : 'Cadastrar ingrediente' }}</h2>
        <label for="ingrediente-nome">Nome</label>
        <input id="ingrediente-nome" v-model="formularioIngrediente.nome" required />
        <label for="ingrediente-estoque">Estoque disponível (g)</label>
        <input id="ingrediente-estoque" v-model="formularioIngrediente.estoque" type="number" min="0" step="0.01" required />
        <p class="admin-ajuda-estoque">O estoque é informado em gramas e usado para controlar a disponibilidade dos pratos.</p>
        <div class="admin-botoes-formulario">
          <button class="botao botao-salvar" type="submit" :disabled="salvandoIngrediente">
            {{ salvandoIngrediente ? 'Salvando...' : 'Salvar ingrediente' }}
          </button>
          <button class="botao-cancelar" type="button" @click="novoIngrediente">Limpar formulário</button>
        </div>
      </form>
    </section>
    <section v-if="aba === 'bebidas' && !carregando" class="admin-layout">
      <div class="admin-lista">
        <div class="admin-titulo-lista">
          <h2>Bebidas cadastradas</h2>
          <button class="botao botao-pequeno" type="button" @click="novaBebida">Nova bebida</button>
        </div>
        <article v-for="bebida in bebidas" :key="bebida.id" class="admin-registro">
          <div>
            <strong>{{ bebida.nome }}</strong>
            <span>{{ bebida.estoque }} em estoque · {{ bebida.disponivel ? 'Disponível' : 'Indisponível' }}</span>
          </div>
          <div class="admin-acoes-registro">
            <button class="botao-editar" type="button" @click="editarBebida(bebida)">Editar</button>
            <button
              class="botao-excluir"
              type="button"
              :disabled="excluindo === 'bebida-' + bebida.id"
              @click="excluirRegistro('bebida', bebida)"
            >
              {{ excluindo === 'bebida-' + bebida.id ? 'Excluindo...' : 'Excluir' }}
            </button>
          </div>
        </article>
      </div>

      <form class="admin-formulario" @submit.prevent="salvarBebida">
        <h2>{{ formularioBebida.id ? 'Editar bebida' : 'Cadastrar bebida' }}</h2>
        <label for="bebida-nome">Nome</label>
        <input id="bebida-nome" v-model="formularioBebida.nome" required />
        <label for="bebida-preco">Preço (R$)</label>
        <input id="bebida-preco" v-model="formularioBebida.preco" type="number" min="0.01" step="0.01" required />
        <label for="bebida-estoque">Unidades em estoque</label>
        <input id="bebida-estoque" v-model="formularioBebida.estoque" type="number" min="0" step="1" required />
        <label class="admin-checkbox"><input v-model="formularioBebida.disponivel" type="checkbox" /> Disponível para pedidos</label>
        <div class="admin-botoes-formulario">
          <button class="botao botao-salvar" type="submit" :disabled="salvandoBebida">
            {{ salvandoBebida ? 'Salvando...' : 'Salvar bebida' }}
          </button>
          <button class="botao-cancelar" type="button" @click="novaBebida">Limpar formulário</button>
        </div>
      </form>
    </section>

    <section v-if="aba === 'pedidos'" class="admin-pedidos">
      <div class="admin-titulo-lista">
        <div>
          <h2>Pedidos recebidos</h2>
          <p class="admin-ajuda-estoque">{{ pedidos.length }} {{ pedidos.length === 1 ? 'pedido no total' : 'pedidos no total' }}</p>
        </div>
        <button class="botao-editar" type="button" :disabled="carregandoPedidos" @click="carregarPedidos">
          {{ carregandoPedidos ? 'Atualizando...' : 'Atualizar lista' }}
        </button>
      </div>

      <p v-if="carregandoPedidos" class="admin-mensagem" role="status">Buscando pedidos na API...</p>
      <div v-else-if="erroPedidos" class="admin-mensagem erro-admin" role="alert">
        <p>{{ erroPedidos }}</p>
        <div class="admin-acoes-topo">
          <button class="botao-editar" type="button" @click="carregarPedidos">Tentar novamente</button>
          <a class="admin-voltar" href="/api/pedidos/?page_size=100" target="_blank" rel="noreferrer">Ver resposta da API</a>
        </div>
      </div>
      <template v-else>
        <p v-if="pedidos.length === 0" class="admin-vazio">Ainda não há pedidos registrados.</p>
        <template v-else>
          <nav class="filtros-pedidos" aria-label="Filtrar pedidos por status">
            <button
              v-for="filtro in opcoesFiltroPedidos"
              :key="filtro.valor"
              type="button"
              :class="['filtro-pedido', { selecionado: filtroPedidos === filtro.valor }]"
              :aria-pressed="filtroPedidos === filtro.valor"
              @click="filtroPedidos = filtro.valor"
            >
              {{ filtro.nome }} <span>{{ contarPedidos(filtro.valor) }}</span>
            </button>
          </nav>
          <p v-if="pedidosFiltrados.length === 0" class="admin-vazio">Nenhum pedido nesta situação.</p>
          <article
            v-for="pedido in pedidosFiltrados"
            :key="pedido.id"
            class="admin-pedido"
          >
            <div class="admin-pedido-topo">
              <div>
                <strong>Pedido #{{ pedido.id }}</strong>
                <span>{{ pedido.data ? new Date(pedido.data).toLocaleString('pt-BR') : 'Data não informada' }}</span>
              </div>
              <strong>{{ formatarPreco(totalPedido(pedido)) }}</strong>
            </div>
            <ul v-if="pedido.itens.length">
              <li v-for="item in pedido.itens" :key="item.id">
                {{ item.quantidade }} × {{ nomeItemPedido(item) }} — {{ formatarPreco(Number(item.preco_unitario) * item.quantidade) }}
              </li>
            </ul>
            <p v-else class="admin-vazio">Este pedido não possui itens informados.</p>
            <div class="admin-status-pedido">
              <span :class="['pedido-status', `pedido-status-${pedido.status}`]">{{ nomeStatus(pedido.status) }}</span>
              <select v-model="pedido.novoStatus" :aria-label="`Novo status do pedido ${pedido.id}`">
                <option v-for="status in statusPedidos" :key="status.valor" :value="status.valor">{{ status.nome }}</option>
              </select>
              <button class="botao-editar" type="button" :disabled="pedido.novoStatus === pedido.status" @click="salvarStatus(pedido)">Salvar status</button>
              <small v-if="pedido.estoque_baixado">Estoque baixado</small>
            </div>
          </article>
        </template>
      </template>
    </section>
  </main>
</template>









