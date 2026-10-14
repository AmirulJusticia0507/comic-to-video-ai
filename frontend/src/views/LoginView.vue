<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const data = await api('/auth/login', {
      method: 'POST',
      body: { email: email.value, password: password.value },
    })
    auth.setAuth(data.access_token, { email: email.value })
    router.push('/upload')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <form @submit.prevent="submit" class="bg-white p-8 rounded-lg shadow-md w-full max-w-sm">
      <h1 class="text-2xl font-bold mb-6 text-center">Login</h1>
      <div class="mb-4">
        <label class="block text-sm font-medium mb-1">Email</label>
        <input v-model="email" type="email" required class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div class="mb-4">
        <label class="block text-sm font-medium mb-1">Password</label>
        <input v-model="password" type="password" required class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <p v-if="error" class="text-red-500 text-sm mb-4">{{ error }}</p>
      <button type="submit" :disabled="loading" class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50">
        {{ loading ? 'Logging in...' : 'Login' }}
      </button>
      <p class="text-sm text-center mt-4">
        No account?
        <router-link to="/register" class="text-blue-600 hover:underline">Register</router-link>
      </p>
    </form>
  </div>
</template>
