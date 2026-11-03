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

## 2. Turunan gradien, ditulis dengan tangan

Catatan jujur: kode `backward_grid` starter sudah saya baca di Fase 0, jadi turunan ini tidak sepenuhnya ditulis "sebelum membaca kode" seperti diminta panduan. Yang saya lakukan: menurunkan rumusnya sendiri dari rumus komposit, sampai ke bentuk yang berbeda dari starter, lalu baru membandingkan keduanya di bagian 3.

### Dari warna pixel ke α

Untuk satu ray dengan N sampel:

```
C = Σ_{i=1..N} T_i α_i c_i + T(N+1) c_bg,      T_i = (1 - α_1)(1 - α_2)...(1 - α_(i-1))
```

Ambil satu sampel k, lalu lihat bagaimana setiap suku bergantung pada α_k:

- **sampel di depan k (i < k):** `T_i` dan `α_i` tidak memuat α_k, jadi turunannya 0;
- **sampel k sendiri:** `T_k α_k c_k`, dan `T_k` tidak memuat α_k, jadi turunannya `T_k c_k`;
- **semua sampel di belakang k (i > k) dan background:** setiap `T_i` memuat tepat satu faktor `(1 - α_k)`, yaitu `T_i = T_k (1 - α_k) P_i`, dengan `P_i` perkalian `(1 - α_j)` untuk `k < j < i`.

Suku-suku di belakang k bisa dikumpulkan menjadi:

```
Σ_{i>k} T_i α_i c_i + T(N+1) c_bg = T_k (1 - α_k) B_k
B_k = Σ_{i>k} P_i α_i c_i + P_(N+1) c_bg
```

`B_k` punya arti yang jelas: **warna yang terlihat dari tepat di belakang sampel k**, yaitu komposit sampel k+1 sampai N di atas background, seolah-olah cahayanya mulai dari penuh. Turunan bagian ini terhadap α_k adalah `-T_k B_k`. Jadi:

```
dC/dα_k = T_k c_k - T_k B_k = T_k (c_k - B_k)
```

Artinya: menaikkan opacity sampel k menukar sedikit "apa yang ada di belakangnya" dengan warnanya sendiri, sebanyak cahaya yang sampai ke situ (`T_k`). Kalau warna sampel k lebih dekat ke target daripada apa yang di belakangnya, opacity-nya akan naik, dan sebaliknya.

`B_k` dihitung dari belakang ke depan dalam satu putaran:

```
B_N = c_bg
B_(k-1) = α_k c_k + (1 - α_k) B_k
```

**Hubungan dengan rumus modul.** Modul menulis `dC/dα_k = T_k c_k - (Σ_{i>k} T_i α_i c_i + T(N+1) c_bg) / (1 - α_k)`. Dari persamaan di atas, pembilangnya sama dengan `T_k (1 - α_k) B_k`, jadi kedua rumus sama persis selama `α_k < 1`. Bedanya, bentuk saya **tidak pernah membagi dengan `1 - α_k`**. Sampel yang benar-benar padat (`α_k = 1`) tidak perlu cabang khusus, dan pitfall 12.4 (lupa menjaga pembagian dengan nol) tidak bisa terjadi.

**Dicek dengan E2** (α = 0,5; 0,5; 1, warna merah, hijau, biru, background hitam):

```
B_3 = (0, 0, 0)
B_2 = 1 × biru + 0 × B_3            = (0; 0; 1)
B_1 = 0,5 × hijau + 0,5 × biru     = (0; 0,5; 0,5)
dC/dα_1 = 1    × (merah - B_1) = (1; -0,5; -0,5)
dC/dα_2 = 0,5  × (hijau - B_2) = (0; 0,5; -0,5)
dC/dα_3 = 0,25 × (biru - B_3)  = (0; 0; 0,25)
```

Finite difference pada `volume_render.composite` memberi `(1, -0.5, -0.5)`, `(0, 0.5, -0.5)`, dan `(0, 0, 0.25)`. Sama persis.

### Dari α ke parameter yang dipelajari

```
α = 1 - exp(-σ δ)            →  dα/dσ = δ exp(-σ δ) = δ (1 - α)
σ = softplus(σ_raw)          →  dσ/dσ_raw = sigmoid(σ_raw)
c = sigmoid(c_raw)           →  dc/dc_raw = c (1 - c)
dC/dc_k = T_k α_k = w_k      (per channel)
```

Dengan gradien loss terhadap warna pixel `g = dL/dC` (vektor 3), rantainya menjadi:

```
dL/dσ_raw (sampel k) = [T_k (c_k - B_k) · g] × δ (1 - α_k) × sigmoid(σ_raw)
dL/dc_raw (sampel k) = w_k g × c_k (1 - c_k)
```

Satu voxel dilewati banyak sampel, dari banyak ray dan banyak view, jadi gradien voxel adalah **jumlah** gradien semua sampel yang jatuh di voxel itu.

## 3. Inti `nerf_toy.py` ditulis ulang

Bagian yang saya tulis ulang: scene analitik, kamera di lingkaran, pengambilan sampel, komposit untuk seluruh gambar, `VoxelGrid`, forward pass, backward pass, dan loop latih. Nilai scene (empat teras candi dan densitasnya), inisialisasi grid, dan cara latihnya sengaja tidak diubah, supaya perubahan angka nanti hanya berasal dari hal yang memang saya ganti.

Yang berubah di `backward_grid`:
- **Starter:** memulihkan `T_k` dengan `weights / clip(alpha, 1e-8)`, lalu memakai rumus modul dengan pembagian `/(1 - α_k)` yang dijepit di `1e-6` dan cabang khusus untuk `α ≥ 1 - 1e-9`.
- **Versi saya:** menghitung `T_k` langsung sebagai perkalian berantai, lalu memakai `T_k (c_k - B_k)` dari bagian 2. Tidak ada pembagian dan tidak ada cabang.

Komentar di `train` juga saya tambah. Langkah latihnya memakai gradien dari `Σ (gambar - target)² / (pixel × view)`, yaitu 3 kali gradien MSE per channel yang dicetak. Learning rate menyerap faktor itu, jadi ini bukan bug, tetapi perlu ditulis supaya angka `lr = 100` tidak membingungkan.

### Bukti 1: di kondisi normal hasilnya sama

| Yang dibandingkan | Selisih versi saya vs starter |
|---|---|
| render analitik, scene, kamera | 0 |
| gambar hasil render grid | 0 |
| gradien warna | 0 |
| gradien density (kondisi test, σ_raw acak di sekitar 0) | `1,7e-16` |
| grid setelah 800 iterasi latih (`fit_nerf_toy.py`) | `2,7e-15` |

MSE akhir `0.009124692865406037` dan PSNR novel view `14.441333111669415` dB sama sampai digit terakhir. Semua script mencetak angka yang sama dengan Fase 0, dan `tests.py` tetap 34 ok dengan selisih gradien `4.89e-11`.

### Bukti 2: di kondisi ekstrem versi starter salah, versi saya benar

Saya geser semua σ_raw di kasus test, lalu membandingkan kedua backward dengan finite difference memakai tiga ukuran langkah (`1e-2`, `1e-3`, `1e-4`) yang hasilnya saling sepakat. Kesalahan diukur relatif terhadap gradien terbesar di grid itu.

| Geseran σ_raw | Rentang α | Kesalahan starter | Kesalahan versi saya |
|---|---|---|---|
| 0 | 0,047 sampai 0,57 | paling besar `4e-08` | paling besar `4e-08` |
| -18 | sampai `7,6e-10` (hampir kosong) | 23% | `7e-05` |
| +30 | `1 - 1,8e-08` (hampir padat) | 300%, **tandanya terbalik** | `9e-05` |

Contoh di geseran +30: finite difference memberi `+4.4000e-08`, versi saya `+4.4000e-08`, starter `-8.7894e-08`. Kalau dipakai melatih, starter akan menggeser voxel itu ke arah yang salah. Penyebabnya:
- **di sisi hampir kosong:** pemulihan `T = w / clip(α, 1e-8)` keliru saat α di bawah `1e-8`;
- **di sisi hampir padat:** `1 - α` di antara `1e-9` dan `1e-6` tidak masuk cabang khusus, tetapi penyebutnya dijepit ke `1e-6`, jadi hasil baginya terlalu kecil. Inilah celah yang dicatat T3 di panduan, dan ternyata memang salah.

Kesalahan versi saya `7e-05` dan `9e-05` adalah batas ketelitian finite difference itu sendiri, bukan kesalahan rumus. Kondisi ekstrem ini tidak pernah muncul saat training di modul ini (σ_raw tetap di antara -4,5 dan 6,6), jadi angka starter di PDF tetap sah. Tetapi test starter tidak akan menangkapnya, karena ia hanya mengecek σ_raw di sekitar 0. Test untuk kedua kondisi ekstrem ini saya tambahkan di commit berikutnya.
