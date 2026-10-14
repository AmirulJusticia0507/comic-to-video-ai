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
  try {
    projects.value = await api('/projects')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadPanels(projectId) {
  try {
    panelsByProject.value[projectId] = await api(`/panels?project_id=${projectId}`)
  } catch (e) {
    error.value = e.message
  }
}

function logout() {
  auth.logout()
  window.location.href = '/login'
}

onMounted(load)
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-4xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">Projects</h1>
        <div class="flex items-center gap-4">
          <span v-if="auth.user?.credits != null" class="text-sm text-gray-600">{{ auth.user.credits }} credits</span>
          <router-link to="/upload" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            New Project
          </router-link>
          <button @click="logout" class="text-gray-600 hover:underline text-sm">Logout</button>
        </div>
      </div>

      <p v-if="error" class="text-red-500 mb-4 text-sm">{{ error }}</p>
      <p v-if="loading" class="text-gray-500">Loading...</p>
      <p v-else-if="projects.length === 0" class="text-gray-500">No projects yet. Create one to get started.</p>

      <div class="space-y-4">
        <div v-for="project in projects" :key="project.id" class="bg-white rounded-lg shadow p-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold">{{ project.title }}</h2>
              <p class="text-xs text-gray-500 capitalize">{{ project.status }}</p>
            </div>
            <button @click="loadPanels(project.id)" class="text-sm text-blue-600 hover:underline">Show panels</button>
          </div>
          <ul v-if="panelsByProject[project.id]" class="mt-3 space-y-2">
            <li v-for="panel in panelsByProject[project.id]" :key="panel.id" class="text-sm border rounded p-2">
              <span class="font-medium">Panel #{{ panel.panel_order }}</span>
              <span v-if="panel.motion_prompt" class="text-gray-600"> — {{ panel.motion_prompt }}</span>
              <p class="text-xs text-gray-400 truncate">{{ panel.image_url }}</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
