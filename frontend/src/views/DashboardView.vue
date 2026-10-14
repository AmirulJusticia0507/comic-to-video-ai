<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const projects = ref([])
const newTitle = ref('')
const loading = ref(true)
const creating = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  try {
    projects.value = await api('/api/v1/projects')
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createProject() {
  if (!newTitle.value.trim() || creating.value) return
  creating.value = true
  error.value = ''
  try {
    await api('/api/v1/projects', { method: 'POST', body: { title: newTitle.value.trim() } })
    newTitle.value = ''
    await load()
  } catch (err) {
    error.value = err.message
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await auth.fetchUser()
  await load()
})
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold">Projects</h1>

    <form class="mb-6 flex gap-2" @submit.prevent="createProject">
      <input
        v-model="newTitle"
        type="text"
        placeholder="New project title"
        class="flex-1 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
      />
      <button
        type="submit"
        class="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-50"
        :disabled="creating || !newTitle.trim()"
      >
        Create
      </button>
    </form>

    <p v-if="error" class="mb-4 text-sm text-red-400">{{ error }}</p>
    <p v-if="loading" class="text-gray-400">Loading...</p>
    <p v-else-if="projects.length === 0" class="text-gray-400">
      No projects yet. Create one to start uploading comic panels.
    </p>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <router-link
        v-for="project in projects"
        :key="project.id"
        :to="`/projects/${project.id}`"
        class="rounded-lg border border-gray-800 bg-gray-900 p-4 transition-colors hover:border-indigo-600"
      >
        <h2 class="truncate font-semibold text-gray-100">{{ project.title }}</h2>
        <p class="mt-1 text-xs uppercase tracking-wide text-gray-500">{{ project.status }}</p>
        <p class="mt-2 text-sm text-gray-400">
          {{ project.panels?.length || 0 }} panel(s)
        </p>
      </router-link>
    </div>
  </div>
</template>
