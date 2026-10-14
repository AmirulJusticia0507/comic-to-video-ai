# Troubleshooting Docker Desktop — WSL Integration

Dokumen ini mencatat penanganan error Docker Desktop di Windows saat integrasi WSL gagal:

- `WSL integration with distro 'Ubuntu' unexpectedly stopped. Do you want to restart it?`
- `running wsl distro proxy in Ubuntu distro: exit status 1`

## Ringkasan Masalah

Error ini muncul ketika Docker Desktop gagal menjalankan proses proxy di dalam distro WSL (biasanya `Ubuntu`). Penyebab umum:

- WSL / kernel WSL usang atau macet.
- Data Docker Desktop korup (settings, `docker-desktop` distro).
- Docker Desktop kurang kompatibel dengan versi WSL terpasang.
- Distro `Ubuntu` bermasalah (langka bila `wsl -d Ubuntu -- echo ok` berhasil).

## Diagnostik Awal

Jalankan perintah berikut dari PowerShell:

```powershell
wsl --shutdown
wsl --update
wsl --version
wsl -l -v
wsl -d Ubuntu -- echo ok
```

### Hasil pada kasus ini

```
WSL version: 3.0.3.0
Kernel version: 6.18.54.1-1

  NAME              STATE           VERSION
* Ubuntu            Running         2
  docker-desktop    Stopped         2

wsl -d Ubuntu -- echo ok
ok
```

Kesimpulan: distro `Ubuntu` **sehat**. `docker-desktop` berstatus `Stopped` adalah normal ketika Docker Desktop belum dijalankan. Artinya masalah ada di sisi Docker Desktop, bukan WSL.

## Langkah Perbaikan (urut, dari paling ringan)

### 1. Restart total WSL + Docker Desktop

```powershell
wsl --shutdown
```

Tutup Docker Desktop dari system tray, lalu buka kembali.

### 2. Update WSL

```powershell
wsl --update
wsl --version
```

Bug ini kadang berasal dari kernel WSL usang.

### 3. Toggle WSL Integration

Docker Desktop → **Settings → Resources → WSL Integration**:
1. Matikan toggle `Ubuntu`, klik **Apply**.
2. Nyalakan kembali toggle `Ubuntu`, klik **Apply**.
3. **Restart** Docker Desktop.

### 4. Update Docker Desktop

Versi WSL yang baru kadang tidak kompatibel dengan Docker Desktop lama. Cek **Settings → Updates** atau unduh installer terbaru dari docker.com, lalu restart.

### 5. Purge / Reset Dinilai

Docker Desktop → **Settings → Troubleshoot**:
1. **Clean / Purge data**.
2. **Reset to factory defaults**.

Peringatan: container dan image lokal akan hilang; distro `docker-desktop` dibangun ulang.

### 6. Re-register distro docker

Jika semua langkah di atas gagal:

```powershell
wsl --unregister docker-desktop
```

Lalu buka Docker Desktop kembali; distro akan dibuat otomatis.

### 7. Jika Ubuntu sendiri bermasalah

Hanya bila `wsl -d Ubuntu -- echo ok` gagal:

```powershell
wsl -d Ubuntu
sudo apt update && sudo apt -f install
```

atau restore dari backup `.tar`.

## Catatan

- `docker-desktop` berstatus `Stopped` di `wsl -l -v` bukan indikator error.
- Selalu mulai dari langkah 1–2 sebelum melakukan purge/reset agar data container tidak hilang tanpa perlu.
