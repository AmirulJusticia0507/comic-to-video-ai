<script setup>
import { computed, reactive, ref } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { useJobSocket } from '../composables/useJobSocket'
import ProgressBar from '../components/ProgressBar.vue'
import VideoPlayer from '../components/VideoPlayer.vue'

const auth = useAuthStore()

const title = ref('')
const project = ref(null)
const panels = ref([])
const previews = ref({})
const prompts = ref({})
const manualUrl = ref('')
const uploadMode = ref('file')
const selectedFiles = ref([])
const busy = ref(false)
const error = ref('')
const jobIds = ref([])
const trackers = reactive({})
const playUrls = reactive({})

const canRender = computed(() => panels.value.length > 0 && !busy.value)

async function createProject() {
  error.value = ''
  busy.value = true
  try {
    project.value = await api('/projects', { method: 'POST', body: { title: title.value || 'Untitled comic' } })
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

function onFilesPicked(event) {
  selectedFiles.value = Array.from(event.target.files || [])
  previews.value = {}
  selectedFiles.value.forEach((file) => {
    previews.value[file.name] = URL.createObjectURL(file)
  })
}

async function uploadOne(file, order) {
  const presigned = await api('/uploads/presigned-url', {
    method: 'POST',
    body: { filename: file.name, content_type: file.type },
  })
  const put = await fetch(presigned.upload_url, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': file.type },
  })
  if (!put.ok) throw new Error(`upload to storage failed (${put.status})`)
  const panel = await api('/panels', {
    method: 'POST',
    body: {
      project_id: project.value.id,
      image_url: presigned.key,
      panel_order: order,
      motion_prompt: prompts.value[file.name] || null,
    },
  })
  panels.value.push(panel)
}

async function uploadFiles() {
  error.value = ''
  if (!project.value) {
    error.value = 'create a project first'
    return
  }
  busy.value = true
  try {
    let order = panels.value.length
    for (const file of selectedFiles.value) {
      await uploadOne(file, order)
      order += 1
    }
    selectedFiles.value = []
  } catch (e) {
    if (e.status === 404) {
      uploadMode.value = 'url'
      error.value = 'direct upload endpoint is not available yet, paste an image URL instead'
    } else {
      error.value = e.message
    }
  } finally {
    busy.value = false
  }
}

async function addManualPanel() {
  error.value = ''
  if (!project.value) {
    error.value = 'create a project first'
    return
  }
  if (!manualUrl.value) return
  busy.value = true
  try {
    const panel = await api('/panels', {
      method: 'POST',
      body: {
        project_id: project.value.id,
        image_url: manualUrl.value,
        panel_order: panels.value.length,
        motion_prompt: null,
      },
    })
    panels.value.push(panel)
    manualUrl.value = ''
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function render() {
  error.value = ''
  busy.value = true
  try {
    const data = await api('/generations/render', {
      method: 'POST',
      body: { panel_ids: panels.value.map((p) => p.id) },
    })
    jobIds.value = data.job_ids
    auth.user = { ...auth.user, credits: data.credits_remaining }
    for (const jobId of jobIds.value) {
      const tracker = useJobSocket(jobId)
      trackers[jobId] = tracker
      tracker.start().then(() => resolveVideo(jobId))
    }
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function resolveVideo(jobId) {
  const tracker = trackers[jobId]
  const check = async () => {
    const state = tracker?.state
    if (state?.status === 'COMPLETED' && state?.videoUrl && !playUrls[jobId]) {
      try {
        const data = await api(`/uploads/download-url?key=${encodeURIComponent(state.videoUrl)}`)
        playUrls[jobId] = data.url
      } catch {
        playUrls[jobId] = state.videoUrl
      }
    } else if (state?.status !== 'FAILED') {
      setTimeout(check, 2000)
    }
  }
  check()
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-3xl mx-auto space-y-6">
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold">New render</h1>
        <router-link to="/" class="text-blue-600 hover:underline">Projects</router-link>
      </div>

      <p v-if="error" class="bg-red-50 text-red-600 text-sm p-3 rounded">{{ error }}</p>

      <section class="bg-white rounded-lg shadow p-4">
        <h2 class="font-semibold mb-3">1. Project</h2>
        <div v-if="!project" class="flex gap-2">
          <input v-model="title" placeholder="Comic title" class="flex-1 border rounded px-3 py-2" />
          <button @click="createProject" :disabled="busy" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50">
            Create
          </button>
        </div>
        <p v-else class="text-sm text-gray-700">Project: <span class="font-medium">{{ project.title }}</span></p>
      </section>

      <section class="bg-white rounded-lg shadow p-4">
        <h2 class="font-semibold mb-3">2. Panels</h2>
        <div class="flex gap-2 mb-3 text-sm">
          <button @click="uploadMode = 'file'" :class="uploadMode === 'file' ? 'font-bold' : 'text-gray-500'">Upload file</button>
          <span class="text-gray-300">|</span>
          <button @click="uploadMode = 'url'" :class="uploadMode === 'url' ? 'font-bold' : 'text-gray-500'">Paste URL</button>
        </div>

        <div v-if="uploadMode === 'file'" class="space-y-3">
          <input type="file" accept="image/png,image/jpeg,image/webp" multiple @change="onFilesPicked" />
          <div v-for="file in selectedFiles" :key="file.name" class="flex items-center gap-3 border rounded p-2">
            <img v-if="previews[file.name]" :src="previews[file.name]" class="w-16 h-16 object-cover rounded" />
            <div class="flex-1">
              <p class="text-sm font-medium truncate">{{ file.name }}</p>
              <input v-model="prompts[file.name]" placeholder="Motion prompt (optional)" class="w-full text-sm border rounded px-2 py-1 mt-1" />
            </div>
          </div>
          <button @click="uploadFiles" :disabled="busy || selectedFiles.length === 0" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50">
            Upload panels
          </button>
        </div>

        <div v-else class="flex gap-2">
          <input v-model="manualUrl" placeholder="https://... image URL" class="flex-1 border rounded px-3 py-2" />
          <button @click="addManualPanel" :disabled="busy || !manualUrl" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50">
            Add
          </button>
        </div>

        <ul class="mt-4 space-y-2">
          <li v-for="panel in panels" :key="panel.id" class="text-sm border rounded p-2 flex justify-between">
            <span>Panel #{{ panel.panel_order }}</span>
            <span class="text-gray-500 truncate max-w-xs">{{ panel.image_url }}</span>
          </li>
        </ul>
      </section>

      <section class="bg-white rounded-lg shadow p-4">
        <h2 class="font-semibold mb-3">3. Render</h2>
        <button @click="render" :disabled="!canRender" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50">
          Render {{ panels.length }} panel(s)
        </button>

        <div class="mt-4 space-y-3">
          <div v-for="jobId in jobIds" :key="jobId" class="border rounded p-3">
            <div class="flex items-center justify-between mb-2 text-sm">
              <span class="font-medium capitalize">{{ trackers[jobId]?.state.status?.toLowerCase() || 'pending' }}</span>
              <span class="text-gray-500">{{ trackers[jobId]?.state.progress ?? 0 }}%</span>
            </div>
            <ProgressBar :progress="trackers[jobId]?.state.progress ?? 0" class="mb-2" />
            <p v-if="trackers[jobId]?.state.errorMessage" class="text-red-500 text-sm">{{ trackers[jobId].state.errorMessage }}</p>
            <VideoPlayer v-if="playUrls[jobId]" :src="playUrls[jobId]" class="mt-2" />
            <p v-else-if="trackers[jobId]?.state.videoUrl" class="text-xs text-gray-400 mt-2 break-all">{{ trackers[jobId].state.videoUrl }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
