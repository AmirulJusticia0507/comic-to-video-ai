# AGENTS.md

## Project
Comic-to-Video AI Generator — web app untuk mengonversi gambar komik/manga menjadi video animasi pendek secara otomatis menggunakan AI generative (Image-to-Video). Arsitektur: Asynchronous Job Queue (non-blocking UI).

## Tech Stack
- Frontend: Vue.js 3 (Composition API), Pinia, Vue Router, TailwindCSS, Vite
- Backend: FastAPI (Python 3.11+), Celery + Redis (broker), WebSockets
- Database: NeonDB (Serverless PostgreSQL), ORM SQLAlchemy, migrasi Alembic
- Storage: Cloudflare R2 / AWS S3 (presigned URL upload)
- AI Processing: Fal.ai / Replicate API

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
│   └── src/{assets,components,router,stores,views}
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
6. [-] Projects & Panels API CRUD
7. [DONE] Render endpoint `/api/v1/generations/render` + credits check/deduction (api/generations.py, services/credits.py, core/celery_app.py)
8. [DONE] Celery worker + render task (status updates, retry, stale-job reaper, beat schedule) — workers/render.py
9. [IN PROGRESS] AI service: OpenAI-compatible client against griphubrouter (https://griphubrouter.web.id/v1) — chat_completion + generate_image. generate_video_from_image is a stub (NotImplementedError); image-to-video not yet wired. Config via AI_PROVIDER_BASE_URL / AI_PROVIDER_MODEL.
10. [-] WebSocket `/ws/jobs/{job_id}` + Redis pubsub bridge untuk progress
11. [-] Frontend scaffold (Vite Vue3, Pinia, Router, Tailwind)
12. [-] Frontend views/components: Upload, Progress bar, Video Player
13. [-] Perbaiki dokumentasi (enum casing, pilihan Celery/ARQ, index, webhook)
