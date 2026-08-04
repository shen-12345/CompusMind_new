import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import router from './router'
import App from './App.vue'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 如果已登录，尝试获取用户信息
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
if (authStore.isLoggedIn) {
  authStore.fetchUser()
}

app.mount('#app')