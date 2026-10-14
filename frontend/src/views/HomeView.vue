<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const projects = ref([])
const panelsByProject = ref({})
const loading = ref(true)
const error = ref('')

async function load() {
  try { projects.value = await api('/projects') }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function loadPanels(projectId) {
  try { panelsByProject.value[projectId] = await api(`/panels?project_id=${projectId}`) }
  catch (e) { error.value = e.message }
}

function logout() {
  auth.logout()
  window.location.href = '/login'
}

onMounted(async () => {
  await auth.fetchUser()
  await load()
})
</script>

<template>
  <main class="app-shell">
    <div class="mx-auto max-w-6xl">
      <nav class="mb-14 flex items-center justify-between">
        <div class="flex items-center gap-3"><div class="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 font-black text-slate-950">C</div><div><p class="font-semibold leading-none">Comic Motion</p><p class="mt-1 text-[11px] uppercase tracking-widest text-slate-500">AI Studio</p></div></div>
        <div class="flex items-center gap-3"><span v-if="auth.user?.credits != null" class="status-pill"><span class="mr-2 h-1.5 w-1.5 rounded-full bg-cyan-300"></span>{{ auth.user.credits }} credits</span><button @click="logout" class="btn-secondary">Sign out</button></div>
      </nav>
      <header class="mb-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div><p class="eyebrow">Your workspace</p><h1 class="mt-3 text-4xl font-black tracking-[-0.035em] sm:text-5xl">Bring every panel<br />to life.</h1><p class="mt-4 max-w-xl text-slate-400">Create, direct, and monitor your comic animation projects from one focused workspace.</p></div>
        <router-link to="/upload" class="btn-primary">+ New project</router-link>
      </header>
      <p v-if="error" class="mb-5 rounded-xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{{ error }}</p>
      <div v-if="loading" class="surface grid min-h-48 place-items-center text-slate-400">Loading projects...</div>
      <div v-else-if="projects.length === 0" class="surface grid min-h-64 place-items-center p-8 text-center"><div><div class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-violet-500/15 text-2xl">✦</div><h2 class="mt-5 text-xl font-semibold">Your canvas is empty</h2><p class="mt-2 text-sm text-slate-400">Create your first project and upload a comic panel.</p><router-link to="/upload" class="btn-primary mt-6">Create first project</router-link></div></div>
      <div v-else class="grid gap-5 md:grid-cols-2">
        <article v-for="project in projects" :key="project.id" class="surface group p-5 transition hover:-translate-y-1 hover:border-violet-400/30">
          <div class="flex items-start justify-between gap-4"><div class="min-w-0"><span class="status-pill">{{ project.status }}</span><router-link :to="`/projects/${project.id}`" class="mt-4 block truncate text-xl font-bold tracking-tight text-white transition group-hover:text-violet-300">{{ project.title }}</router-link><p class="mt-2 text-sm text-slate-500">Animation project</p></div><router-link :to="`/projects/${project.id}`" class="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/[0.04] text-lg text-slate-300 transition group-hover:border-violet-400/30 group-hover:bg-violet-500/10">→</router-link></div>
          <div class="mt-6 border-t border-white/10 pt-4"><button @click="loadPanels(project.id)" class="text-xs font-semibold uppercase tracking-wider text-cyan-300 hover:text-cyan-200">{{ panelsByProject[project.id] ? 'Refresh panels' : 'Preview panels' }}</button><ul v-if="panelsByProject[project.id]" class="mt-3 space-y-2"><li v-for="panel in panelsByProject[project.id]" :key="panel.id" class="rounded-xl bg-white/[0.04] px-3 py-2 text-sm"><span class="font-medium">Panel {{ panel.panel_order + 1 }}</span><span v-if="panel.motion_prompt" class="ml-2 text-slate-500">— {{ panel.motion_prompt }}</span></li></ul></div>
        </article>
      </div>
    </div>
  </main>
</template>
