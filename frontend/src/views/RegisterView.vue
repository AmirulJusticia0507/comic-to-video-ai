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
    await api('/auth/register', {
      method: 'POST',
      body: { email: email.value, password: password.value },
    })
    router.push('/login')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="app-shell grid place-items-center">
    <form @submit.prevent="submit" class="surface w-full max-w-md p-7 sm:p-10">
      <div class="mb-8 flex items-center gap-3"><div class="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 font-black text-slate-950">C</div><span class="font-semibold">Comic Motion Studio</span></div>
      <p class="eyebrow">Start creating</p>
      <h1 class="mt-3 text-3xl font-bold tracking-tight">Create your studio account</h1>
      <p class="mt-2 text-sm leading-6 text-slate-400">Your first 10 generation credits are included.</p>
      <div class="mt-8"><label class="mb-2 block text-sm font-medium text-slate-300">Email address</label><input v-model="email" type="email" required autocomplete="email" class="field" placeholder="you@example.com" /></div>
      <div class="mt-5"><label class="mb-2 block text-sm font-medium text-slate-300">Password</label><input v-model="password" type="password" required minlength="8" autocomplete="new-password" class="field" placeholder="Minimum 8 characters" /></div>
      <p v-if="error" class="mt-4 rounded-xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{{ error }}</p>
      <button type="submit" :disabled="loading" class="btn-primary mt-6 w-full">{{ loading ? 'Creating account...' : 'Create account' }}</button>
      <p class="mt-6 text-center text-sm text-slate-500">Already have an account? <router-link to="/login" class="font-semibold text-violet-300 hover:text-violet-200">Sign in</router-link></p>
    </form>
  </main>
</template>
