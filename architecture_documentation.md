# System Architecture & Workflow

Dokumen ini menjelaskan alur kerja data dan arsitektur sistem pengolahan animasi gambar komik.

## 1. High-Level Diagram

```text
┌──────────────┐          REST API          ┌──────────────┐
│  Vue.js FE   │ ─────────────────────────> │  FastAPI BE  │
│              │ <───────────────────────── │              │
└──────────────┘     WebSocket Status       └──────────────┘
       │                                           │
       │ Direct Upload                             │ Dispatch Task
       ▼                                           ▼
┌──────────────┐                            ┌──────────────┐
│ S3 / R2      │                            │ Redis Queue  │
│ Storage      │                            └──────────────┘
└──────────────┘                                   │
       ▲                                           │ Consume
       │                                           ▼
       │ Upload Video                       ┌──────────────┐
       └─────────────────────────────────── │ Celery Worker│
                                            └──────────────┘
                                                   │
                                                   │ API Call
                                                   ▼
                                             ┌──────────────┐
                                             │ AI Engine    │
                                             │ Higgsfield   │
                                             │ (I2V) +      │
                                             │ griphubrouter│
                                             │ (chat/image) │
                                             └──────────────┘
```

> Pilihan worker final untuk implementasi saat ini adalah **Celery + Redis**, bukan ARQ. AI image-to-video memakai **Higgsfield** melalui submit lalu polling `status_url`.

---

## 2. Pipeline Pemrosesan

1. **Upload & Persiapan (User/FE):**
   * Pengguna mengunggah satu atau beberapa panel komik.
   * Gambar diunggah langsung ke S3/R2 melalui *presigned URL* (`POST /api/v1/uploads/presigned-url` → `PUT` langsung ke storage).
   * Pengguna menambahkan deskripsi motion/prompt per panel (opsional).

2. **Inisiasi Job (BE):**
   * FE mengirim payload berisi `panel_ids` dan konfigurasi ke endpoint `/api/v1/generations/render`.
   * Backend memvalidasi kepemilikan panel, mengecek dan memotong **1 kredit per panel** (HTTP 402 bila kredit kurang).
   * FastAPI membuat record `RenderJob` dengan status `PENDING` di NeonDB (satu job per panel).
   * FastAPI mendorong task `comic_video.render_panel` ke **Redis Queue**.
   * Backend mengembalikan HTTP 202 Accepted beserta `job_ids` ke Frontend.
   * Jika enqueue gagal, transaksi di-rollback (job + kredit dikembalikan).

3. **Pemrosesan Asinkron (Worker & AI):**
   * **Celery Worker** mengambil task dari Redis.
   * Worker mengubah status job menjadi `PROCESSING` di NeonDB dan mem-publish event ke Redis pubsub channel `render_job:{job_id}`.
   * Worker memanggil API AI *Image-to-Video* (**Higgsfield**: submit → poll `status_url` sampai selesai) dengan parameter gambar & prompt.
   * Setelah AI mengembalikan hasil render, Worker mengunduh video dan menyimpan kembali ke S3/R2 storage dengan key `videos/{job_id}.mp4`.
   * Worker memperbarui status job di NeonDB menjadi `COMPLETED` dan menyimpan `video_url`.
   * Setiap perubahan status/progres di-publish ke Redis pubsub dengan payload `{type:"job.update", job_id, status, progress, video_url, error_message, updated_at}`.
   * Retry otomatis 3x (backoff) untuk error transient; job yang macet di `PENDING`/`PROCESSING` > 30 menit ditandai `FAILED` oleh stale-job reaper (Celery beat tiap 5 menit).

4. **Real-time Feedback (FE):**
   * Vue.js memantau status melalui WebSocket connection (`/ws/jobs/{job_id}?token=...`, auth via query param atau header `Authorization: Bearer`).
   * Server mengirim snapshot job saat connect, lalu men-stream event pubsub; fallback polling DB tiap 2 detik bila Redis pubsub tidak tersedia. Koneksi ditutup otomatis saat status `COMPLETED`/`FAILED`.
   * Progress bar dan status diperbarui di tampilan Vue secara interaktif.
   * Ketika selesai, video player memuat hasil animasi secara otomatis.

## 3. Keputusan Integrasi Status Video

Backend mengambil status render Higgsfield dengan polling ke `status_url`; aplikasi tidak menyediakan endpoint webhook dari provider video. Pilihan ini menjaga worker dapat berjalan tanpa URL callback publik dan membuat seluruh transisi status tetap dikendalikan oleh task Celery.

WebSocket bukan webhook provider. WebSocket hanya menyalurkan perubahan internal dari Redis pubsub ke frontend melalui `/ws/jobs/{job_id}`. Jika pubsub Redis tidak tersedia, server membaca status dari database setiap 2 detik.

---

## 4. Strategi Penghematan Biaya & Scale

* **Storage (Cloudflare R2):** Digunakan karena tidak membebankan biaya *egress* (download bandwidth) saat streaming video ke user.
* **Serverless Database (NeonDB):** Memungkinkan autoscaling dan zero-cost saat idel jika traffic belum tinggi.
* **Decoupled AI Engine:** Menggunakan griphubrouter untuk chat/image generation dan Higgsfield untuk image-to-video sehingga aplikasi tidak perlu mengelola GPU dedicated.
