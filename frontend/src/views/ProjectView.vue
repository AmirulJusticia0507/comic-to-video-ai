<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import JobTracker from '../components/JobTracker.vue'
import UploadForm from '../components/UploadForm.vue'

const route = useRoute()
const projectId = route.params.id

const project = ref(null)
const loading = ref(true)
const error = ref('')
const selected = ref(new Set())
const rendering = ref(false)

const panels = computed(() => project.value?.panels ?? [])

const latestJobByPanel = computed(() => {
  const map = new Map()
  for (const panel of panels.value) {
    const jobs = panel.render_jobs ?? panel.jobs ?? []
    const latest = jobs[0]
    if (latest) map.set(panel.id, latest)
  }
  return map
})

const allSelectedRenderable = computed(() => {
  const ids = panels.value.map((p) => p.id)
  return ids.length > 0 && ids.every((id) => selected.value.has(id))
})

function toggle(panelId) {
  const next = new Set(selected.value)
  if (next.has(panelId)) next.delete(panelId)
  else next.add(panelId)
  selected.value = next
}

function toggleAll() {
  if (allSelectedRenderable.value) {
    selected.value = new Set()
  } else {
    selected.value = new Set(panels.value.map((p) => p.id))
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    project.value = await api(`/api/v1/projects/${projectId}`)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function onUploaded() {
  load()
}

async function renderSelected() {
  const panelIds = panels.value
    .filter((p) => selected.value.has(p.id))
    .map((p) => p.id)
  if (panelIds.length === 0 || rendering.value) return
  rendering.value = true
  error.value = ''
  try {
    await api('/api/v1/generations/render', { method: 'POST', body: { panel_ids: panelIds } })
    selected.value = new Set()
    await load()
  } catch (err) {
    error.value = err.message
  } finally {
    rendering.value = false
  }
}

onMounted(() => {
  selected.value = new Set()
  load()
})
</script>

<template>
  <div v-if="loading" class="text-gray-400">Loading...</div>

  <div v-else-if="error" class="text-red-400">{{ error }}</div>

  <div v-else-if="project">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <router-link to="/" class="text-sm text-gray-400 hover:text-gray-200">&larr; Projects</router-link>
        <h1 class="mt-1 text-2xl font-bold">{{ project.title }}</h1>
      </div>
      <button
        class="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="rendering || selected.size === 0"
        @click="renderSelected"
      >
        {{ rendering ? 'Rendering...' : `Render ${selected.size} panel(s)` }}
      </button>
    </div>

    <div class="grid gap-6 lg:grid-cols-3">
      <div class="lg:col-span-1">
        <UploadForm :project-id="projectId" @uploaded="onUploaded" />
      </div>

      <div class="lg:col-span-2">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-200">Panels</h2>
          <button
            v-if="panels.length"
            class="text-xs text-indigo-400 hover:underline"
            @click="toggleAll"
          >
            {{ allSelectedRenderable ? 'Deselect all' : 'Select all' }}
          </button>
        </div>

        <p v-if="panels.length === 0" class="text-gray-400">
          No panels yet. Upload your first comic panel.
        </p>

        <div class="space-y-4">
          <div
            v-for="panel in panels"
            :key="panel.id"
            class="rounded-lg border border-gray-800 bg-gray-900 p-4"
          >
            <div class="flex items-start gap-3">
              <input
                type="checkbox"
                class="mt-1 h-4 w-4 accent-indigo-500"
                :checked="selected.has(panel.id)"
                @change="toggle(panel.id)"
              />
              <img
                :src="panel.image_url"
                :alt="`Panel ${panel.panel_order}`"
                class="h-24 w-auto rounded border border-gray-700 object-contain"
              />
              <div class="min-w-0 flex-1">
                <p class="text-xs text-gray-500">Order {{ panel.panel_order }}</p>
                <p v-if="panel.motion_prompt" class="mt-1 truncate text-xs text-gray-400">
                  {{ panel.motion_prompt }}
                </p>
                <div v-if="latestJobByPanel.has(panel.id)" class="mt-3">
                  <JobTracker
                    :job-id="latestJobByPanel.get(panel.id).id"
                    :panel-image-url="panel.image_url"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
