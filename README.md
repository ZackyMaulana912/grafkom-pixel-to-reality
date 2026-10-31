# Grafika Komputer: dari Pixel ke Realitas

Zacky Maulana (NIM 20241337034), Praktikum Grafika Komputer, S1 Informatika UMSurabaya, semester 5.

Semua modul memakai satu subjek yang sama: **patung kuda berdiri milik saya sendiri**, di ruangan tempat patung itu berdiri. Subjek ini dibawa bertahap dari modul ke modul. Modul 1 memakai fotonya, Modul 2 denah ruangannya, Modul 3 model 3D ruangan dan patungnya, dan Modul 4 memakai model itu sebagai panggung scene Godot. Setiap modul punya kode di `Source/` dan tulisan di `docs/`, dengan prediksi dan diagnosis yang di-commit sebelum hasilnya diukur.

## Daftar modul

| Modul | Topik | Hasil yang bisa dibuka | Dokumen |
|---|---|---|---|
| [Modul 1](Module1/README.md) | Representasi digital, warna & memori | `Source/report/report.html` (dibuat dengan `make report`) | [laporan](Module1/docs/laporan) |
| [Modul 2](Module2/README.md) | Rendering pipeline & primitif 2D | [denah ruangan di WebGL](https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module2/Source/web/) | [laporan](Module2/docs/laporan) |
| [Modul 3](Module3/README.md) | Transformasi 3D, proyeksi, texture & real-time rendering | [ruangan dan patung di WebGL](https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module3/Source/web/) | [laporan](Module3/docs/laporan) |
| [Modul 4](Module4/README.md) | Animasi, kinematika & game engine | [scene Godot di browser](https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module4/build/web/) | [laporan](Module4/docs/laporan) |

Ringkasan tiap modul:

- **Modul 1.** Angka di file gambar adalah kode sRGB, bukan jumlah cahaya. Downscale foto saya yang menghitung rata-rata di linear light dibandingkan dengan rata-rata kode sRGB yang naif, lalu gamma, dithering, aliasing, dan simulasi buta warna diukur dengan angka.
- **Modul 2.** Rasteriser garis dan segitiga dari nol (aturan top-left, fixed-point) untuk denah ruangan saya, dibandingkan pixel per pixel dengan Three.js.
- **Modul 3.** Transformasi, rasteriser z-buffer, dan ray tracer dari nol untuk model ruangan saya (394 segitiga, texture dari foto saya), lalu disamakan dengan viewer Three.js.
- **Modul 4.** FK, IK, spline, dan quaternion dari nol (standard library Python), rantai kinematik dari lengan saya sendiri, dan scene Godot 4.7.2 dengan kamera spline di sekitar patung, rig lengan saya, dan karakter CC0 yang berjalan tanpa kaki tergelincir.

## Cara menjalankan

Setiap modul berdiri sendiri, dengan lingkungan Python (`.venv`) atau Node-nya sendiri di folder `Source/`:

| Modul | Perintah utama |
|---|---|
| 1 | `cd Module1/Source && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && make data && make test` |
| 2 | `cd Module2/Source && nvm use && npm ci && npm test` |
| 3 | `cd Module3/Source && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python make_model.py && python tests.py` |
| 4 | `cd Module4/Source && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python tests.py`, lalu buka `godot_project/` di Godot 4.7.2 |

Detail, versi yang dipakai, dan baris Verified ada di `Source/README.md` setiap modul. Server lokal untuk halaman web selalu dibuka di `127.0.0.1`.

## Catatan repo

- PDF modul dari dosen tidak di-commit. Bahan awal dari dosen selalu masuk lebih dulu sebagai commit tersendiri, jadi perubahan saya bisa dilihat dengan `git diff` terhadap commit itu.
- Folder `Module5/` belum dikerjakan dan sementara disembunyikan lewat `.gitignore`.
- Halaman GitHub Pages disajikan langsung dari branch `main` (repo memakai `.nojekyll`).
