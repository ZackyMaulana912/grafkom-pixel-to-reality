# Fase 3: Renderer from-scratch dan gradien (Lab 2 no 1 dan 2)

Fase ini dikerjakan dalam beberapa commit. Catatan ini bertambah setiap commit.

## 1. Satu konvensi kamera dan pixel (K12)

### Masalah di starter

Starter punya dua cara mengubah pixel menjadi ray yang tidak dijelaskan di mana pun:

- `pixel_to_camera_dir(u, v)` memakai `(u, v)` apa adanya;
- `generate_rays` (untuk satu gambar penuh) memakai pusat pixel, yaitu `kolom + 0,5` dan `baris + 0,5`.

Selain itu, `nerf_toy.py` punya salinan `generate_rays` sendiri, walaupun komentarnya menyebut memakai konvensi `ray_generator.py`. Hasil keduanya kebetulan sama, tetapi kalau salah satu diubah, yang lain tidak ikut berubah, dan tidak ada test yang akan tahu.

### Yang saya ubah

**`ray_generator.py` saya tulis ulang** dengan konvensi yang dipatok sekali di bagian atas file:

- ruang kamera mengikuti OpenGL dan Modul 3: +x ke kanan, +y ke atas, kamera menghadap -z;
- `(u, v)` adalah koordinat gambar yang **kontinu**: `u` ke kanan, `v` ke bawah, sehingga y diberi tanda minus;
- pixel di kolom `col`, baris `row` menempati kotak `[col, col + 1) × [row, row + 1)`, jadi pusatnya `(col + 0,5; row + 0,5)`.

Sekarang hanya ada **satu rumus**. `pixel_to_camera_dir` menerima `(u, v)` persis seperti diberikan, dan bisa menerima angka tunggal maupun array. `generate_rays` tidak lagi punya rumus sendiri: ia memanggil `pixel_to_camera_dir` dengan koordinat pusat setiap pixel. Jadi setengah pixel tadi bukan lagi perbedaan diam-diam, melainkan aturan yang tertulis: E1 dan `my_ray.py` memberi titik kontinu, sedangkan gambar penuh menembak lewat pusat pixel, seperti nerfstudio.

**`nerf_toy.generate_rays` tidak lagi punya salinan.** Fungsinya tinggal menghitung focal length dari sudut pandang (`focal_from_fov`, fungsi baru di `ray_generator.py`), lalu memanggil `ray_generator.generate_rays`.

**`volume_render.py` saya tulis ulang.** Transmittance sekarang dihitung sebagai perkalian berantai `1, (1 - α₁), (1 - α₁)(1 - α₂), ...`. Elemen terakhirnya adalah sisa untuk background, yang saya tulis `T(N+1)` (lihat Studi Pendahuluan Q2(b)). Kolom alpha yang dicetak sekarang dihitung dari σ dan δ, bukan lagi diketik tetap seperti di starter.

### Bukti bahwa hasilnya tidak berubah

Penulisan ulang ini tidak boleh mengubah angka. Saya bandingkan versi baru dengan versi starter dari commit sebelumnya, pada 300 kasus acak (focal length, principal point, pixel, putaran kamera, ukuran gambar, alpha, dan warna):

| Yang dibandingkan | Selisih terbesar |
|---|---|
| `pixel_to_camera_dir` | 0 |
| `generate_rays` (origin dan arah) | 0 |
| `nerf_toy.generate_rays` | 0 |
| bobot, transmittance, sisa background | 0 |
| warna hasil komposit | `2,2e-16` |

Selisih `2,2e-16` hanya urutan penjumlahan yang berbeda, karena warna sekarang dihitung dengan perkalian matriks. Angka itu adalah satu langkah pembulatan terkecil di sekitar 1.

Output semua script tetap sama persis dengan Fase 0:
- E1 dan E2 sama;
- MSE latih `0.13714 / 0.02095 / 0.01390 / 0.01083 / 0.00912`;
- PSNR `20.69 / 14.44` dB;
- perbandingan 2 vs 8 view `9.30 / 12.02` dB, selisih `+2.71`;
- ray saya tetap `(-0.17634, -0.34145, -0.92321)`.

### Test baru: `test_ray_convention` (7 check, total 34 ok)

- origin setiap ray sama dengan posisi kamera;
- untuk 20 kamera acak, ray versi gambar penuh di kolom `col`, baris `row` sama dengan ray versi tunggal di `(col + 0,5; row + 0,5)`, dengan selisih terbesar di bawah `1e-12`;
- ray yang diproyeksikan balik dengan rumus Modul 3 jatuh tepat di pusat pixelnya;
- `nerf_toy.generate_rays` identik dengan `ray_generator.generate_rays`;
- alpha E2 yang dihitung dari σ dan δ memang `(0,5; 0,5; 1,0)`.

Supaya terbukti test ini bisa gagal, saya merusak kode dengan sengaja di salinan sementara:

| Kerusakan | Hasil test |
|---|---|
| `generate_rays` kembali memakai `col` tanpa `+ 0,5` | gagal: selisih `0.0217` |
| `nerf_toy` memakai principal point yang bergeser setengah pixel | gagal: selisih `0.416` |
