<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
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
    await auth.login(email.value, password.value)
    router.push('/upload')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="app-shell grid place-items-center overflow-hidden">
    <div class="grid w-full max-w-5xl overflow-hidden rounded-3xl border border-white/10 bg-slate-950/70 shadow-2xl shadow-violet-950/30 backdrop-blur-xl lg:grid-cols-[1.1fr_.9fr]">
      <section class="relative hidden min-h-[620px] overflow-hidden border-r border-white/10 p-12 lg:flex lg:flex-col lg:justify-between">
        <div class="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-violet-600/30 blur-3xl"></div>
        <div class="relative">
          <div class="mb-12 flex items-center gap-3"><div class="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 font-black text-slate-950">C</div><span class="font-semibold tracking-tight">Comic Motion Studio</span></div>
          <p class="eyebrow">AI animation workspace</p>
          <h1 class="mt-5 max-w-md text-5xl font-black leading-[1.05] tracking-[-0.04em]">Turn still panels into cinematic motion.</h1>
          <p class="mt-6 max-w-md text-base leading-7 text-slate-400">Upload your artwork, direct the movement, and let the render pipeline handle the rest.</p>
        </div>
        <div class="relative grid grid-cols-3 gap-3 text-sm">
          <div v-for="(item, index) in ['Upload', 'Direct', 'Render']" :key="item" class="rounded-2xl border border-white/10 bg-white/[0.04] p-4"><strong class="block text-xl text-white">0{{ index + 1 }}</strong><span class="text-slate-500">{{ item }}</span></div>
        </div>
      </section>
      <form @submit.prevent="submit" class="flex min-h-[620px] flex-col justify-center p-7 sm:p-12">
        <p class="eyebrow">Welcome back</p>
        <h2 class="mt-3 text-3xl font-bold tracking-tight">Sign in to your studio</h2>
        <p class="mt-2 text-sm text-slate-400">Continue building your next animated scene.</p>
        <div class="mt-8"><label class="mb-2 block text-sm font-medium text-slate-300">Email address</label><input v-model="email" type="email" required autocomplete="email" class="field" placeholder="you@example.com" /></div>
        <div class="mt-5"><label class="mb-2 block text-sm font-medium text-slate-300">Password</label><input v-model="password" type="password" required autocomplete="current-password" class="field" placeholder="Enter your password" /></div>
        <p v-if="error" class="mt-4 rounded-xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{{ error }}</p>
        <button type="submit" :disabled="loading" class="btn-primary mt-6 w-full">{{ loading ? 'Logging in...' : 'Login' }}</button>
        <p class="mt-6 text-center text-sm text-slate-500">New to the studio? <router-link to="/register" class="font-semibold text-violet-300 hover:text-violet-200">Create an account</router-link></p>
      </form>
    </div>
  </main>
</template>
