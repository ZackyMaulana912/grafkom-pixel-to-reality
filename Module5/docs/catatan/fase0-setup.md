# Fase 0: Setup repo, venv, toolchain, dan baseline

Tujuan fase ini: bahan dari dosen masuk git apa adanya, semua kode dosen dijalankan di Mac saya sebelum diubah sedikit pun, AR app dicek di browser headless, dan versi library dikunci.

## Toolchain (Lab 1 no 1)

Dicatat 2 November 2026.

| Komponen | Versi |
|---|---|
| Komputer | Mac model Mac17,2, chip Apple M5 (arm64) |
| OS | macOS 27.0.1 (build 26A434) |
| Python | 3.11.8 (pyenv), di `.venv` milik `Module5/Source` |
| NumPy | 2.4.6 |
| pygltflib | 1.16.5 (hanya untuk `make_temple_glb.py`) |
| matplotlib | 3.11.2 (hanya untuk gambar README, bukan untuk hitungan) |
| Playwright | 1.64.1, dengan Chrome Headless Shell 156.0.8078.4 (hanya untuk `verify_ar_app.py`) |
| Browser untuk menguji AR app | belum diisi, saya isi sendiri saat Fase 5 |
| HP untuk uji AR | belum diisi, saya isi sendiri saat Fase 5 |

## Langkah dan buktinya

1. **Folder Modul 5 dibuka di `.gitignore` root.** Baris `/Module5/` saya buang dan diganti satu pola baru, `Module5/Source/data/pusaka_capture/*.ppm`. Gambar PPM itu selalu bisa dibuat ulang oleh `capture.py`, sedangkan `poses.json` di folder yang sama tetap di-commit.
2. **Yang tidak boleh masuk git terbukti tidak masuk** (`git check-ignore -v`):
   - file panduan pribadi saya di `Module5/` tertangkap `.git/info/exclude`. Namanya sempat tidak cocok dengan pola di sana, jadi saya ganti dulu sebelum folder ini dibuka;
   - `Module5/Module5_EN.pdf` tertangkap `.gitignore` root (`Module*/*.pdf`);
   - `data/pusaka_capture/view_000.ppm` tertangkap pola PPM yang baru;
   - `Source/out/` tertangkap `Source/.gitignore` bawaan starter;
   - `Source/.venv/` tertangkap `.venv/`;
   - `poses.json` dan `pusaka_temple.glb` **tidak** tertangkap, dan memang harus ikut di-commit.
3. **Commit pertama berisi starter apa adanya** (`a522d3c`, 22 file). Semua pekerjaan saya nanti bisa dilihat dengan `git diff a522d3c`.
4. **Kode dosen dijalankan sebelum diubah:**

   ```
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python ray_generator.py
   .venv/bin/python volume_render.py
   .venv/bin/python capture.py
   .venv/bin/python fit_nerf_toy.py
   .venv/bin/python nerf_bug.py
   .venv/bin/python tests.py
   ```

   Semua selesai dengan exit 0. Hasilnya dibandingkan dengan PDF:

   | Yang dicek | PDF | Mac saya |
   |---|---|---|
   | E1, arah ray | `(0.800, -0.000, -1.000)`, dinormalisasi `(0.625, -0.000, -0.781)` | sama persis |
   | E2, bobot | `0.500 / 0.250 / 0.250`, background `0.000`, jumlah `1.000` | sama persis |
   | E2, warna akhir | `(0.500, 0.250, 0.250)` | sama persis |
   | `fit_nerf_toy.py`, MSE latih | `0.13714 / 0.02095 / 0.01390 / 0.01083 / 0.00912` | sama persis |
   | `fit_nerf_toy.py`, PSNR | view latih 20.69 dB, novel 22.5 derajat 14.44 dB | sama persis |
   | `nerf_bug.py`, 2 view | latih 21.03 dB, novel 190 derajat 9.30 dB | sama persis |
   | `nerf_bug.py`, 8 view | latih 19.49 dB, novel 190 derajat 12.02 dB, selisih +2.71 dB | sama persis |
   | `tests.py` | `ALL CHECKS PASSED (17 ok)` | sama |
   | Selisih gradien terburuk | sekitar `3e-11` | `4.89e-11` |
   | Waktu `tests.py` | sekitar 10 detik (README starter) | 5.7 detik |

   Selisih gradien `4.89e-11` tetap jauh di bawah ambang `1e-6`. Angka `3e-11` di PDF tidak bisa saya dapatkan, jadi yang saya pakai di laporan adalah angka dari run saya sendiri.

5. **`capture.py` menulis ulang `poses.json` dengan isi yang sama, tapi bentuk filenya beda.** `git diff --stat` menunjukkan 220 baris berubah, padahal yang benar-benar beda hanya digit terakhir beberapa angka (contoh `2.121320343559643` menjadi `2.1213203435596424`). Selisih angka terbesar `4.4e-16`, sedangkan kunci lainnya sama persis. Penyebab semua baris ikut berubah: file dari dosen memakai akhiran baris Windows (CRLF) di 220 dari 220 baris, sedangkan hasil generate di Mac memakai LF. `hotspots.json` juga begitu (95 dari 95 baris CRLF). Isinya sama persis kalau CR dibuang. `.glb` hasil `make_temple_glb.py` identik byte per byte dengan yang dari dosen (sha256 `71f19e78...bdbc98`). Ketiga file dikembalikan dengan `git checkout`. Karena itu, test `poses.json` nanti membandingkan angka dengan toleransi, bukan membandingkan isi file.

6. **Baseline AR app di browser headless.** Saya unduh Playwright dan Chromium atas izin saya sendiri, lalu menjalankan:

   ```
   cd ar_app
   ../.venv/bin/python -m http.server 8743 --bind 127.0.0.1
   ../.venv/bin/python verify_ar_app.py http://127.0.0.1:8743
   ```

   Hasilnya `ALL CHECKS PASSED (10 ok)`. Server hanya terbuka untuk komputer ini dan langsung dimatikan, port 8743 kembali bebas. Script ini menimpa `screenshots/m5_ar_overview.png`, jadi file itu dikembalikan dengan `git checkout`.

   Satu baris berbeda dari PDF: target quiz tercetak `'Tubuh Candi'`, sedangkan PDF menulis `'Panel Relief'`. Ini wajar, karena `app.js` memilih target quiz secara acak (`Math.random`), jadi namanya bisa beda tiap kali dijalankan.

7. **Versi library dikunci.** `requirements.txt` sekarang memakai `==` sesuai isi `.venv`, termasuk library pendukung yang ikut terpasang. Komentar yang merujuk file yang tidak ada di zip (`Module5_EN.tex` dan `../../figures/make_figures_m5.py`) saya buang. Playwright saya pisah ke `requirements-verify.txt`, supaya `pip install -r requirements.txt` tetap ringan. Kedua file sudah saya pasang di venv sementara yang baru: `pip check` bersih, dan daftar paketnya identik dengan `.venv`.

## Temuan tambahan saat membaca dan menjalankan starter

Hasil ini didapat dari run di salinan sementara, jadi starter tidak diubah. Semuanya baru akan ditangani di Fase 3.

- **Satu dari enam voxel yang dicek gradiennya tidak pernah dilewati ray.** Gradiennya nol, baik dari rumus maupun dari finite difference, jadi voxel itu lolos dengan sendirinya tanpa menguji apa pun.
- **Gradien sigma salah saat alpha sangat kecil (di bawah `1e-8`).** Rumusnya memulihkan `T` dengan `weights / clip(alpha, 1e-8)`, jadi untuk alpha sekecil itu nilai `T` keliru. Saat `sigma_raw` di test digeser -18, selisih relatifnya sekitar 200%, dan saat digeser -22 menjadi 330%. Test tetap lolos karena selisih mutlaknya hanya sekitar `1e-9`, jauh di bawah ambang `1e-6`. Di training sungguhan (8 view, 800 iterasi) `sigma_raw` terendah -4.49 dan tidak ada satu pun dari 81.920 sampel yang alpha-nya di bawah `1e-8`. Jadi ini celah di test, bukan bug yang mengubah hasil.
- **Kolom alpha yang dicetak `volume_render.py` diketik tetap** (`alphas_shown = [0.5, 0.5, 1.0]`), bukan diambil dari hasil hitungan. Kolom bobot dan warnanya memang dihitung.
