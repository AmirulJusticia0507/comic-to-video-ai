# Database Schema (NeonDB / PostgreSQL)

Sistem menggunakan database PostgreSQL di NeonDB dengan ORM **SQLAlchemy** dan migrasi **Alembic**.

## Entity Relationship Diagram (ERD) Text Representation

```text
[USERS] 1 ──── < [PROJECTS] 1 ──── < [COMIC_PANELS] 1 ──── < [RENDER_JOBS]
```

---

## Skema Tabel

### 1. `users`
Menyimpan informasi identitas dan kuota pengguna.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key, Default: `gen_random_uuid()` | ID Unik User |
| `email` | VARCHAR(255) | Unique, Not Null | Email pendaftaran |
| `hashed_password` | VARCHAR(255) | Not Null | Password terenkripsi |
| `credits` | INTEGER | Default: `10` | Sisa kredit/kuota generasi |
| `created_at` | TIMESTAMPTZ | Default: `NOW()` | Waktu dibuat |

---

### 2. `projects`
Mewakili satu sesi pengerjaan komik yang bisa terdiri dari beberapa panel.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key | ID Unik Proyek |
| `user_id` | UUID | Foreign Key (`users.id`) | Pemilik Proyek |
| `title` | VARCHAR(255) | Not Null | Judul komik/proyek |
| `status` | VARCHAR(50) | Default: `'draft'` | Status: `draft`, `processing`, `completed` |
| `created_at` | TIMESTAMPTZ | Default: `NOW()` | Waktu dibuat |

---

### 3. `comic_panels`
Menyimpan panel-panel gambar dari komik yang diunggah.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key | ID Unik Panel |
| `project_id` | UUID | Foreign Key (`projects.id`) | Proyek terkait |
| `image_url` | TEXT | Not Null | URL Gambar di S3/R2 |
| `panel_order` | INTEGER | Not Null | Urutan panel dalam komik |
| `motion_prompt` | TEXT | Nullable | Deskripsi gerakan animasi untuk AI |
| `created_at` | TIMESTAMPTZ | Default: `NOW()` | Waktu dibuat |

---

### 4. `render_jobs`
Mencatat antrean dan status pengerjaan video animasi oleh AI Worker.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key | ID Unik Job |
| `panel_id` | UUID | Foreign Key (`comic_panels.id`) | Panel komik yang di-render |
| `status` | VARCHAR(50) | Default: `'PENDING'` | Status: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED` |
| `progress` | INTEGER | Default: `0` | Persentase progres (0-100) |
| `video_url` | TEXT | Nullable | URL Hasil Video Animasi |
| `error_message` | TEXT | Nullable | Pesan error jika gagal |
| `created_at` | TIMESTAMPTZ | Default: `NOW()` | Waktu job masuk |
| `updated_at` | TIMESTAMPTZ | Default: `NOW()` | Waktu perubahan terakhir |

---

## Konvensi Enum (case-sensitive)
- `projects.status`: lowercase — `draft`, `processing`, `completed`
- `render_jobs.status`: UPPERCASE — `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`

---

## Indeks & Constraint
| Nama | Tabel | Kolom | Jenis |
| :--- | :--- | :--- | :--- |
| `uq_users_email` | `users` | `email` | Unique constraint |
| `ix_projects_user_id` | `projects` | `user_id` | Index (FK) |
| `ix_comic_panels_project_id` | `comic_panels` | `project_id` | Index (FK) |
| `uq_comic_panels_project_order` | `comic_panels` | `(project_id, panel_order)` | Unique constraint |
| `ix_render_jobs_panel_id` | `render_jobs` | `panel_id` | Index (FK) |

PostgreSQL tidak otomatis membuat indeks untuk kolom foreign key. Ketiga indeks FK di atas dibuat eksplisit agar lookup relasi, pemeriksaan kepemilikan, dan operasi cascade tidak melakukan sequential scan pada tabel anak. Constraint gabungan pada panel juga mencegah dua panel dalam proyek yang sama memiliki `panel_order` identik.

---

## Catatan Implementasi
- Semua PK memakai `gen_random_uuid()` sebagai server default (built-in PostgreSQL 13+, tanpa ekstensi tambahan; didukung NeonDB).
- `users.credits` = kuota generasi; 1 kredit dipotong per panel saat `POST /api/v1/generations/render` (HTTP 402 bila kurang).
- `render_jobs.updated_at` diperbarui otomatis setiap ada perubahan status/progres.
