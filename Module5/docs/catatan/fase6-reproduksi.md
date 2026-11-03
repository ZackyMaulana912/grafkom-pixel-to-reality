# Fase 6: Reproduksi dari clone bersih (Lab 3 no 4, A5)

## 1. Clone bersih dari repo lokal, 4 November 2026

Commit `b3a8b6d` saya clone ke folder sementara, lalu dibuatkan `.venv` baru. Tidak ada file dari laptop yang ikut, termasuk `.venv`, scan mentah, foto asli, dan file panduan pribadi.

```
git clone <repo> cek-bersih && cd cek-bersih/Module5/Source
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip freeze           # sama persis dengan requirements.txt
.venv/bin/python capture.py              # wrote 8 views
(cd ar_app && ../.venv/bin/python make_temple_glb.py)
.venv/bin/python tests.py                # ALL CHECKS PASSED (81 ok), 13,9 detik
.venv/bin/python fit_nerf_toy.py         # training-view PSNR 20.32 dB, novel 22.5 deg 14.85 dB
.venv/bin/python nerf_bug.py             # +2.66 dB, [ok]
.venv/bin/python my_ray.py               # (-0.17634, -0.34145, -0.92321), 22.60 deg
.venv/bin/python -m pip install -r requirements-verify.txt
(cd ar_app && ../.venv/bin/python -m http.server 8745 --bind 127.0.0.1 &)
(cd ar_app && ../.venv/bin/python verify_ar_app.py http://127.0.0.1:8745)   # ALL CHECKS PASSED (17 ok)
```

Semua angka sama dengan repo. `pusaka_temple.glb` yang dibuat ulang identik dengan yang ter-commit. Server hanya dibuka di `127.0.0.1` dan sudah dimatikan. Chromium untuk Playwright diambil dari cache yang sudah terunduh di Fase 0, jadi tidak ada unduhan browser baru.

**Satu masalah yang ditemukan, lalu diperbaiki.** Setelah `capture.py` dan `make_temple_glb.py`, `git status` di clone menunjukkan dua file berubah:
- `ar_app/assets/hotspots.json`: isinya sama persis, hanya akhiran barisnya berubah dari CRLF (file dosen dibuat di Windows) ke LF;
- `data/pusaka_capture/poses.json`: akhiran baris berubah, dan beberapa angka berbeda di digit ke-16. Selisih terbesarnya `4,4e-16`, sama dengan T6.

Sesuai keputusan saya, kedua file sekarang di-commit persis seperti yang dihasilkan script dosen di Mac. Repo dan clone menghasilkan file yang identik byte per byte, jadi setelah langkah resmi Lab 3 no 4, `git status` di clone tetap bersih. Versi asli dosen tetap ada di commit `a522d3c`. Test `poses.json` tetap memakai toleransi `1e-9` (K11), karena di komputer lain digit terakhirnya bisa saja berbeda lagi. Selisih di Mac sekarang 0.

**Yang tidak bisa diulang dari clone saja, dan itu disengaja:**
- `kuda.glb` dibuat dari scan mentah (`ar_app/scan/`, 233 MB). Scan itu dibuat dari foto asli, yang tidak di-commit;
- `amr23.glb` dibuat dari file Blender Sketchfab (235 MB), yang juga tidak di-commit.

Keduanya di-commit sebagai hasil jadi, lengkap dengan script pembuatnya dan checksum sumbernya di `assets/LICENSE.md`. Dari sumber yang sama di laptop saya, script itu menghasilkan GLB yang identik byte per byte. Itu sudah dibuktikan di Fase 5.

## 2. Clone dari GitHub dan uji perangkat

Bagian ini diisi setelah commit ini di-push.
