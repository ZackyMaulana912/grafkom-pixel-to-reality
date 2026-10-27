# Foto subjek Modul 1

Subjek: patung kuda berdiri milik saya sendiri, difoto di dalam rumah dengan iPhone 17 Pro pada 27 Oktober 2026.

| Isi | Keterangan |
|---|---|
| `small/` | 24 foto yang dipakai, 907 × 1612 pixel, sudah diubah ke sRGB dan tanpa metadata (lokasi GPS dibuang). Ini yang masuk repo. |
| `original/` | 28 foto asli 4536 × 8064 dari kamera. **Tidak masuk repo** karena terlalu besar (sekitar 6 sampai 7 MB per file, 104,65 MiB setelah dibuka) dan menyimpan lokasi GPS. |
| `originals.csv` | Data ke-28 foto asli: ukuran, ukuran file, ISO, kecepatan rana, waktu pengambilan, checksum, dan dipakai atau tidak. |
| `checksums.sha256` | Checksum SHA-256 foto asli, sebagai bukti file mana yang dipakai. |
| `excluded.txt` | 4 foto yang tidak dipakai karena blur, beserta alasannya. |
| `keterangan.csv` | Keterangan singkat isi setiap foto, dipakai untuk `data/manifest.csv`. |

## Cara memakai

Dari clone baru, cukup jalankan `make data`. Perintah itu membaca `small/` dan mengisi `data/` serta `data/manifest.csv`. Foto asli tidak diperlukan.

Kalau foto asli tersedia di `original/`, versi kecil bisa dibuat ulang dengan `make photos-small`. Hasilnya identik byte per byte dengan isi `small/` yang ada di repo. Keaslian foto asli bisa dicek dengan:

```
cd photos/original
shasum -a 256 -c ../checksums.sha256
```

Foto asli disimpan oleh pemilik repo dan bisa diberikan kalau diminta.
