import { defineStore } from 'pinia'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'c2v_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem(TOKEN_KEY, token)
    },
    async fetchUser() {
      if (!this.token) return
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${this.token}` },
      })
      if (res.ok) {
        this.user = await res.json()
      } else {
        this.logout()
      }
    },
    async login(email, password) {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'login failed')
      }
      const data = await res.json()
      this.setToken(data.access_token)
      await this.fetchUser()
    },
    async register(email, password) {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'registration failed')
      }
      await this.login(email, password)
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
    },
  },
})
