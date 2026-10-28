# Laporan Modul 2: Rendering Pipeline & Primitif 2D

Zacky Maulana (NIM 20241337034), S1 Informatika UMSurabaya
Praktikum Grafika Komputer

Semua angka di laporan ini berasal dari program yang benar-benar dijalankan. Perintahnya ditulis di setiap bagian, dan detail langkahnya ada di `docs/catatan/`.

**Toolchain (Lab 1 no 1):**

| Komponen | Versi |
|---|---|
| Komputer | Mac17,2, chip Apple M5 |
| OS | macOS 27.0.1 |
| Node | v22.23.4 (`.nvmrc`) |
| npm | 10.9.9 |
| Three.js | 0.160.0 |
| serve | 14.2.6 |
| Browser uji | Chrome 156.0.8078.48 headless, ANGLE Metal |
| Tanggal | 28 Oktober 2026 |

Repo ini menaruh kode modul di `Module2/Source/`, bukan `code/Module2/` seperti tertulis di modul.

---

## 1. Input dan penempatan di pipeline (A1)

**Input.** Patung kuda saya tidak punya denah, jadi saya menelusuri **ruangan tempat patung itu berdiri** (`Source/myplan.json`, skema sama dengan `pusaka_plan.json`). Isinya:

- ruangan 2 × 4 m;
- lemari penyimpanan 4 × 0,4 m dengan 8 pintu di dinding kanan;
- sekat berlubang tempat vas di sisi masuk, sebagai pembagian interior;
- jalan masuk sekitar 0,5 m di pojok kiri;
- alas patung 8 × 30 cm.

Lebar jalan masuk berasal dari perbandingan 1/4, dan letak patung adalah perkiraan. Keduanya ditandai sebagai perkiraan di JSON dan di `docs/denah/README.md`. Hasilnya 14 polyline dan 20 segmen, dengan skala 130 px/m di canvas 800 × 600.

**Satu segmen dinding melewati tujuh tahap** (`node walkthrough.mjs`, dinding belakang):

| Tahap | Angka |
|---|---|
| 1 Application | (0, 4) m → (2, 4) m, kategori `wall` |
| 2 Vertex processing | x = (x_m + 2) × 130, y = 599 − (y_m + 0,3) × 130 → (260, 40) dan (520, 40) |
| 3 Assembly & clipping | satu garis, kedua titik di dalam canvas, tidak ada yang dipotong |
| 4 Rasterisation | Bresenham: Δx = 260, Δy = 0, 261 pixel di baris 40 |
| 5 Fragment shading | warna rata dinding (33,145,140) |
| 6 Per-fragment ops | tanpa depth test dan blending; garis ditulis setelah lantai, jadi garis yang menang |
| 7 Framebuffer | pixel (390,40) = (33,145,140), di atasnya latar (18,18,22), di bawahnya lantai (230,236,245) |

**Kalau satu tahap dilewati:** tanpa tahap 2, angka meter langsung menjadi pixel. Ruangan hanya menjadi kotak 3 × 5 pixel di pojok kiri atas, terbalik (jalan masuk di atas), dan semua detail di bawah 1 m menyusut menjadi titik. Tidak ada error yang muncul, jadi test `worldToScreen` pada titik yang diketahui tetap diperlukan.

## 2. Primitif dari nol dan kecocokan dengan referensi (A2)

Semua primitif di `raster.mjs` ditulis ulang dengan JavaScript polos tanpa package:

- **DDA**: titik ke-k dihitung langsung, tanpa penumpukan galat;
- **Bresenham**: variabel keputusan seperti Contoh E3, berlaku untuk semua oktan;
- **`triangle()`**: fixed-point 1/256 pixel, aturan tepi, dan perbaikan urutan titik otomatis;
- **`triangleNaive()`**, **`barycentric()`**, dan **`fillRect()`** untuk uji sample-centre.

| Uji | Hasil |
|---|---|
| DDA dan Bresenham (2,1) → (9,5) | (2,1) (3,2) (4,2) (5,3) (6,3) (7,4) (8,4) (9,5), dengan D = 1, −5, 3, −3, 5, −1, 7, 1 |
| 8 refleksi garis | mulai dan berakhir tepat di ujungnya, 8-connected, semua pixel ≤ 0,5 dari garis ideal |
| Asterisk 24 jari-jari, R = 110 | \|jarak − R\| terburuk 0,364 px, penyimpangan terbesar 0,491 px |
| Tanda edge E4 | (3,3) = (8,12,8) di dalam; (5,5) dan (1,4) di luar; barycentric P1 = (3/7, 2/7, 2/7) |
| Contoh E1 | aturan pusat 2 × 2; sudut inklusif 3 × 3 |
| `ref/square_fill_ref.ppm` (dari dosen) | 144/144, PSNR inf, max \|diff\| 0 |
| `ref/tri_ref.ppm` dan `ref/tri_t8_ref.ppm` | max \|diff\| = 0 |
| Sweep 1.934 segitiga vs referensi independen | 0 berbeda |

**Asal-usul referensi:** `ref/tri_ref.ppm` yang diminta modul tidak ada di starter. Saya membuatnya di `make_tri_ref.mjs` dengan cara yang sengaja berbeda dari `triangle()`: setiap pixel diuji sendiri, koordinat dikali 2, dan aturannya ditulis literal tanpa trik bias.

**Satu pixel dihitung tangan.** E4, pixel (3,1) dengan pusat (3,5; 1,5):

- E_AB = (6 − 1)(0,5) − (2 − 1)(2,5) = **0**, jadi tepat di edge A → B;
- E_BC = 14 dan E_CA = 14.

Edge A → B punya Δy = +1, jadi menurut rumus modul biasnya 0. Hasilnya 0 + 0 ≥ 0, sehingga pixel ini **menyala**, sama dengan kodenya.

Pembandingnya, pixel (1,2): E_CA = 0 di edge C → A (Δy = −6), biasnya −1, jadi 0 − 1 < 0 dan pixel ini **mati**, juga sama dengan kodenya.

Perbandingan garis dengan starter: 6.725 dari 20.000 segmen acak memberi pixel berbeda, dan setiap perbedaannya kasus seri (dua pixel sama-sama berjarak 0,5). Untuk denah saya dan denah dosen, hasilnya identik.

## 3. Diagnosis dan perbaikan (A3)

**Diagnosis sebelum perbaikan** (`docs/prediksi/diagnosis-celah.md`, di-commit lebih dulu, dari pixel `triangle()` starter):

1. **Persegi 6 × 6 yang dibagi di diagonal.** Dengan "E ≥ 0", pixel (2,2), (3,3), ..., (7,7) tergambar dua kali (6 pixel). Dengan "E > 0", keenam pixel itu menjadi celah. Penyebabnya, pusat pixel tepat di diagonal punya E = 0 di **kedua** segitiga, dan tidak ada aturan pemutus. Contohnya pixel (4,4): E = 21 − 21 = 0 dan 15 − 15 = 0.
2. **Temuan baru: aturan top-left di starter membuang pixel yang jelas di dalam.** Bias −1 hanya benar kalau E bilangan bulat, padahal dengan pusat x + 0,5, E bisa 0,5. Di 1.934 segitiga acak, 34 segitiga kehilangan total 42 pixel, semuanya dengan nilai edge terkecil 0,5. Contohnya (16,0), (4,23), (2,12), pixel (2,14): E = (0,5; 41; 136,5).

**Perbaikan:** vertex dibulatkan ke grid 1/256 pixel. Pusat pixel menjadi 256x + 128, semua E menjadi bilangan bulat, dan bias −1 tepat berarti "E > 0". E dihitung bertambah per pixel (sifat linear Pineda).

**Bukti.** Kelima prediksi di diagnosis tepat:

- persegi once = 36, twice = 0, gaps = 0;
- sweep 0 berbeda;
- referensi max |diff| 0;
- referensi dosen tetap identik;
- mode tanpa aturan tetap 6/6.

Dengan `triangle()` starter, 4 test baru **gagal**. Dengan versi saya, keempatnya lolos.

**Bias 0 dan −1 (§9).** T1 melewati diagonal dari (8,8) ke (2,2): Δy = −6, jadi bias −1. T2 melewati diagonal dari (2,2) ke (8,8): Δy = +6, jadi bias 0. Arahnya berlawanan, sehingga tepat satu segitiga memiliki pixel diagonal, yaitu T2.

**Temuan tambahan.** Dengan y ke bawah dan total > 0, segitiga berjalan searah jarum jam di layar. Rumus modul (Δy > 0, atau Δy = 0 dan Δx < 0) memberikan pixel tepi ke edge **kanan dan bawah**, yaitu cerminan aturan top-left GPU.

Buktinya saya ambil dari WebGL mentah tanpa antialiasing, di GPU Apple M5 dan di SwiftShader (hasil keduanya identik):

- GPU menyalakan (1,2) dan (2,5), sedangkan rumus modul menyalakan (3,1) dan (4,4);
- GPU memberikan diagonal persegi ke T1, rumus modul ke T2.

Keduanya sama-sama rapat tanpa celah. Opsi `fillRule: "gpu"` cocok 144/144 dengan gambar GPU. Default-nya tetap rumus modul, karena referensi dari dosen dibuat dengan rumus itu.

**Perbaikan pitfall: auto-flip winding.** `triangle()` menukar dua vertex kalau total < 0.

| Kasus | Sebelum (starter) | Sesudah |
|---|---|---|
| E4 urutan A, C, B | 0 pixel | 14 pixel, identik dengan urutan A, B, C |
| Lantai `myplan.json` dalam urutan JSON | 0 pixel | 135.200 pixel |

## 4. Render pustaka dan diff pixel (A4)

Viewer Three.js (`web/viewer.mjs`) menggambar `myplan.json` di 800 × 600 dengan `setPixelRatio(1)`. Warna dan `worldToScreen` diambil dari `plan_common.mjs`, file yang sama yang dipakai rasteriser saya.

Dua bug di viewer starter terbukti di Chrome dengan GPU sungguhan:

- **T3, lantai hilang.** `ShapeGeometry` membereskan arah outline sendiri, lalu kamera y-ke-bawah mencerminkan layar sehingga semua segitiga membelakangi kamera dan dibuang. Perbaikannya `side: DoubleSide`.
- **T4, garis di batas dua baris.** Vertex garis ada di koordinat integer, padahal pusat pixel GL ada di +0,5. Akibatnya dua baris masing-masing mendapat 50%, dicampur di kode sRGB: (43,10,53). Perbaikannya, vertex garis digeser +0,5.

| Viewer | Identik | PSNR | SSIM |
|---|---|---|---|
| seperti starter | 71,48% | 6,9 dB | 0,006 |
| hanya T3 diperbaiki | 98,92% | 31,1 dB | 0,997 |
| keduanya diperbaiki | **479.929 / 480.000 (99,985%)** | **52,7 dB** | **1,000** |

**Setiap pixel yang tidak cocok** (`node diff_pixels.mjs out/plan_scratch.ppm plan_three.ppm`):

- **46 pixel** ada di garis diagonal kepala panah. Ini antialiasing MSAA: pixel di garis mendapat 3/4 warna (194,178,33), dan tetangganya 1/4 (77,71,26).
- **25 pixel** ada di ujung atau sambungan garis. Di situ sampel MSAA terbagi antara dua garis, misalnya pojok lemari dan dinding (46,114,139) = 50:50. Rasteriser saya memakai "yang terakhir menang".
- **0 pixel** di garis lurus atau di dalam lantai.

Untuk denah dosen dengan viewer yang sudah diperbaiki: 479.964/480.000 identik, PSNR 56,9 dB, dan semua perbedaannya di ujung atau sambungan.

Modul memperkirakan PSNR "30 sampai 40 dB". Dengan bug T4 PSNR denah saya 31,1 dB, padahal semua garis salah tempat. Karena itu saya menambahkan syarat bahwa kelompok "lainnya" harus 0: dengan bug T4 jumlahnya 5.015.

**Penyimpangan dari PDF.** Modul meminta `plan_three.png`. Saya memakai `plan_three.ppm` dari tombol Export PPM, karena membaca PNG di `compare.mjs` butuh package `pngjs` dan bagian dari-nol tidak boleh memakai package.

## 5. Keputusan forward vs backward (A4)

**Prediksi** (`docs/prediksi/prediksi-forward-backward.md`, di-commit sebelum `bench.mjs` dijalankan):

- forward menang di kedua zoom, sekitar 100 sampai 1000 kali di 1× dan 50 sampai 500 kali di 10×;
- backward hampir sama di 1× dan 10×;
- forward di 10× paling banyak 3 kali forward 1×.

**Masalah pengukuran.** `bench.mjs` bawaan memperlihatkan backward lebih cepat di zoom 10× (73 vs 54 ms, 76 vs 25 ms), seperti angka di PDF. Percobaan terkontrol menunjukkan zoom yang **diukur pertama** selalu lambat, apa pun zoom-nya, karena ikut menanggung pemanasan JIT V8. Saya menambahkan pemanasan, 5 putaran bergantian, dan median.

**Hasil** (3 run, 20 segmen):

| Zoom | Forward | Backward | Rasio |
|---|---|---|---|
| 1× | 0,041 sampai 0,045 ms | 25,33 sampai 25,37 ms | 560 sampai 616 kali |
| 10× | 0,169 sampai 0,173 ms | 25,18 sampai 25,28 ms | 146 sampai 149 kali |

**Rekonsiliasi:**

| Prediksi | Hasil |
|---|---|
| Arah (forward menang) | tepat |
| Rasio di kedua zoom | tepat |
| Backward datar terhadap zoom | tepat |
| Angka absolut | meleset, mesin ini lebih cepat dari perkiraan: 2,6 ns per uji jarak, bukan 5 sampai 30 ns |
| Kenaikan forward di 10× | sedikit meleset: 3,9 kali, bukan paling banyak 3 kali, karena langkah Bresenham naik 10 kali dan hanya separuh waktunya alokasi yang tetap |

**Pilihan: forward** untuk viewer denah pan/zoom. Biayanya mengikuti panjang garis. Backward 25 ms per frame sudah melewati jatah 16,7 ms untuk 60 fps.

**Kondisi yang membalik pilihan ini:**

1. ada efek per pixel (glow, garis tebal berdasarkan jarak, heatmap jarak ke dinding), yang gratis di backward;
2. zoom ekstrem tanpa clipping garis, karena Bresenham tetap menelusuri bagian di luar layar sementara backward tetap 25 ms;
3. target GPU dengan shader per pixel, karena backward menjadi paralel di ribuan core.

## 6. Aksesibilitas (A5)

Legenda memakai ramp viridis 5 langkah, label teks, dan marker berbeda: ● patung, ◆ lemari, ■ dinding, ▲ sekat berlubang, ▼ jalan masuk. Ada toggle deuteranopia, protanopia, dan grayscale. Screenshot keempat tampilan ada di `docs/img/legend_*.png`.

`node cvd_check.mjs` memakai matriks yang dibaca langsung dari `web/index.html` dan ambang 20 dari Modul 1:

| Tampilan | Jarak terkecil (lemari / dinding) |
|---|---|
| normal | 68,2 |
| deuteranopia | 36,9 |
| protanopia | 46,4 |
| grayscale (CSS) | 69,3 |
| kontrol negatif, palet merah-hijau di deuteranopia | 17,7, gagal |

Warna dari screenshot Chrome cocok dengan hitungan Node paling banyak selisih 1 kode. Ini membuktikan dua hal:

- filter SVG menerapkan matriksnya di **linear light**, sama dengan `cvd.py` Modul 1, sehingga angkanya identik;
- filter CSS `grayscale(1)` menghitung langsung pada **kode sRGB**.

Urutan warna legenda saya pilih berdasarkan **di mana benda digambar**. Kontrasnya diukur dengan rasio WCAG: patung di atas lantai terang mendapat warna tergelap (12,8:1), dan panah jalan masuk di atas latar gelap mendapat kuning (14,8:1).

## 7. Keterbatasan

1. **Data denah.** Lebar jalan masuk berasal dari perbandingan, letak patung adalah perkiraan, dan foto sketsa tangan belum dilampirkan.
2. **Uji browser otomatis.** Semua uji browser dijalankan di Chrome headless. GPU-nya sungguhan (Apple M5), tapi belum ada uji di browser yang saya buka sendiri atau di browser lain. Hasil antialiasing bisa sedikit berbeda di GPU lain, karena MSAA tidak dijamin sama antar vendor.
3. **GitHub Pages belum aktif** saat laporan ini ditulis, jadi URL-nya belum diuji (termasuk tipe MIME file `.mjs`).
4. **Aturan tepi.** Default `triangle()` mengikuti rumus modul, yang merupakan cerminan aturan GPU. Untuk denah saya ini tidak berpengaruh, karena tidak ada pusat pixel yang jatuh tepat di tepi lantai. Tapi untuk mesh dengan tepi miring, rasteriser saya dan GPU akan berbeda di pixel tepat-di-tepi, kecuali memakai `fillRule: "gpu"`.
5. **Matriks CVD.** Asal-usul angka matriks di `index.html` (sama dengan `cvd.py`) belum saya temukan publikasinya. Matriks 3 × 3 seperti ini juga hanya perkiraan kasar penglihatan buta warna.
6. **`bench.mjs`.** Waktu absolut berbeda antar mesin dan antar run. Yang bisa dipegang adalah rasio dan arahnya.

## 8. Reproducibility (A6)

**Salinan bersih.** Hanya file yang akan masuk git disalin ke folder baru: 77 file Modul 2, ditambah `.gitignore` dan `.nojekyll` di root. Tanpa `node_modules`, `out/`, PDF, dan file pribadi:

```
$ nvm use
Found '.../clean/Module2/Source/.nvmrc' with version <22.23.4>
Now using node v22.23.4 (npm v10.9.9)
$ npm ci
found 0 vulnerabilities
$ npm test
ALL CHECKS PASSED  (22 ok, 0 fail)
$ npm run plan
plan "Ruangan patung kuda (rumah saya) -- denah lantai"
polylines: 14   segments: 20   framebuffer: 800x600   silhouette FILLED
wrote out/plan_scratch.ppm (1440015 bytes)
$ node make_tri_ref.mjs --check
  triangles that differ: 0   pixels missing: 0   pixels extra: 0
$ node gpu_rule_check.mjs
fillRule "gpu" vs independent reference with the GPU tie rule: 0/1934 triangles differ, 0 missing, 0 extra
$ node prelim_check.mjs
ALL STUDI PENDAHULUAN NUMBERS CHECKED
$ node cvd_check.mjs
legend distinct in every view (>= 20)
$ npm run serve      (lalu curl)
200 text/html  /web/
200 application/javascript  /web/viewer.mjs
200 application/javascript  /plan_common.mjs
200 application/json  /myplan.json
node 127.0.0.1:4173 (LISTEN)
$ node compare.mjs out/plan_scratch.ppm plan_three.ppm      (export dari salinan bersih)
same size 800x600   identical pixels: 479929/480000   PSNR: 52.7 dB   SSIM: 1.000   max |diff|: 176
```

**Hasilnya identik dengan salinan kerja.** Semua yang bisa dibuat ulang tanpa browser saya buat ulang di salinan bersih, dan hasilnya identik byte demi byte:

- 6 diagram SVG;
- `ref/tri_ref.ppm` dan `ref/tri_t8_ref.ppm`;
- semua PNG yang berasal dari `out/`;
- semua PPM di `out/`.

Dari 33 gambar dan file referensi yang di-commit, tidak ada satu pun yang berbeda. Export viewer dari salinan bersih juga identik byte demi byte dengan export dari salinan kerja.

Sisanya memang tidak dibuat ulang otomatis:

- screenshot legenda dan halaman, `ref/gpu_*.ppm`, `plan_three*.png`, dan `diff_plan*.png` butuh browser (Export PPM dan screenshot). Tanpa export itu, `npm run png` menuliskan pemberitahuan "not found", bukan diam saja;
- `ref/square_fill_ref.ppm` berasal dari dosen;
- gambar di `docs/prediksi/img/` adalah bukti dari `triangle()` **starter** sebelum perbaikan.

**Belum diuji:** clone dari GitHub setelah push, dan URL GitHub Pages:
https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module2/Source/web/
