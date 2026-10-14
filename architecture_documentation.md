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
                                            │ (Fal/Replicate│
                                            └──────────────┘
```

---

## 2. Pipeline Pemrosesan

1. **Upload & Persiapan (User/FE):**
   * Pengguna mengunggah satu atau beberapa panel komik.
   * Gambar diunggah langsung ke S3/R2 melalui *presigned URL* yang diprovide oleh Backend.
   * Pengguna menambahkan deskripsi motion/prompt per panel (opsional).

2. **Inisiasi Job (BE):**
   * FE mengirim payload berisi `panel_ids` dan konfigurasi ke endpoint `/api/v1/generations/render`.
   * FastAPI membuat record `Project` & `RenderJob` dengan status `PENDING` di NeonDB.
   * FastAPI mendorong task ID ke **Redis Queue**.
   * Backend mengembalikan HTTP 202 Accepted beserta `job_id` ke Frontend.

3. **Pemrosesan Asinkron (Worker & AI):**
   * **Celery Worker** mengambil task dari Redis.
   * Worker mengubah status job menjadi `PROCESSING` di NeonDB dan mengirim notifikasi via WebSocket.
   * Worker memanggil API AI *Image-to-Video* (misal: Fal.ai/SVD) dengan parameter gambar & prompt.
   * Setelah AI mengembalikan hasil render, Worker mengunduh video dan menyimpan kembali ke S3/R2 storage.
   * Worker memperbarui status job di NeonDB menjadi `COMPLETED` dan menyimpan `video_url`.

4. **Real-time Feedback (FE):**
   * Vue.js memantau status melalui WebSocket connection (`/ws/jobs/{job_id}`).
   * Progress bar dan status diperbarui di tampilan Vue secara interaktif.
   * Ketika selesai, video player memuat hasil animasi secara otomatis.

---

## 3. Strategi Penghematan Biaya & Scale

* **Storage (Cloudflare R2):** Digunakan karena tidak membebankan biaya *egress* (download bandwidth) saat streaming video ke user.
* **Serverless Database (NeonDB):** Memungkinkan autoscaling dan zero-cost saat idel jika traffic belum tinggi.
* **Decoupled AI Engine:** Menggunakan pihak ketiga (Fal.ai/Replicate) di fase MVP agar tidak perlu membayar sewa GPU dedicated saat server tidak digunakan.