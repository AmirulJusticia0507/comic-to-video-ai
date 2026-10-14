# AGENTS.md

## Project
Comic-to-Video AI Generator — web app untuk mengonversi gambar komik/manga menjadi video animasi pendek secara otomatis menggunakan AI generative (Image-to-Video). Arsitektur: Asynchronous Job Queue (non-blocking UI).

## Tech Stack
- Frontend: Vue.js 3 (Composition API), Pinia, Vue Router, TailwindCSS, Vite
- Backend: FastAPI (Python 3.11+), Celery + Redis (broker), WebSockets
- Database: NeonDB (Serverless PostgreSQL), ORM SQLAlchemy, migrasi Alembic
- Storage: Cloudflare R2 / AWS S3 (presigned URL upload)
- AI Processing: OpenAI-compatible client via griphubrouter (https://griphubrouter.web.id/v1) — chat + image generation; Higgsfield Seedance 2.5 SDK — image-to-video (services/video.py)

## Target Repo Structure
```
comic-to-video-ai/
├── backend/
│   ├── app/
│   │   ├── api/        # Endpoint routers (REST & WS)
│   │   ├── core/       # Config, Security (JWT), DB session, Redis client
│   │   ├── models/     # SQLAlchemy models
│   │   ├── schemas/    # Pydantic schemas
│   │   ├── services/   # Integrasi AI & S3/R2
│   │   └── workers/    # Celery tasks
│   ├── alembic/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   └── src/{api,assets,components,composables,router,stores,views}
├── docs/               # architecture_documentation.md, database_schema.md
└── README.md
```

## Database Schema (ref: docs/database_schema.md)
`users 1─< projects 1─< comic_panels 1─< render_jobs`
- Semua PK UUID; `users.credits` default 10 (kuota generasi)
- `render_jobs.status`: PENDING / PROCESSING / COMPLETED / FAILED + `progress` (0-100)
- Index pada FK: `projects.user_id`, `comic_panels.project_id`, `render_jobs.panel_id`

## Conventions
- Tidak menambahkan komentar kode kecuali diminta
- Ikuti pola kode yang sudah ada di repo
- JANGAN commit file `.env` / secrets
- Gunakan enum status sesuai dokumen (proyek: draft/processing/completed; job: PENDING/PROCESSING/COMPLETED/FAILED)

## Workflow (WAJIB)
- **Setiap task yang selesai WAJIB langsung commit + push ke `origin/main`** sebelum pindah ke task berikutnya
- Commit message format: `<task-id>: <deskripsi singkat>` (contoh: `task-3: tambah SQLAlchemy models & migration`)
- Verifikasi dulu (lint/typecheck/test) sebelum commit bila relevan

## Task List (roadmap)
1. [DONE] Backend scaffold (struktur app/, requirements.txt, .env.example, main.py)
2. [DONE] Core: config, JWT security, DB session, Redis client (get_settings factory pattern)
3. [DONE] DB models SQLAlchemy + Alembic migration + index/unique constraint (User, Project, ComicPanel, RenderJob)
4. [DONE] Auth API: register/login + JWT token (email-validator dep)
5. [DONE] Storage service: presigned URL upload S3/R2 + validasi file
6. [DONE] Projects & Panels API CRUD (api/projects.py, api/panels.py, schemas/project.py, schemas/comic_panel.py + wiring main.py)
7. [DONE] Render endpoint `/api/v1/generations/render` + credits check/deduction (api/generations.py, services/credits.py, core/celery_app.py)
8. [DONE] Celery worker + render task (status updates, retry, stale-job reaper, beat schedule) — workers/render.py
9. [DONE] AI service: OpenAI-compatible client via griphubrouter — chat_completion + generate_image (services/ai.py); image-to-video via Higgsfield Seedance 2.5 SDK (services/video.py, dipakai workers/render.py; contoh: backend/examples/higgsfield_seedance.py)
10. [DONE] WebSocket `/ws/jobs/{job_id}` + Redis pubsub bridge untuk progress (api/ws.py, services/job_events.py, schemas/job.py). Auth via query param `?token=` atau header `Authorization: Bearer`. Close codes: 4401 unauthorized, 4400 bad uuid, 4404 job not found / bukan milik user. Payload event: `{type:"job.update", job_id, status, progress, video_url, error_message, updated_at}`. Kirim snapshot saat connect, lalu stream pubsub channel `render_job:{job_id}`; fallback poll DB tiap 2 detik bila Redis pubsub tidak tersedia. Tutup otomatis saat status COMPLETED/FAILED. Client bisa kirim teks `ping` untuk dapat `{"type":"pong"}`
11. [DONE] Frontend scaffold (Vite Vue3, Pinia, Router, Tailwind; api/client.js helper + auth store)
12. [DONE] Frontend views/components: Upload (file via presigned PUT + paste URL fallback, live progress via useJobSocket), ProgressBar, VideoPlayer, Home/Login/Register/Upload/Project. api/uploads.py sudah terdaftar di main.py; useJobSocket pakai `/jobs/{id}` (api/jobs.py, presign video via `/uploads/download-url`) tanpa double `/ws`; route `/projects/:id` + guard auth di router.
13. [-] Perbaiki dokumentasi (enum casing, pilihan Celery/ARQ, index, webhook)
