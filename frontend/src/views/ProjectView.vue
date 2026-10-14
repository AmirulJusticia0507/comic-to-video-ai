<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import JobTracker from '../components/JobTracker.vue'
import UploadForm from '../components/UploadForm.vue'

const route = useRoute()
const auth = useAuthStore()
const projectId = route.params.id

const project = ref(null)
const panels = ref([])
const imageUrls = ref({})
const latestJobByPanel = ref(new Map())
const loading = ref(true)
const error = ref('')
const selected = ref(new Set())
const rendering = ref(false)

const allSelected = computed(() => {
  return panels.value.length > 0 && panels.value.every((p) => selected.value.has(p.id))
})

function toggle(panelId) {
  const next = new Set(selected.value)
  if (next.has(panelId)) next.delete(panelId)
  else next.add(panelId)
  selected.value = next
}

function toggleAll() {
  if (allSelected.value) {
    selected.value = new Set()
  } else {
    selected.value = new Set(panels.value.map((p) => p.id))
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [proj, panelList, jobList] = await Promise.all([
      api(`/projects/${projectId}`),
      api(`/panels?project_id=${projectId}`),
      api(`/jobs?project_id=${projectId}`),
    ])
    project.value = proj
    panels.value = panelList
    resolveImageUrls(panelList)
    const latest = new Map()
    for (const job of jobList) {
      if (!latest.has(job.panel_id)) latest.set(job.panel_id, job)
    }
    latestJobByPanel.value = latest
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function onUploaded() {
  load()
}

function imageSrc(panel) {
  return imageUrls.value[panel.id] || panel.image_url
}

async function resolveImageUrls(list) {
  const entries = await Promise.all(
    list.map(async (panel) => {
      const key = panel.image_url || ''
      if (/^https?:\/\//i.test(key) || /^blob:/i.test(key) || /^data:/i.test(key)) {
        return [panel.id, key]
      }
      try {
        const data = await api(`/uploads/download-url?key=${encodeURIComponent(key)}`)
        return [panel.id, data.url]
      } catch {
        return [panel.id, key]
      }
    }),
  )
  imageUrls.value = Object.fromEntries(entries)
}

async function renderSelected() {
  const panelIds = panels.value.filter((p) => selected.value.has(p.id)).map((p) => p.id)
  if (panelIds.length === 0 || rendering.value) return
  rendering.value = true
  error.value = ''
  try {
    const data = await api('/generations/render', {
      method: 'POST',
      body: { panel_ids: panelIds },
    })
    if (data.credits_remaining != null && auth.user) {
      auth.user = { ...auth.user, credits: data.credits_remaining }
    }
    selected.value = new Set()
    await load()
  } catch (err) {
    error.value = err.message
  } finally {
    rendering.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="app-shell">
    <div v-if="loading" class="text-gray-500">Loading...</div>

    <div v-else-if="error" class="text-red-500">{{ error }}</div>

    <div v-else-if="project" class="mx-auto max-w-5xl">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <router-link to="/" class="text-sm font-medium text-cyan-300 hover:text-cyan-200">&larr; Projects</router-link>
          <h1 class="mt-2 text-3xl font-black tracking-tight">{{ project.title }}</h1>
        </div>
        <button
          class="btn-primary"
          :disabled="rendering || selected.size === 0"
          @click="renderSelected"
        >
          {{ rendering ? 'Rendering...' : `Render ${selected.size} panel(s)` }}
        </button>
      </div>

      <div class="grid gap-6 lg:grid-cols-3">
        <div class="lg:col-span-1">
          <UploadForm
            :project-id="projectId"
            :next-order="panels.length"
            @uploaded="onUploaded"
          />
        </div>

        <div class="lg:col-span-2">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-900">Panels</h2>
            <button
              v-if="panels.length"
              class="text-xs text-blue-600 hover:underline"
              @click="toggleAll"
            >
              {{ allSelected ? 'Deselect all' : 'Select all' }}
            </button>
          </div>

          <p v-if="panels.length === 0" class="text-gray-500">
            No panels yet. Upload your first comic panel.
          </p>

          <div class="space-y-4">
            <div
              v-for="panel in panels"
              :key="panel.id"
              class="surface p-4"
            >
              <div class="flex items-start gap-3">
                <input
                  type="checkbox"
                  class="mt-1 h-4 w-4 accent-blue-600"
                  :checked="selected.has(panel.id)"
                  @change="toggle(panel.id)"
                />
                <img
                  :src="imageSrc(panel)"
                  :alt="`Panel ${panel.panel_order}`"
                  loading="lazy"
                  class="h-24 w-auto rounded border border-gray-200 object-contain"
                />
                <div class="min-w-0 flex-1">
                  <p class="text-xs text-gray-500">Panel #{{ panel.panel_order }}</p>
                  <p v-if="panel.motion_prompt" class="mt-1 truncate text-xs text-gray-600">
                    {{ panel.motion_prompt }}
                  </p>
                  <div v-if="latestJobByPanel.has(panel.id)" class="mt-3">
                    <JobTracker
                      :job-id="latestJobByPanel.get(panel.id).id"
                      :panel-image-url="imageSrc(panel)"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
