<script setup>
import { onBeforeUnmount, ref } from 'vue'
import JSZip from 'jszip'
import { api } from '../api/client'

const props = defineProps({
  projectId: { type: String, required: true },
  nextOrder: { type: Number, default: 0 },
})

const emit = defineEmits(['uploaded'])

const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/webp']
const MAX_SIZE_BYTES = 20 * 1024 * 1024

const files = ref([])
const filePreviews = ref(new Map())
const motionPrompt = ref('')
const uploading = ref(false)
const uploadProgress = ref('')
const error = ref('')
const dragOver = ref(false)
const archive = ref(null)
const archiveInput = ref(null)
const importing = ref(false)
const success = ref('')
const archivePreviews = ref([])
const previewLoading = ref(false)

const PREVIEW_IMAGE_EXTS = ['.png', '.jpg', '.jpeg', '.webp']

function clearArchivePreviews() {
  for (const item of archivePreviews.value) URL.revokeObjectURL(item.url)
  archivePreviews.value = []
}

function clearFilePreviews() {
  for (const url of filePreviews.value.values()) URL.revokeObjectURL(url)
  filePreviews.value.clear()
}

onBeforeUnmount(() => {
  clearFilePreviews()
  clearArchivePreviews()
})

function naturalCompare(a, b) {
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' })
}

async function buildZipPreviews(file) {
  previewLoading.value = true
  try {
    const zip = await JSZip.loadAsync(file)
    const names = Object.keys(zip.files).filter((name) => {
      const lower = name.toLowerCase()
      const base = lower.split('/').pop()
      if (!base || base.startsWith('.') || lower.startsWith('__macosx/')) return false
      const entry = zip.files[name]
      if (entry.dir) return false
      return PREVIEW_IMAGE_EXTS.some((ext) => lower.endsWith(ext))
    })
    names.sort(naturalCompare)
    const limited = names.slice(0, 100)
    const items = []
    for (const name of limited) {
      const blob = await zip.files[name].async('blob')
      if (blob.size > MAX_SIZE_BYTES) continue
      items.push({ name: name.split('/').pop(), url: URL.createObjectURL(blob) })
    }
    archivePreviews.value = items
  } catch {
    archivePreviews.value = []
  } finally {
    previewLoading.value = false
  }
}

function onFileChange(event) {
  error.value = ''
  const selected = Array.from(event.target.files || [])
  if (selected.length) addFiles(selected)
  event.target.value = ''
}

function onDrop(event) {
  dragOver.value = false
  error.value = ''
  const selected = Array.from(event.dataTransfer?.files || [])
  if (selected.length) addFiles(selected)
}

function addFiles(selected) {
  const skipped = []
  for (const item of selected) {
    if (!ALLOWED_TYPES.includes(item.type)) {
      skipped.push(`${item.name}: tipe tidak didukung`)
      continue
    }
    if (item.size > MAX_SIZE_BYTES) {
      skipped.push(`${item.name}: lebih dari 20 MB`)
      continue
    }
    if (files.value.length >= 100) {
      skipped.push(`${item.name}: maks 100 file sekaligus`)
      break
    }
    files.value.push(item)
    filePreviews.value.set(item, URL.createObjectURL(item))
  }
  if (skipped.length) error.value = skipped.join('; ')
}

function removeFile(index) {
  const item = files.value[index]
  URL.revokeObjectURL(filePreviews.value.get(item))
  filePreviews.value.delete(item)
  files.value.splice(index, 1)
}

async function uploadSingle(item, order) {
  const presigned = await api('/uploads/presigned-url', {
    method: 'POST',
    body: { filename: item.name, content_type: item.type },
  })

  const uploadRes = await fetch(presigned.upload_url, {
    method: 'PUT',
    headers: { 'Content-Type': item.type },
    body: item,
  })
  if (!uploadRes.ok) throw new Error(`storage upload failed (${uploadRes.status})`)

  return api('/panels', {
    method: 'POST',
    body: {
      project_id: props.projectId,
      image_url: presigned.key,
      panel_order: order,
      motion_prompt: motionPrompt.value || null,
    },
  })
}

async function submit() {
  if (!files.value.length || uploading.value) return
  uploading.value = true
  error.value = ''
  try {
    let order = props.nextOrder
    const total = files.value.length
    for (let i = 0; i < total; i++) {
      uploadProgress.value = total > 1 ? `Uploading ${i + 1}/${total}...` : 'Uploading...'
      await uploadSingle(files.value[i], order)
      order += 1
    }
    const done = total
    files.value = []
    clearFilePreviews()
    motionPrompt.value = ''
    uploadProgress.value = ''
    success.value = total > 1 ? `Uploaded ${done} panel(s)` : success.value
    emit('uploaded', { count: done })
  } catch (err) {
    error.value = err.message
  } finally {
    uploading.value = false
    uploadProgress.value = ''
  }
}

function onArchiveChange(event) {
  error.value = ''
  success.value = ''
  clearArchivePreviews()
  const selected = event.target.files?.[0] || null
  if (selected) {
    const name = selected.name.toLowerCase()
    if (!name.endsWith('.zip') && !name.endsWith('.rar')) {
      error.value = 'only ZIP and RAR archives are supported'
      archive.value = null
      return
    }
    if (selected.size > 200 * 1024 * 1024) {
      error.value = 'archive must be smaller than 200 MB'
      archive.value = null
      return
    }
    if (name.endsWith('.zip')) buildZipPreviews(selected)
  }
  archive.value = selected
}

async function importArchive() {
  if (!archive.value || importing.value) return
  importing.value = true
  error.value = ''
  success.value = ''
  try {
    const form = new FormData()
    form.append('project_id', props.projectId)
    form.append('archive', archive.value)
    if (motionPrompt.value) form.append('motion_prompt', motionPrompt.value)
    const panels = await api('/panels/import-archive', { method: 'POST', body: form })
    success.value = `Imported ${panels.length} panel(s)`
    archive.value = null
    motionPrompt.value = ''
    clearArchivePreviews()
    if (archiveInput.value) archiveInput.value.value = ''
    emit('uploaded', panels)
  } catch (err) {
    error.value = err.message
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <div class="surface p-5">
    <h3 class="mb-3 text-sm font-semibold text-white">Upload panel</h3>

    <div
      class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors"
      :class="dragOver ? 'border-violet-400 bg-violet-500/10' : 'border-white/15 bg-white/[0.03] hover:border-white/30'"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="onDrop"
      @click="$refs.fileInput.click()"
    >
      <input
        ref="fileInput"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        multiple
        class="hidden"
        @change="onFileChange"
      />
      <p v-if="!files.length" class="text-sm text-gray-500">
        Drag &amp; drop gambar komik di sini, atau klik untuk pilih (bisa banyak sekaligus)
      </p>
      <div v-else class="grid w-full grid-cols-2 gap-3 sm:grid-cols-4">
        <article v-for="(item, index) in files" :key="`${item.name}-${item.size}`" class="overflow-hidden rounded-xl border border-white/10 bg-slate-950/70 text-left">
          <img :src="filePreviews.get(item)" :alt="item.name" class="aspect-square w-full object-cover" />
          <div class="flex items-center gap-2 px-2 py-2">
            <span class="min-w-0 flex-1 truncate text-xs font-medium text-slate-300" :title="item.name">{{ item.name }}</span>
            <button type="button" class="shrink-0 text-xs text-rose-400 hover:text-rose-300" aria-label="Hapus gambar" @click.stop="removeFile(index)">&times;</button>
          </div>
        </article>
      </div>
      <p class="mt-1 text-xs text-gray-400">PNG, JPEG, or WebP — maks 20 MB per gambar, 100 file sekaligus</p>
    </div>

    <label class="mt-3 block text-sm font-semibold text-white" for="motion-prompt">Motion prompt</label>
    <textarea
      id="motion-prompt"
      v-model="motionPrompt"
      rows="3"
      placeholder="Sekali isi saja, berlaku untuk semua gambar (optional)"
      class="field mt-1 resize-none"
    ></textarea>
    <p class="mt-1 text-xs text-slate-500">Satu prompt dipakai untuk semua gambar, baik upload file maupun import arsip.</p>

    <p v-if="error" class="mt-2 text-sm text-red-500">{{ error }}</p>

    <button
      class="btn-primary mt-3 w-full"
      :disabled="!files.length || uploading"
      @click="submit"
    >
      {{ uploading ? uploadProgress || 'Uploading...' : files.length > 1 ? `Upload ${files.length} Panels` : 'Upload Panel' }}
    </button>

    <div class="my-5 flex items-center gap-3 text-xs uppercase tracking-widest text-slate-600"><span class="h-px flex-1 bg-white/10"></span>atau<span class="h-px flex-1 bg-white/10"></span></div>

    <label class="block text-sm font-semibold text-white">Import banyak panel</label>
    <p class="mt-1 text-xs leading-5 text-slate-500">ZIP atau RAR, maks 200 MB. Maks 100 gambar, 20 MB per gambar, total 500 MB. Panel diurutkan berdasarkan nama file.</p>
    <input ref="archiveInput" type="file" accept=".zip,.rar,application/zip,application/vnd.rar" class="mt-3 block w-full text-sm text-slate-400 file:mr-3 file:rounded-lg file:border-0 file:bg-white/10 file:px-3 file:py-2 file:text-slate-200" @change="onArchiveChange" />
    <p v-if="previewLoading" class="mt-2 text-xs text-slate-400">Membaca isi arsip...</p>
    <div v-if="archivePreviews.length" class="mt-3">
      <p class="text-xs font-medium text-slate-300">Preview isi ZIP ({{ archivePreviews.length }} gambar):</p>
      <div class="mt-2 grid max-h-64 grid-cols-4 gap-2 overflow-y-auto rounded-lg border border-white/10 bg-black/20 p-2">
        <figure v-for="item in archivePreviews" :key="item.url" class="overflow-hidden rounded-md bg-white/5">
          <img :src="item.url" :alt="item.name" loading="lazy" class="h-16 w-full object-cover" />
          <figcaption class="truncate px-1 py-0.5 text-[10px] text-slate-400" :title="item.name">{{ item.name }}</figcaption>
        </figure>
      </div>
    </div>
    <p v-else-if="archive && archive.name.toLowerCase().endsWith('.rar')" class="mt-2 text-xs text-slate-500">Preview tidak tersedia untuk RAR — gambar akan tampil setelah import.</p>
    <p v-if="success" class="mt-2 text-sm text-green-500">{{ success }}</p>
    <button class="btn-secondary mt-3 w-full" :disabled="!archive || importing" @click="importArchive">{{ importing ? 'Importing...' : 'Import archive' }}</button>
  </div>
</template>
