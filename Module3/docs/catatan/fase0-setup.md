# Fase 0: Setup repo, venv, dan toolchain

Tujuan fase ini: bahan dari dosen masuk git apa adanya, gambar acuan dibuat dari kode dosen yang belum diubah, versi library terkunci, dan server lokal hanya bisa dibuka dari laptop saya sendiri.

## Toolchain (Lab 1 no 1)

Dicatat 28 Oktober 2026.

| Komponen | Versi |
|---|---|
| Komputer | Mac model Mac17,2, chip Apple M5 (arm64) |
| OS | macOS 27.0.1 (build 26A434) |
| Python | 3.11.8 (pyenv), di `.venv` milik `Module3/Source` |
| NumPy | 2.4.6, memakai Accelerate (BLAS bawaan macOS) |
| Pillow | 13.0.0 |
| Node | v20.20.2. Tidak dipakai Modul 3, karena server lokalnya `python -m http.server` |
| Three.js | 0.160.0 dari CDN jsdelivr (importmap di `web/index.html`) |
| Browser untuk uji otomatis | Google Chrome 156.0.8078.48, mode tanpa layar (headless) |
| Browser yang saya buka sendiri | diisi setelah saya membuka halamannya (lihat catatan Fase 5) |
| Pemeriksa model independen | Blender 5.2.2 (hanya membuka OBJ, tidak dipakai membuat model) |

## Langkah dan buktinya

1. **Folder Modul 3 dibuka di `.gitignore` root.** Baris `/Module3/` saya buang, sedangkan Modul 4 dan 5 tetap tersembunyi.
2. **Yang tidak boleh masuk git terbukti tidak masuk** (`git check-ignore -v`):
   - file panduan pribadi saya di `Module3/` tertangkap `.git/info/exclude`, yang tidak ikut ter-commit;
   - `Module3/Module3_ID.pdf` tertangkap `.gitignore` root (`Module*/*.pdf`);
   - `Module3/Source/out/...` tertangkap `Module3/Source/.gitignore` bawaan starter (`out/`);
   - `Module3/Source/.venv/` tertangkap `.gitignore` root (`.venv/`).
3. **Commit pertama berisi starter apa adanya.** Isi starter tidak mengandung file sampah (`__MACOSX`, `._*`, `__pycache__`), hanya `.DS_Store` di folder `Module3/` yang sudah di-ignore. Semua pekerjaan saya bisa dilihat dengan `git diff <commit starter>`.
4. **Kode dosen dijalankan sebelum diubah sedikit pun:**

   ```
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt    # numpy 2.4.6, pillow 13.0.0
   .venv/bin/python make_model.py                         # 120 vertex, 180 segitiga, relief.ppm 196.623 B
   .venv/bin/python tests.py                              # 8 OK, ALL CHECKS PASSED
   .venv/bin/python tests.py                              # run kedua, tetap 8 OK
   ```

   Run pertama mencetak `(ref/temple_ref.ppm generated -- commit it)`. **Gambar acuan `ref/temple_ref.ppm` lahir di sini, dari rasteriser dosen yang belum saya sentuh** (keputusan K12). Saya meng-commit-nya bersama `data/pusaka_model.obj` dan `data/relief.ppm` sebelum ada perubahan kode. Jadi kalau tulisan ulang saya nanti identik dengan file ini, artinya hasilnya identik dengan kode dosen.

   Catatan jujur: referensi ini adalah **referensi regresi**, bukan kebenaran independen. Ia hanya membuktikan bahwa kode saya menghasilkan frame yang sama dengan kode dosen. Pembanding independennya adalah ray tracer (Fase 3) dan WebGL (Fase 5).

## Hasil kode dosen di Mac saya

| Perintah | Hasil di Mac | Di PDF |
|---|---|---|
| `worked_example.py` | clip `[5.196 5.196 9.408 11]`, NDC `[0.472 0.472 0.855]`, screen `[589 158]` | sama |
| `raster3d.py --demo-triangle --w 64 --h 64` | 1199 fragment, UV centroid (0,410; 0,337) vs naif (0,500; 0,333) | sama |
| raster vs ray tracer candi 256 × 256 | **PSNR 68,1 dB**, SSIM 1,000, max\|diff\| **28** | PSNR 76,9 dB, max\|diff\| 10 |
| raster vs ray tracer candi 512 × 512 | PSNR 69,8 dB, SSIM 1,000, max\|diff\| 33 | tidak ada |

Hasil raster vs ray tracer di Mac saya **berbeda** dari PDF (dan juga dari run awal di Linux: 76,5 dB, max 10). Angkanya tetap di atas target 60 dB, tapi jelas tidak sama. Penyebabnya saya selidiki di Fase 3, bukan saya tebak di sini.

Dua temuan dari run awal (sebelum Modul 3 dimulai, di komputer lain) juga terbukti ulang di Mac:

- **T5:** `raster3d.py --out out/mymodel.ppm` mencetak `wrote out/mymodel.ppm and out/mymodel.ppm`. Citra depth menimpa citra warna karena nama file tidak mengandung kata "raster".
- **T6:** quick start README starter merender raster 512 dan ray tracer 256, lalu `compare.py` berhenti dengan `size mismatch` (kode keluar 2).

## Mengunci versi library (K6)

Starter menulis `numpy>=1.24` dan `pillow>=10.0`, jadi `pip install` bisa memasang versi apa pun yang lebih baru. Saya menguncinya ke versi yang benar-benar terpasang dan teruji:

```
numpy==2.4.6
pillow==13.0.0
```

Saya buktikan file ini bisa dipasang ulang dari nol di venv baru yang terpisah: `pip freeze` menghasilkan tepat `numpy==2.4.6` dan `pillow==13.0.0`.

Kenapa NumPy 2.4.6 dan bukan versi terbaru: menurut PyPI, NumPy 2.5.4 (terbaru) mensyaratkan Python ≥ 3.12. Di Python 3.11, versi tertinggi yang bisa dipasang adalah 2.4.6 (`pip index versions numpy`). Run awal di Linux memakai Python 3.13, makanya mendapat 2.5.4. Versi di README starter juga 2.4.6. Kalau nanti pindah ke Python 3.12 atau lebih baru, cukup ubah angka di file ini, lalu jalankan ulang `tests.py`.

## Server lokal (K10, T8)

PDF menyuruh `npx serve web`. Ada dua masalah:

1. **Model tidak termuat (T8).** Viewer mengambil `../data/...` dan `../scenes/...`, jadi yang harus dilayani adalah folder `Source/`, bukan `web/`.
2. **Terbuka ke seluruh jaringan.** `serve` dan `python -m http.server` sama-sama mendengarkan di semua antarmuka kalau tidak diberi alamat.

Perintah yang saya pakai, dari `Module3/Source`:

```
.venv/bin/python -m http.server 8000 --bind 127.0.0.1
```

Bukti saat diuji: `lsof` menunjukkan `TCP 127.0.0.1:8000 (LISTEN)`, bukan `*:8000`. `curl` ke `/web/`, `/web/viewer.js`, `/data/pusaka_model.obj`, `/data/mymodel.obj`, dan `/scenes/mymodel.json` semuanya 200. Setelah itu server saya matikan, dan port 8000 kosong lagi. Port 3000 tidak dipakai, karena sudah dipakai program lain di laptop saya.

Tidak perlu Node atau unduhan package apa pun: `http.server` sudah ada di Python.
