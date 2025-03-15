import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import VueApexCharts from 'vue3-apexcharts'

// Opret og monter Vue-applikation
const app = createApp(App)
app.use(store)
app.use(router)
app.use(VueApexCharts)
app.mount('#app')
