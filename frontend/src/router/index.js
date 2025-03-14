import { createRouter, createWebHistory } from 'vue-router'

// Lazy loading af komponenter for bedre ydelse
const MeterOverview = () => import('../views/MeterOverview.vue')
const ScanMeters = () => import('../views/ScanMeters.vue')
const MeterDetail = () => import('../views/MeterDetail.vue')

const routes = [
  {
    path: '/',
    name: 'Home',
    component: MeterOverview,
    meta: {
      title: 'Måler Oversigt'
    }
  },
  {
    path: '/scan',
    name: 'Scan',
    component: ScanMeters,
    meta: {
      title: 'Søg Efter Nye Målere'
    }
  },
  {
    path: '/meter/:mac',
    name: 'MeterDetail',
    component: MeterDetail,
    props: true,
    meta: {
      title: 'Måler Detaljer'
    }
  },
  // Redirect til forsiden for alle ukendte ruter
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// Opdatering af dokumenttitel baseret på rute
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} | Måler System` : 'Måler System'
  next()
})

export default router
