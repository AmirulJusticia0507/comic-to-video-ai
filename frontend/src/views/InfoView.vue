<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pages = {
  privacy: {
    eyebrow: 'Legal',
    title: 'Kebijakan Privasi',
    intro: 'Ringkasan tentang data yang diproses saat Anda memakai Comic Motion Studio.',
    sections: [
      ['Data yang kami proses', 'Kami memproses email akun, password yang telah di-hash, proyek, panel komik, prompt gerakan, status render, serta kredit penggunaan.'],
      ['Penyimpanan dan provider', 'Data akun dan metadata proyek tersimpan di NeonDB. File gambar dan video disimpan pada storage S3/R2. Permintaan generasi dapat dikirim ke griphubrouter dan Higgsfield untuk menjalankan fitur AI.'],
      ['Keamanan', 'Token akses digunakan untuk melindungi akun dan setiap resource diperiksa berdasarkan kepemilikannya. Jangan mengunggah materi yang tidak berhak Anda gunakan.'],
      ['Retensi dan penghapusan', 'Data tetap tersimpan selama akun dan proyek digunakan. Untuk permintaan penghapusan data, hubungi pengelola aplikasi melalui kanal bantuan yang tersedia.'],
    ],
  },
  cookies: {
    eyebrow: 'Preferences',
    title: 'Kebijakan Cookies',
    intro: 'Aplikasi saat ini tidak memakai cookie iklan atau pelacakan pihak ketiga.',
    sections: [
      ['Penyimpanan lokal', 'Token login disimpan pada localStorage agar sesi tetap aktif ketika halaman dimuat ulang. Ini bukan cookie dan dapat dihapus dengan logout atau menghapus data situs di browser.'],
      ['Cache PWA', 'Service worker menyimpan app shell dan aset statis untuk mempercepat pemuatan serta menyediakan pengalaman offline terbatas. Data API dan proses render tetap membutuhkan internet.'],
      ['Kontrol Anda', 'Anda dapat menghapus cache, localStorage, dan instalasi PWA melalui pengaturan situs pada browser kapan saja.'],
    ],
  },
  help: {
    eyebrow: 'Support',
    title: 'Pusat Bantuan',
    intro: 'Panduan cepat dari panel gambar hingga video animasi.',
    sections: [
      ['1. Buat proyek', 'Masuk ke workspace, pilih New project, lalu berikan nama untuk proyek komik Anda.'],
      ['2. Unggah panel', 'Pilih satu atau beberapa gambar JPG, PNG, atau WebP. Ukuran maksimal setiap file adalah 20 MB.'],
      ['3. Tulis arahan gerak', 'Motion prompt dapat menjelaskan gerakan karakter, kamera, pencahayaan, atau suasana yang diinginkan.'],
      ['4. Mulai render', 'Pilih panel lalu tekan Render. Progress akan diperbarui secara real-time sampai video siap diputar.'],
      ['Pemecahan masalah', 'Pastikan backend, Redis, dan Celery worker aktif. Jika render gagal, periksa pesan error job dan konfigurasi provider pada backend.'],
    ],
  },
  about: {
    eyebrow: 'Product',
    title: 'Tentang Comic Motion Studio',
    intro: 'Workspace AI untuk mengubah panel komik statis menjadi klip animasi pendek.',
    sections: [
      ['Cara kerja', 'Frontend Vue berkomunikasi dengan FastAPI. Render diproses secara asynchronous oleh Celery dan Redis agar antarmuka tetap responsif.'],
      ['Teknologi AI', 'griphubrouter menangani kemampuan chat dan image generation, sedangkan Higgsfield menangani proses image-to-video.'],
      ['Status produk', 'Aplikasi masih dalam tahap pengembangan. Hasil AI dapat bervariasi dan sebaiknya ditinjau sebelum dipublikasikan.'],
    ],
  },
}

const page = computed(() => pages[route.name] || pages.about)
</script>

<template>
  <main class="app-shell">
    <div class="mx-auto max-w-3xl py-8 sm:py-16">
      <router-link to="/" class="text-sm font-semibold text-cyan-300 hover:text-cyan-200">← Kembali ke aplikasi</router-link>
      <header class="mt-10">
        <p class="eyebrow">{{ page.eyebrow }}</p>
        <h1 class="mt-4 text-4xl font-black tracking-[-0.035em] sm:text-5xl">{{ page.title }}</h1>
        <p class="mt-5 text-lg leading-8 text-slate-400">{{ page.intro }}</p>
      </header>
      <div class="mt-10 space-y-4">
        <section v-for="section in page.sections" :key="section[0]" class="surface p-6 sm:p-7">
          <h2 class="text-lg font-semibold text-white">{{ section[0] }}</h2>
          <p class="mt-3 leading-7 text-slate-400">{{ section[1] }}</p>
        </section>
      </div>
      <p class="mt-8 text-xs text-slate-600">Terakhir diperbarui: 14 Oktober 2026</p>
    </div>
  </main>
</template>
