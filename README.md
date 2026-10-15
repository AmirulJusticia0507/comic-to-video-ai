# Comic-to-Video AI Generator

Sistem berbasis Web untuk mengonversi gambar komik/manga menjadi video animasi pendek secara otomatis menggunakan AI generative (Image-to-Video models).

Aplikasi ini dirancang dengan arsitektur **Asynchronous Job Queue** untuk menangani pemrosesan AI yang intensif tanpa memblokir antarmuka pengguna (*non-blocking UI*).

---

## 🏗️ Tech Stack

* **Frontend:** Vue.js 3 (Composition API), Pinia (State Management), TailwindCSS, Vue Router.
* **Backend:** FastAPI (Python 3.11+), Celery + Redis (Task Worker), WebSockets.
* **Database:** NeonDB (Serverless PostgreSQL).
* **Storage:** Cloudflare R2 / AWS S3 (penyimpan file gambar & video).
* **AI Processing:** griphubrouter (OpenAI-compatible: chat + image generation) / Higgsfield Seedance (Image-to-Video).

---

## 🚀 Quick Start

### Prerequisites

* Python 3.11+
* Node.js 18+
* Redis Server (untuk Celery Broker)
* PostgreSQL / Account NeonDB

---

### 1. Backend Setup (FastAPI)

```bash
# Clone repository
git clone https://github.com/AmirulJusticia0507/comic-to-video-ai.git
cd comic-to-video-ai/backend

# Buat virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Salin environment variables
cp .env.example .env

# Jalankan Database Migration
alembic upgrade head

# Jalankan Server Development FastAPI (dari folder backend/)
uvicorn main:app --reload --port 8000
```

Jalankan juga Celery Worker di terminal terpisah:

```bash
celery -A app.core.celery_app worker --loglevel=info
```

Di Windows wajib tambah `--pool=solo` (pool `prefork` crash dengan
`ValueError` di `fast_trace_task` pada Celery 5.6):

```bash
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

Jalankan juga Celery Beat bila ingin requeue/reaper otomatis tiap 5 menit:

```bash
celery -A app.core.celery_app.celery_app beat --loglevel=info
```

---

### 2. Frontend Setup (Vue.js 3)

```bash
cd ../frontend

# Install dependencies
npm install

# Salin environment variables
cp .env.example .env

# Jalankan Development Server
npm run dev
```

Aplikasi akan berjalan di `http://localhost:5173`.

### 3. MinIO lokal

Jalankan Docker Desktop, lalu dari root repository:

```bash
docker compose up -d minio minio-init
```

MinIO API tersedia di `http://localhost:9100` dan console di `http://localhost:9101`. Login development menggunakan `minioadmin` / `minioadmin`. Service `minio-init` otomatis membuat bucket `comic-videos`.

Gunakan konfigurasi MinIO yang tersedia di `backend/.env.example`, lalu restart backend dan Celery worker setelah mengganti konfigurasi storage.

Redis 7 untuk Celery tersedia pada `localhost:6380` dan dapat dijalankan bersama MinIO:

```bash
docker compose up -d redis minio minio-init
```

---

## ⚙️ Environment Variables (.env)

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql://user:password@ep-cool-site-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
REDIS_URL=redis://localhost:6380/0

SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256

# Storage (S3 / Cloudflare R2)
STORAGE_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
STORAGE_ACCESS_KEY=your_access_key
STORAGE_SECRET_KEY=your_secret_key
STORAGE_BUCKET_NAME=comic-videos

# AI Services (chat + image via griphubrouter)
AI_PROVIDER_API_KEY=your_griphubrouter_key
AI_PROVIDER_BASE_URL=https://griphubrouter.web.id/v1
AI_PROVIDER_MODEL=gemini-3.8-flash
AI_IMAGE_MODEL=gpt-image

# AI Video (Higgsfield image-to-video)
VIDEO_PROVIDER=higgsfield
VIDEO_API_BASE_URL=https://api.higgsfield.ai
VIDEO_API_KEY_ID=
VIDEO_API_KEY_SECRET=your_higgsfield_key_secret
VIDEO_MODEL=alibaba/wan-3.0-prime/image-to-video
```

### Frontend (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws
```

---

## 📁 Struktur Repositori

```text
comic-to-video-ai/
├── architecture_documentation.md  # Arsitektur, antrean, WebSocket, dan polling provider
├── database_schema.md             # Skema, enum, indeks, dan constraint database
├── backend/                   # FastAPI Backend
│   ├── app/
│   │   ├── api/               # Endpoint Routers (REST & WS)
│   │   ├── core/              # Config, Security, DB session
│   │   ├── models/            # SQLAlchemy Data Models
│   │   ├── schemas/           # Pydantic Data Schemas
│   │   ├── services/          # Integrasi AI & S3
│   │   └── workers/           # Celery Async Tasks
│   ├── alembic/               # Migration scripts
│   ├── main.py
│   └── requirements.txt
├── frontend/                  # Vue.js 3 Frontend
│   ├── src/
│   │   ├── assets/
│   │   ├── components/        # UI Components (Uploader, Canvas, Player)
│   │   ├── router/            # Vue Router Config
│   │   ├── stores/            # Pinia Stores (Auth, Jobs, Canvas)
│   │   ├── views/             # Page Views
│   │   └── App.vue
│   └── package.json
└── README.md
```

Status proyek memakai nilai lowercase `draft`, `processing`, dan `completed`. Status render job memakai nilai uppercase `PENDING`, `PROCESSING`, `COMPLETED`, dan `FAILED`. Detail alur Celery serta keputusan polling tanpa webhook dijelaskan di `architecture_documentation.md`.

---

## Import arsip (ZIP / RAR)

Endpoint `POST /api/v1/panels/import-archive` (`multipart/form-data`: `project_id` + `archive`) mengekstrak gambar dari arsip lalu membuat satu `ComicPanel` per gambar. ZIP didukung native via `zipfile`; RAR via `rarfile` + binary eksternal.

Batas aman: arsip maks 200 MB, maks 100 gambar, 20 MB per gambar, total hasil ekstrak 500 MB. Arsip bersarang (nested archive), arsip terenkripsi, path traversal (`../`, absolute path), dan file yang magic bytes-nya bukan PNG/JPEG/WebP ditolak. Panel diurutkan natural berdasarkan nama file.

Kebutuhan binary RAR: di Windows, `C:\Program Files\WinRAR\UnRAR.exe` terdeteksi otomatis. Di production (Linux), install `unrar` (mis. `apt-get install unrar`) sehingga tersedia di `PATH`, atau set `UNRAR_TOOL=/usr/bin/unrar`.

---

## 🛠️ Troubleshooting

### Job macet di `PENDING`, antrean Redis kosong

Urutan yang benar adalah `db.commit()` **sebelum** `send_task`
(`backend/app/api/generations.py`). Versi lama mengirim task sebelum commit,
sehingga worker yang cepat tidak menemukan job di DB, menganggapnya orphan,
dan job tertinggal di `PENDING` permanen. Worker sekarang retry 3x bila job
belum terlihat, dan hanya menandai `orphan` setelah retry habis.

Pulihkan job `PENDING` yang macet (hanya `PENDING` yang `updated_at`-nya
lebih dari 120 detik yang di-requeue; job `FAILED` harus di-render ulang):

```bash
celery -A app.core.celery_app.celery_app call comic_video.requeue_pending_jobs
```

### `Received unregistered task of type 'comic_to_video.render_panel'`

Nama task yang dikirim API harus sama dengan yang didaftarkan worker
(`comic_video.render_panel`, lihat `RENDER_PANEL_TASK` di
`backend/app/core/celery_app.py`). Bila error ini muncul setelah update kode,
**restart API dan worker** — proses Python yang sudah berjalan tidak membaca
kode baru. Cek kolom `origin` di header pesan untuk tahu proses pengirim yang
masih memakai kode lama, lalu `taskkill /PID <pid> /F`.

### Perubahan `.env` tidak berpengaruh

`get_settings()` di-cache (`lru_cache`), jadi restart API dan worker setiap
kali mengubah `backend/.env`.

### `video provider is not configured`

Isi `VIDEO_API_KEY_ID` dan `VIDEO_API_KEY_SECRET` di `backend/.env` dengan
kredensial dari https://console.higgsfield.ai, lalu restart API dan worker.
Uji kredensial dulu tanpa antrean lewat script contoh (baca `HF_KEY` dari
`backend/.env.local` dengan format `key-id:key-secret`):

```bash
python examples\higgsfield_seedance.py
```

`invalid credentials` = key salah; `not_enough_credits` = key valid tapi
kuota habis, top up di console yang sama. Jangan render dari UI sebelum script
contoh berhasil — job yang gagal ikut menandai `FAILED`.

### `missed heartbeat` / `mingle: sync with N nodes`

Ada worker ganda yang hidup dan berebut antrean. Matikan proses Celery yang
tidak dipakai (`Get-Process python` lalu `taskkill`).

---

## 📄 Lisensi

[MIT License](LICENSE)
