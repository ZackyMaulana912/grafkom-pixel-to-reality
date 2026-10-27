# Laporan Modul 1: Representasi Digital, Warna & Memori

Zacky Maulana (NIM 20241337034), S1 Informatika UMSurabaya
Praktikum Grafika Komputer

Semua angka di laporan ini berasal dari program di `Module1/Source/` yang benar-benar dijalankan. Catatan langkah demi langkah ada di `docs/catatan/`, dan prediksi yang ditulis sebelum pengukuran ada di `docs/prediksi/`.

---

## 1. Input dan manifest (A1)

**Subjek:** patung kuda berdiri milik saya sendiri, difoto di dalam rumah. Saya mengambil 28 foto dengan iPhone 17 Pro pada 27 Oktober 2026, pukul 11.33 sampai 11.36, sambil mengelilingi patung tanpa memindahkannya.

**Toolchain (Lab 1 nomor 1):** macOS 27.0.1 (Apple Silicon), Python 3.11.8, NumPy 2.4.6, Pillow 13.0.0 dengan dukungan WebP dan AVIF, GNU Make 3.81. Dicatat 23 Oktober 2026, diperiksa ulang 27 Oktober 2026.

| Pengaturan kamera (dibaca dari EXIF) | Nilai |
|---|---|
| Kamera | iPhone 17 Pro, kamera utama 6,765 mm, f/1.78 |
| Resolusi | 4536 × 8064 pixel |
| ISO | 250 sampai 400 (otomatis) |
| Kecepatan rana | 1/33 sampai 1/40 detik |
| Format | JPG dengan profil warna Display P3 |

Empat foto saya buang karena blur, setelah diukur ketajamannya lalu dicek langsung pada potongan resolusi penuh: IMG_8881, 8885, 8888, dan 8891. Sisanya **24 foto** dengan putaran 360 derajat yang lengkap.

Foto asli tidak masuk repo karena terlalu besar dan menyimpan lokasi GPS rumah. Yang masuk repo adalah versi kecil 907 × 1612 yang:

- diperkecil 5 kali dengan merata-ratakan di linear light,
- diubah dari Display P3 ke sRGB dengan matriks 3 × 3 yang saya hitung sendiri, dengan selisih paling banyak 1 kode dari mesin warna Pillow,
- dibuang semua metadatanya, termasuk GPS, sudah dicek di struktur file JPG-nya.

Checksum SHA-256 ke-28 foto asli ada di `Source/photos/checksums.sha256`.

`data/manifest.csv` berisi 47 baris: 21 citra sintetis dari starter, 24 foto saya, dan 2 crop untuk Lab 3. Baris foto mencatat ukuran **asli** dari kamera, karena budget harus dihitung pada resolusi yang benar-benar ditulis kamera. Contoh barisnya:

```
filename,width,height,channels,on_disk_bytes,format,note
IMG_8884.jpg,4536,8064,3,5971188,"JPEG, Apple iPhone 17 Pro, ISO 250, 1/33 s, f/1.78","samping agak dari belakang, kepala menghadap kiri foto; latar dinding polos (versi kerja 907x1612: IMG_8884.ppm)"
```

---

## 2. Budget (A1)

MB = 10^6 byte dan GB = 10^9 byte (basis 10). MiB = 2^20 = 1.048.576 byte dan GiB = 2^30 byte (basis 2). Setiap angka diberi label.

| Item | Hitungan | Hasil |
|---|---|---|
| Byte per foto (RGB888) | 4536 × 8064 × 3 | **109.734.912 B** = 109,7349 MB = 104,6514 MiB |
| Working set 24 foto | 109.734.912 × 24 | **2.633.637.888 B** = 2.511,63 MiB (2,4528 GiB) |
| Flythrough 10 s, 30 fps | 109.734.912 × 300 | **32.920.473.600 B** = 32,9205 GB = 30,6596 GiB |
| Bandwidth | 109.734.912 × 30 | **3.292.047.360 B/s** = 3.292,05 MB/s = 26.336,38 Mbit/s |

`python budget.py --wh 4536 8064 --fps 30 --seconds 10` mencetak 109,734,912 B per frame dan 32,920,473,600 B per klip. Keduanya sama persis sampai ke byte.

**Satu angka direproduksi manual: IMG_8884.** Setelah dibuka ukurannya 4536 × 8064 × 3 = 109.734.912 B. Di disk ukurannya 5.971.188 B. Rasio kompresi efektifnya 109.734.912 / 5.971.188 = **18,38×**. Ini cocok dengan `budget.md` yang dibuat `make report`.

**Ukuran di disk vs ukuran setelah dibuka (Lab 1 nomor 4):**

| Foto | Isi | Di disk | Rasio |
|---|---|---|---|
| IMG_8884 | latar dinding polos, ISO 250 | 5.971.188 B | 18,38× |
| IMG_8889 | latar rak dan barang yang ramai, ISO 320 | 6.855.280 B | 16,01× |
| IMG_8897 | latar lemari, ISO 400 | 7.350.768 B | 14,93× |

Ukuran file mengikuti banyaknya detail halus di resolusi penuh. Saya mengukur rata-rata perubahan antar pixel bertetangga untuk setiap foto, dan korelasinya dengan ukuran file **0,98**. Noise dari ISO yang lebih tinggi kemungkinan ikut menyumbang: rata-rata ukuran file 6,21 MB di ISO 250, 6,67 MB di ISO 320, dan 7,19 MB di ISO 400. Pengaruh ISO dan pengaruh isi foto tidak bisa saya pisahkan, karena foto ISO 400 juga diambil dari sisi dengan latar yang berbeda. Inilah alasan foto langit polos dan foto dedaunan berbeda ukuran walaupun resolusinya sama: JPEG mencatat area rata dengan sedikit angka, dan area penuh perubahan dengan banyak angka.

**Implikasi untuk texture capstone (dari contoh E7):**

| Texture | Dengan mip | Muat di 8 GiB | 200 texture |
|---|---|---|---|
| 4096² RGBA8 | 85,33 MiB | 96 | 16,67 GiB (tidak muat) |
| 2048² RGBA8 | 21,33 MiB | 384 | 4,17 GiB |
| 4096² BC7 (1 B/pixel) | 21,33 MiB | 384 | 4,17 GiB |
| 2048² BC7 | 5,33 MiB | 1.536 | 1,04 GiB |

Angka "muat" di atas belum dikurangi geometri, framebuffer, dan render target. Rencana saya: texture di GPU memakai kompresi BC7, hanya objek utama yang memakai 4096, dan objek kecil cukup 2048.

---

## 3. Primitif from-scratch dan kecocokannya (A2)

Semua primitif saya tulis ulang dengan pendekatan sendiri, hanya memakai NumPy, lalu dicocokkan dengan satu pembanding. Penjelasan lengkapnya ada di `docs/catatan/fase3-primitif.md`.

| Primitif | Cara saya | Pembanding | Hasil |
|---|---|---|---|
| `histogram_from_scratch` | urutkan nilai, lalu cari posisi awal setiap bin | `numpy.histogram`, untuk setiap jumlah bin 1 sampai 256 | **max err = 0** |
| `box_blur_2x2` | jumlah empat "anyaman" pixel | Contoh E1 | [[6,22,38,54],[22,38,54,70],[38,54,70,86],[54,70,86,102]], **mean 54** |
| `box_blur_3x3` | summed-area table | rata-rata tetangga hitung tangan | (1,1) = 14,67 → 15; (0,0) = 4; (2,3) = 38,67 → 39 |
| `resample_nearest` | ambil pixel kiri-atas setiap blok | Contoh E1 | persis a_ij = 16(i + j) |
| `resample_bilinear` | interpolasi 1D yang dipakai dua kali | identitas 1D dan Pillow `BILINEAR` | **25 / 50 / 75**; upscale 2× paling banyak 1 kode dari Pillow |
| `rgb_to_grey` | decode, Rec. 709, encode | Pillow `convert("L")` | 256 abu-abu datar: selisih **0**; (200, 100, 50): 128 vs Pillow 124, **celah 4 kode** |

Saat menulis ulang bilinear, saya menemukan **bug di starter**: perbesaran [0, 100] menjadi **[75, 25, 75, 100]**, padahal seharusnya [0, 25, 75, 100] (Pillow juga memberi itu). Pixel pertama yang jatuh di luar gambar diberi bobot 75% ke tetangga yang salah. Versi saya memperbaikinya, dan test baru yang saya tambahkan terbukti gagal kalau dijalankan pada kode starter.

**Satu blok 2×2 dari foto saya, dihitung tangan.** Blok paling kontras di IMG_8884 (baris 1136, kolom 676), di tepi patung terhadap dinding: R = 195, 48, 224, 98.

1. Bagi 255: 0,7647; 0,1882; 0,8784; 0,3843.
2. Decode ((c + 0,055) / 1,055)^2,4: 0,5457; 0,0296; 0,7454; 0,1221.
3. Rata-rata cahaya: 1,4428 / 4 = 0,36071.
4. Encode 1,055 × ℓ^(1/2,4) − 0,055 = 0,63482, lalu × 255 = 161,878 → **162**.

Dengan cara yang sama G = **157** dan B = **158**. `resample.py` memberi **[162, 157, 158]**, sama persis sampai level kode. Cara naif memberi [141, 134, 134], 21 sampai 24 kode lebih gelap.

---

## 4. Diagnosis dan perbaikan (A3)

### Thumbnail yang gelap

**Diagnosis sebelum perbaikan** (`docs/prediksi/diagnosis-gamma.md`, ditulis dan di-commit sebelum membuka `gamma_resize_bug.py`). Bukti dari nilai pixel saja:

- Rata-rata kode thumbnail tetap 144,20, sama dengan sumber, tapi rata-rata cahayanya turun dari 0,38885 ke 0,29731: **23,5% cahaya hilang**.
- Setiap nilai thumbnail sama persis (100%) dengan rata-rata keempat kode sRGB di bloknya. Kalau dihitung dengan rata-rata cahaya, tidak ada yang cocok (0%).
- Thumbnail lebih gelap di 100% nilai, rata-rata **20,24 kode** dan paling banyak **42 kode**. Paling parah di blok yang kontras: 7,47, lalu 14,55, lalu 24,27 kode, dengan korelasi 0,779.
- Histogramnya bergeser ke kiri, dengan puncak pindah dari bin 160 ke bin 144.

**Akar masalah:** kode sRGB dirata-ratakan langsung tanpa diubah ke linear light.

**Perubahan satu baris:** langkah decode di `resample.py` baris 77, `f = srgb_to_linear(f)`, dengan pasangannya encode di baris 83. Dengan langkah itu dimatikan, hasilnya sama dengan thumbnail gelap (96,64% persis, sisanya beda 1 kode karena urutan pembulatan). Dengan langkah itu dinyalakan, hasilnya 100% sama dengan acuan cahaya independen yang saya tulis sebelum melihat perbaikan.

**Bukti:**

| | Selisih rata-rata | Selisih terbesar | PSNR vs acuan | SSIM |
|---|---|---|---|---|
| Sebelum | 20,24 kode | 42 kode | 21,48 dB | 0,9623 |
| Sesudah | 0 | 0 | tak hingga | 1,0000 |

Rata-rata cahaya kembali dari −23,54% menjadi −0,001% terhadap sumber. Difference image (`report/relief_diff.ppm`, diperkuat 4 kali) paling terang di tekstur yang rapat dan hampir hitam di area rata.

**Kenapa merata-ratakan kode sRGB menggelapkan (modul §8):** kurva sRGB melengkung ke bawah, sehingga kode 128 hanya sekitar 22% cahaya. Rata-rata dua kode jatuh di tengah garis lurus di antara keduanya, sedangkan rata-rata cahaya jatuh di tengah kurva. Karena kurvanya melengkung ke bawah, rata-rata kode selalu di bawah rata-rata cahaya, kecuali semua nilainya sama. Makin jauh nilai-nilai di dalam blok, makin besar selisihnya.

### Demo aliasing

Pola 0,1 sampai 0,9 cycles/pixel, diperkecil ke 1 sampel per pixel. Frekuensinya diukur dengan FFT.

| f | Prediksi \|f − fs\| | Terukur | Sisa kekuatan setelah pre-filter box (terukur = prediksi) |
|---|---|---|---|
| 0,6 | 0,4 | 0,400 | 0,506 |
| 0,7 | 0,3 | 0,300 | 0,369 |
| 0,8 | 0,2 | 0,200 | 0,235 |
| 0,9 | 0,1 | 0,100 | 0,110 |

Alias muncul untuk semua f di atas 0,5, dan setiap frekuensi terukur persis di prediksinya. Frekuensi 0,1 sampai 0,4 tetap di tempatnya. Tepat di 0,5 hasilnya tergantung posisi sampel: kekuatannya 0,098 = |cos(1,669)|. Pre-filter box hanya melemahkan alias, tidak menghapusnya.

### Perbaikan pitfall: cek buta warna di `make test`

Starter punya demo legenda yang hanya mencetak hasil. Sekarang `make test` gagal kalau dua kategori legenda runtuh di bawah jarak 20, dan test itu juga memastikan pengamannya menolak palet merah-hijau.

| Palet | Normal | Deuteranopia | Protanopia | Grayscale | `make test` |
|---|---|---|---|---|---|
| Merah-hijau (sebelum) | 51,0 | 17,7 | 10,5 | 0,0 | gagal |
| Viridis (sesudah) | 68,2 | 36,9 | 46,4 | 79,7 | lolos |

---

## 5. Persepsi (A5)

**CVD.** Legenda sebelum dan sesudah, dalam simulasi deuteranopia, protanopia, dan grayscale, ada di bagian 4 `report.html`. Aturan yang saya terapkan adalah **ramp luminansi**: kecerahan viridis naik terus dari ungu gelap ke kuning terang, sehingga urutannya tetap terbaca walaupun hue-nya tidak terlihat. Palet merah-hijau gagal paling parah di grayscale: dua kategori menjadi abu-abu yang sama persis (jarak 0,0).

**Banding.** Gradien 512 pixel, diukur dengan `dither.py`:

| Gradien | Level | Lebar pita |
|---|---|---|
| 8-bit | 256 | 2 px |
| 5-bit, jatah sama per level | 32 | 16 px |
| 5-bit, rumus round(v × 31) | 32 | 9 px di ujung, 16 sampai 17 px di tengah |

**Yang diubah dithering (Bayer 4×4):** kodenya tetap 32 kode yang sama, tapi pemakaiannya bercampur (misalnya 1.024 pixel per kode menjadi 512, 1.152, 1.024, 1.088, dan seterusnya). Deretan datar terpanjang turun dari 16 px ke 12 px, dan sisanya muncul tepat di titik ketika nilai ideal sama dengan satu level, sehingga memang tidak perlu dicampur. Setelah dirata-ratakan per blok 4×4, seperti mata menyatukan titik-titik yang berdekatan, error terhadap gradien asli turun dari 1,58 ke **0,36 kode**.

---

## 6. Keputusan format (A4)

**Prediksi tertulis** ada di `docs/prediksi/prediksi-format.md` dan di-commit sebelum `format_compare.py` dijalankan.

**Hasil terukur** (crop 256 × 256, setelah decode 196.608 B):

| Format | Dinding: byte | rasio | PSNR | Surai: byte | rasio | PSNR |
|---|---|---|---|---|---|---|
| PNG | 17.945 | 10,96× | tak hingga | 99.593 | 1,97× | tak hingga |
| WebP lossless | 13.366 | 14,71× | tak hingga | 73.108 | 2,69× | tak hingga |
| JPG q92 | 3.804 | 51,68× | 52,1 dB | 19.208 | 10,24× | 40,5 dB |
| WebP q92 | 908 | 216,53× | 48,2 dB | 15.984 | 12,30× | 41,2 dB |
| JPG q75 | 1.941 | 101,29× | 50,0 dB | 10.136 | 19,40× | 36,8 dB |
| JPG q40 | 1.734 | 113,38× | 44,7 dB | 5.707 | 34,45× | 33,9 dB |
| AVIF q40 | 436 | 450,94× | 46,6 dB | 2.788 | 70,52× | 33,8 dB |

**Rekonsiliasi.** Prediksi yang tepat: AVIF q40 paling kecil, surai selalu minimal 3 kali lebih besar dari dinding, urutan ukuran surai persis seperti yang saya tulis, dan artefak JPEG baru jelas di q40. Prediksi yang meleset: PNG dinding ternyata 10,96× (saya kira 2× sampai 4×), JPG lebih padat dari perkiraan, dan WebP q92 lebih kecil dari JPG q40 pada dinding.

Penyebab terbesarnya, yang saya ukur setelah prediksi meleset: crop diambil dari versi kerja yang sudah diperkecil, sehingga noise per pixel di dinding hanya 0,49 kode, dibanding 1,78 kode pada area yang sama di foto asli. Artefak di surai q40 juga diukur: loncatan nilai di batas blok 8 × 8 rata-rata 6,52 kode, dibanding 3,73 kode di dalam blok.

**Perbandingan downscale dengan Pillow (Lab 3 nomor 2).** Pillow `Image.BOX` paling banyak beda 1 kode dari cara naif di ketiga gambar uji. Jadi **bawaan Pillow mereproduksi bug-nya**. Satu-satunya yang cocok dengan hasil benar adalah fungsi dengan langkah decode ke linear. Pada IMG_8884, PSNR Pillow BOX terhadap hasil benar 51,42 dB dengan selisih terbesar 26 kode di tepi patung. Pada relief yang penuh tekstur PSNR-nya 21,68 dB.

**Kebijakan** (`Source/report/formats.md`):

| Kegunaan | Format | Angka pendukung |
|---|---|---|
| Arsip | PNG, ditambah JPG asli kamera | satu-satunya PSNR tak hingga; surai 99.593 B |
| Hero image web | WebP q92 | surai 15.984 B dan 41,2 dB, 17% lebih kecil dan lebih tajam dari JPG q92 |
| Thumbnail | JPG q75, diperkecil linear | surai 10.136 B dan 36,8 dB; Pillow BOX meniru bug gamma |
| Texture Modul 3 | PNG 8-bit sRGB | lossless; di JPG q40 loncatan batas blok sudah 6,52 kode |
| Flythrough | MP4/H.264 sekitar 8 Mbit/s | tanpa kompresi butuh 26.336,38 Mbit/s |

**Kenapa jawaban arsip berbeda dari jawaban termurah.** Yang termurah adalah AVIF q40 (2.788 B). PNG 36 kali lebih besar. Arsip harus menjaga semua kemungkinan pemakaian di masa depan, seperti dipotong, diwarnai ulang, atau dijadikan texture, sedangkan file lossy hanya menjaga tampilan untuk satu ukuran layar. Informasi yang sudah dibuang tidak bisa dikembalikan.

---

## 7. Keterbatasan (A4)

1. **Pada citra yang hampir rata, "gamma-correct lebih baik" hampir tidak terasa.** Pada foto saya, cara naif hanya berbeda rata-rata 0,18 kode (PSNR 52,24 dB). Kesalahannya terkumpul di tepi, sampai 27 kode.
2. **Display target yang bukan sRGB.** Foto asli saya Display P3. Semua kode modul menganggap sRGB, jadi saya mengonversinya, dan 0,07% sampai 0,93% nilai channel yang berada di luar jangkauan sRGB terpotong. Di layar P3 atau HDR, warna paling jenuh itu bisa ditampilkan, tapi pipeline ini sudah membuangnya.
3. **Pipeline 8-bit dengan round-trip tambahan menambah banding.** Saya mengukur: kalau linear light disimpan di 8 bit lalu diubah kembali ke sRGB, hanya 183 dari 256 kode yang selamat. Dari 64 kode tergelap, tinggal 14 nilai, dengan lompatan sampai 13 kode. Di float64 round-trip-nya praktis tanpa error (2,8 × 10⁻¹⁴). Jadi cara benar hanya aman kalau nilai antaranya disimpan dalam presisi tinggi.
4. **Kebijakan format dibuat dari crop versi kerja yang sudah diperkecil**, sehingga noise-nya jauh lebih rendah daripada foto asli. Untuk foto asli, PNG akan jauh kurang efisien daripada angka di tabel.
5. **Exposure tidak saya kunci saat memotret**, jadi ISO berubah antara 250 dan 400, dan tingkat noise antar foto tidak sama.
6. **PSNR dan SSIM global tidak sama dengan persepsi mata.** Contohnya di dinding: JPG q40 punya PSNR 44,7 dB, tapi blok-bloknya sudah menjadi rata total. SSIM di repo ini juga versi global, bukan versi berjendela dari paper aslinya.

---

## 8. Refleksi: kalau kamera hanya menulis JPEG (Lab 3 nomor 6)

Foto saya ditulis iPhone sebagai JPEG 8-bit dalam Display P3. Sebelum lab ini dimulai, banyak hal sudah hilang di dalam kamera. Data sensor mentah dengan bit depth lebih tinggi sudah dibulatkan menjadi 8 bit per channel. Keputusan white balance, pengurangan noise, dan penajaman sudah dipanggang ke dalam pixel dan tidak bisa diulang dengan pengaturan lain. Detail halus sudah dibuang oleh kompresi JPEG: rasio efektifnya 14,93× sampai 18,38×. Area terang yang terpotong juga tidak bisa dipulihkan.

Modul yang paling bergantung pada salinan arsip berkualitas adalah **Modul 5 (NeRF)**, karena rekonstruksi 3D butuh banyak foto dengan exposure dan warna yang konsisten. Pengalaman di lab ini menunjukkan bahwa ISO saya berubah antara 250 dan 400 karena exposure tidak dikunci. **Modul 3** juga bergantung pada arsip, karena texture akan diperkecil dan dibuat mipmap berkali-kali.

Lain kali saya akan:

- mengunci exposure dan white balance sebelum mulai memutari objek,
- menyimpan foto dalam format mentah kalau HP-nya mendukung, atau minimal JPEG resolusi penuh tanpa dikirim lewat aplikasi chat,
- mengambil lebih dari 15 foto dengan beberapa ketinggian kamera,
- mengarsipkan file asli dari kamera tanpa diubah, lalu membuat semua versi turunan dari file itu.

---

## 9. Reproducibility (A6)

Uji dari salinan bersih pada 27 Oktober 2026: semua file yang masuk repo disalin ke folder kosong, tanpa foto asli, tanpa `.venv`, dan tanpa isi `data/` selain `manifest.csv`. Lalu:

```
$ python3 -m venv .venv
$ .venv/bin/pip install -r requirements.txt
numpy==2.4.6
pillow==13.0.0
$ make data
wrote 21 images + manifest.csv to data/  (2827425 bytes on disk)
imported 24 photos -> data/*.ppm (105,270,432 bytes), manifest.csv now has 47 rows
$ make test
OK   ppm_io round-trip
OK   srgb round-trip + E4
OK   make_data running patch (mean 54)
OK   boxblur: E1 2x2 result + mean 54
OK   resample: nearest==a_ij, bilinear 25/50/75, checker split
OK   histogram: max err vs numpy = 0
OK   luma: E5 numbers + flat-grey identity
OK   metrics: psnr/ssim sanity
OK   cvd: red/green collapse under deuteranopia
OK   budget: E6/E7 exact to the byte
OK   dither: bands 2/16 px, Bayer dither breaks them
OK   boxblur: 3x3 = hand neighbour mean
OK   bilinear: identity, constant, edge clamp
OK   luma: flat greys 0..255 = Pillow 'L' within 1
OK   cvd: chart legend survives deuter/protan/grayscale
OK   aliasing: every f lands at its predicted |f - fs|
ALL CHECKS PASSED
$ make report
wrote report/budget.md and report/report.html
```

Tidak ada langkah manual. Semua file `report/`, `data/manifest.csv`, dan ke-47 citra di `data/` yang dihasilkan **identik byte per byte** dengan salinan kerja saya.

**Baris Verified** (di `Source/README.md`): macOS 27.0.1 arm64, Python 3.11.8, NumPy 2.4.6, Pillow 13.0.0 (WebP + AVIF), GNU Make 3.81, 27 Oktober 2026, `make test` 16/16.

**Yang belum diuji:** clone yang diambil langsung dari GitHub (perlu commit di-push dulu), serta Windows dan Linux.
