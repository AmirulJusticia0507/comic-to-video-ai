import { reactive, ref } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws'

export function useJobSocket(jobId) {
  const auth = useAuthStore()
  const state = reactive({
    status: 'PENDING',
    progress: 0,
    videoUrl: null,
    errorMessage: null,
    connected: false,
  })
  const snapshotLoaded = ref(false)
  let socket = null
  let pollTimer = null

  function applyEvent(event) {
    state.status = event.status ?? state.status
    state.progress = event.progress ?? state.progress
    state.videoUrl = event.video_url ?? state.videoUrl
    state.errorMessage = event.error_message ?? state.errorMessage
  }

  function isTerminal() {
    return state.status === 'COMPLETED' || state.status === 'FAILED'
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  async function pollOnce() {
    try {
      const job = await api(`/jobs/${jobId}`)
      applyEvent({
        status: job.status,
        progress: job.progress,
        video_url: job.video_url,
        error_message: job.error_message,
      })
      if (isTerminal()) stopPolling()
    } catch {
      stopPolling()
    }
  }

  function startPolling() {
    stopPolling()
    pollTimer = setInterval(pollOnce, 2000)
  }

  function connect() {
    const url = `${WS_BASE}/jobs/${jobId}?token=${encodeURIComponent(auth.token)}`
    socket = new WebSocket(url)

    socket.onmessage = (msg) => {
      const data = JSON.parse(msg.data)
      if (data.type === 'pong') return
      applyEvent(data)
      if (isTerminal()) {
        socket?.close()
        stopPolling()
      }
    }

    socket.onopen = () => {
      state.connected = true
    }

    socket.onclose = () => {
      state.connected = false
      if (!isTerminal()) {
        startPolling()
      }
    }

    socket.onerror = () => {
      socket?.close()
    }
  }

  async function start() {
    try {
      const job = await api(`/jobs/${jobId}`)
      applyEvent({
        status: job.status,
        progress: job.progress,
        video_url: job.video_url,
        error_message: job.error_message,
      })
      snapshotLoaded.value = true
      if (isTerminal()) return
    } catch {
      snapshotLoaded.value = true
    }
    connect()
  }

  function disconnect() {
    stopPolling()
    socket?.close()
  }

  return { state, snapshotLoaded, start, disconnect }
}
