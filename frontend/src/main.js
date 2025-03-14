import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// Opret og monter Vue-applikation
createApp(App)
  .use(store)
  .use(router)
  .mount('#app')
