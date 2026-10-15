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
git clone https://github.com/your-username/comic-to-video-ai.git
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

---

## ⚙️ Environment Variables (.env)

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql://user:password@ep-cool-site-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
REDIS_URL=redis://localhost:6379/0

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

## 📄 Lisensi

[MIT License](LICENSE)
