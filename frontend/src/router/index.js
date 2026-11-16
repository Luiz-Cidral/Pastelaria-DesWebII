import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CardapioView from '../views/CardapioView.vue'
import AdminView from '../views/AdminView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', component: HomeView },
    { path: '/cardapio', component: CardapioView },
    { path: '/admin', component: AdminView },
  ],
  scrollBehavior(to) {
    return to.hash ? { el: to.hash } : { top: 0 }
  },
})

export default router
