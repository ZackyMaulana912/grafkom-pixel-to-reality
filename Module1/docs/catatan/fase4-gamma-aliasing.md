# Fase 4: Bug gamma, pitfall, dan aliasing (Lab 2 nomor 2, 4, 5)

Fase ini berisi tiga pekerjaan: memperbaiki thumbnail yang terlalu gelap dan membuktikannya, menambahkan satu pengaman terhadap jebakan umum, dan menunjukkan aliasing dengan angka. Semua angka di sini berasal dari program yang dijalankan.

## 1. Thumbnail yang gelap: diagnosis dulu, baru perbaikan

Urutannya saya jaga sesuai permintaan modul. Diagnosis lengkap ada di `docs/prediksi/diagnosis-gamma.md` dan ditulis **sebelum** saya membuka kode `gamma_resize_bug.py`. Diagnosis itu hanya memakai nilai pixel, lewat program `Source/gamma_diagnosis.py`. Ringkasnya:

- Rata-rata kode thumbnail sama dengan gambar sumber (144,20), tapi **23,5% cahaya hilang**.
- Setiap nilai thumbnail sama persis (100%) dengan rata-rata keempat kode sRGB di bloknya.
- Dugaan akar masalah: kode sRGB dirata-ratakan langsung tanpa diubah ke linear light.

### Apa yang saya temukan setelah membuka kodenya

Thumbnail gelap itu sengaja dibuat oleh fungsi `box_downscale_2x_naive` di `make_data.py` sebagai bahan latihan, dan fungsi itu memang merata-ratakan kode secara langsung. Fungsi itu tidak saya ubah, karena tanpanya bahan diagnosisnya hilang.

Versi yang benar ada di `resample.py`, fungsi `box_downscale_2x`. Beda keduanya hanya satu langkah, yaitu baris 77:

```python
f = srgb_to_linear(f)                 # <-- the line the bug omits
```

Baris ini mengubah kode ke linear light sebelum dirata-ratakan, dengan pasangannya di baris 83 yang mengubah hasilnya kembali ke sRGB.

### Bukti bahwa langkah itulah perbaikannya

Program `Source/gamma_fix_check.py` menjalankan fungsi yang sama dua kali, dengan langkah decode dimatikan dan dinyalakan:

| Langkah decode | Dibandingkan dengan | Hasil |
|---|---|---|
| dimatikan | thumbnail gelap dari repo | 96,64% sama persis, sisanya beda 1 kode karena urutan pembulatan sedikit berbeda dengan `make_data.py` |
| dinyalakan | rata-rata cahaya (H2) dari program diagnosis saya | **100% sama persis**, selisih 0 |

Acuan H2 dihitung oleh program diagnosis yang saya tulis sebelum melihat perbaikannya, jadi ini pemeriksaan yang independen.

### Keempat prediksi diagnosis, dicek satu per satu

| Prediksi | Hasil | Status |
|---|---|---|
| 1. Setelah diperbaiki, sama dengan H2 (paling banyak beda 1 kode) | 100% sama, selisih 0 | terbukti |
| 2. Rata-rata kode naik dari 144,20 ke sekitar 164,44 | 144,20 → 164,44 | terbukti |
| 3. Rata-rata cahaya kembali seperti sumber | sebelum −23,54%, sesudah −0,001% | terbukti |
| 4. Selisih paling besar di bagian yang kontras | kontras 32-95: 7,47 kode; 96-159: 14,55; 160-255: 24,27 | terbukti |

### Difference image dan PSNR

`make report` menjalankan `gamma_resize_bug.py --fix`, yang menulis tiga gambar ke `Source/report/`: `relief_naive.ppm` (naif), `relief_linear.ppm` (benar), dan `relief_diff.ppm` (selisihnya, diperkuat 4 kali supaya terlihat). Di gambar selisih, bagian tekstur yang rapat dan kontras paling terang, sedangkan bagian yang halus hampir hitam, persis seperti prediksi 4.

| | Selisih rata-rata | Selisih terbesar | PSNR terhadap acuan H2 | SSIM |
|---|---|---|---|---|
| Sebelum perbaikan | 20,24 kode | 42 kode | 21,48 dB | 0,9623 |
| Sesudah perbaikan | 0 | 0 | tak hingga (identik) | 1,0000 |

### Kenapa merata-ratakan kode membuat gelap (modul §8)

Kurva sRGB melengkung ke bawah: kode 128 hanya sekitar 22% cahaya. Kalau dua kode dirata-ratakan, hasilnya berada di tengah **garis lurus** di antara keduanya, sedangkan rata-rata cahaya berada di tengah **kurva**. Karena kurvanya melengkung ke bawah, rata-rata kode selalu jatuh di bawah rata-rata cahaya, kecuali semua nilainya sama. Makin jauh nilai-nilai di dalam blok, makin besar selisihnya. Itulah sebabnya tepi dan tekstur paling parah, dan area rata hampir tidak berubah.

## 2. Satu blok 2×2 dari foto saya, dihitung tangan (A2)

Saya memilih blok yang paling kontras di foto `IMG_8884` (versi kerja 907 × 1612), di baris 1136 kolom 676. Blok ini ada di tepi patung: dua pixel terang dari dinding dan dua pixel gelap dari patung.

| Posisi | R | G | B |
|---|---|---|---|
| kiri-atas | 195 | 191 | 192 |
| kanan-atas | 48 | 38 | 36 |
| kiri-bawah | 224 | 220 | 221 |
| kanan-bawah | 98 | 88 | 86 |

Langkahnya untuk channel R:

1. Ubah ke 0 sampai 1: 195/255 = 0,7647; 48/255 = 0,1882; 224/255 = 0,8784; 98/255 = 0,3843.
2. Decode ke linear dengan ((c + 0,055) / 1,055)^2,4, karena semua nilai di atas 0,04045: 0,5457; 0,0296; 0,7454; 0,1221.
3. Rata-ratakan cahaya: (0,5457 + 0,0296 + 0,7454 + 0,1221) / 4 = 1,4428 / 4 = 0,36071.
4. Encode kembali dengan 1,055 × ℓ^(1/2,4) − 0,055 = 0,63482.
5. Kali 255: 161,878, dibulatkan menjadi **162**.

Dengan langkah yang sama:

| Channel | Rata-rata linear | Hasil encode × 255 | Kode | Rata-rata kode (naif) |
|---|---|---|---|---|
| R | 0,36071 | 161,878 | **162** | 141,25 → 141 |
| G | 0,33841 | 157,264 | **157** | 134,25 → 134 |
| B | 0,34022 | 157,644 | **158** | 133,75 → 134 |

`resample.py` dengan `gamma_correct=True` memberi **[162, 157, 158]**, sama persis sampai level kode. Cara naif memberi [141, 134, 134], 21 sampai 24 kode lebih gelap. Ini contoh nyata di foto saya sendiri: tepi patung akan tampak lebih gelap dan lebih tebal kalau thumbnail dibuat dengan cara naif.

## 3. Perbaikan pitfall: cek buta warna di `make test`

Dari tiga pilihan modul, saya memilih menambahkan cek colour-vision deficiency (CVD) ke `make test`. Alasannya: starter sudah punya demo legenda, tapi demo itu hanya mencetak hasil dan tidak pernah membuat test gagal. Palet yang buruk bisa lolos tanpa ada yang sadar, persis cerita jet di matplotlib.

**Cara kerjanya:** setiap warna legenda dibuat kotak, lalu dilihat dengan empat cara: normal, simulasi deuteranopia, simulasi protanopia, dan grayscale. Untuk setiap cara, program menghitung jarak terkecil antara dua warna legenda mana pun. Kalau ada yang di bawah 20, artinya dua kategori sudah hampir tidak bisa dibedakan, dan test gagal dengan pesan yang menyebut cara melihat mana yang runtuh.

**Sebelum dan sesudah:**

| Palet | Normal | Deuteranopia | Protanopia | Grayscale | `make test` |
|---|---|---|---|---|---|
| Merah-hijau (sebelum) | 51,0 | 17,7 | 10,5 | **0,0** | gagal |
| Viridis 5 warna (sesudah, dipakai proyek) | 68,2 | 36,9 | 46,4 | 79,7 | lolos |

Pada palet merah-hijau, dua kategori menjadi abu-abu yang persis sama kalau dicetak hitam putih (jarak 0,0). Aturan yang saya terapkan adalah **ramp luminansi**: kecerahan viridis naik terus dari ungu gelap ke kuning terang, sehingga urutannya tetap terbaca walaupun warnanya tidak terlihat.

Test-nya juga memeriksa dirinya sendiri: test akan gagal kalau pengaman ini **tidak** menolak palet merah-hijau. Dengan begitu pengamannya tidak bisa diam-diam rusak. Gambar legenda sebelum dan sesudah, dalam keempat cara melihat, ditulis ke `Source/report/legend*.ppm`.

### Tambahan 31 Oktober 2026: asal matriks dan pembanding dari publikasi

Komentar di `cvd.py` starter menyebut matriksnya "Vienot / Brettel-style". Di Modul 2 saya sempat mencatat bahwa publikasi asli angka-angka itu belum saya temukan. Sekarang sudah saya telusuri:

- **Sumbernya bukan Viénot atau Brettel.** Nilai yang sama persis (deuteranopia 62,5 / 37,5 / 0, 70 / 30 / 0, 0 / 30 / 70; protanopia 56,667 / 43,333 / 0, dan seterusnya, dalam persen) ada di halaman "<canvas> + ColorMatrix = Color Blindness" milik colorjack.com. Saya membacanya dari arsip Wayback Machine tanggal 18 Desember 2008 (`web.archive.org/web/20081218040501/http://www.colorjack.com:80/labs/colormatrix/`). Halaman itu menulis bahwa angkanya dibuat dari data rumus Matthew Wickline, dengan "triangulates the hue", dan ditujukan untuk Channel Mixer di Photoshop atau Pixelmator. Jadi angka ini hasil pencocokan cepat, bukan model dari publikasi ilmiah.
- Sebuah gist yang memakai matriks ini (`gist.github.com/Lokno/df7c3bfdc9ad32558bb7`) menulis "RGB transform matrices generated by Michael of www.colorjack.com". Di kolom komentarnya (nburrus, 28 Oktober 2021) ada laporan bahwa pembuatnya sendiri menyebutnya "a very inaccurate one-night hack". Ini kutipan dari orang lain, bukan dari pembuatnya langsung.

Matriks dosen **tidak saya ubah**, karena teks modul memakainya (baris 1 dan 2 deuteranopia hampir sama, sehingga merah dan hijau menjadi mirip). Yang saya ubah hanya keterangannya di `cvd.py`. Sebagai pembanding saya menambahkan matriks dari model yang dipublikasikan: **Machado, Oliveira & Fernandes (2009)**, "A Physiologically-based Model for Simulation of Color Vision Deficiency", IEEE TVCG 15(6), 1291-1298, Tabel 1 untuk tingkat keparahan 1,0 (dikromasi), disalin dari halaman resmi penulisnya (`inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/`). Halaman itu tidak menyebut apakah matriksnya diterapkan pada linear light atau kode sRGB. Saya menerapkannya di linear light, sama seperti matriks dosen, supaya keduanya bisa dibandingkan dengan adil.

```
$ python cvd.py --compare --image data/relief.ppm
BAD (red/green heavy)      deuteranopia  course   17.7   machado2009    4.7
BAD (red/green heavy)      protanopia    course   10.5   machado2009   10.1
project legend (viridis)   deuteranopia  course   36.9   machado2009   82.2
project legend (viridis)   protanopia    course   46.4   machado2009   92.1
red/green pair: gap 242.1 -> deuteranopia course 127.8, machado2009 50.8
data/relief.ppm deuteranopia: |course - machado2009| mean 4.25, max 11 codes
data/relief.ppm protanopia: |course - machado2009| mean 5.46, max 13 codes
```

| Palet | Deuteranopia (dosen / Machado) | Protanopia (dosen / Machado) | Keputusan pengaman |
|---|---|---|---|
| Merah-hijau | 17,7 / 4,7 | 10,5 / 10,1 | gagal di kedua model |
| Viridis (proyek) | 36,9 / 82,2 | 46,4 / 92,1 | lolos di kedua model |

Kesimpulan saya: **keputusan pengaman legenda tidak bergantung pada matriks ColorJack**. Dengan model Machado, palet merah-hijau malah lebih runtuh, dan viridis lebih aman. Matriks dosen juga meremehkan seberapa mirip merah dan hijau bagi penderita deuteranopia. Pasangan merah (220, 30, 30) dan hijau (30, 180, 30) yang berjarak 242,1 masih tersisa 127,8 menurut matriks dosen, padahal menurut Machado tinggal 50,8. Pada foto relief, kedua model berbeda rata-rata 4,3 sampai 5,5 kode (paling banyak 13 kode).

Test baru `cvd: Machado 2009 gives the same legend verdict` mengecek tiga hal:
- setiap baris matriks Machado berjumlah 1, jadi putih tetap putih;
- legenda proyek tidak runtuh;
- legenda merah-hijau runtuh.

Saya juga membuktikan test itu bisa gagal: kalau matriks Machado diganti matriks identitas (penglihatan normal), test langsung gagal karena legenda merah-hijau tidak lagi runtuh.

## 4. Demo aliasing

Program `Source/aliasing_demo.py` membuat pola cosinus dari 0,1 sampai 0,9 cycles per pixel output. Pola dibuat dulu dengan 16 sampel per pixel sebagai pengganti pemandangan asli, lalu diperkecil ke 1 sampel per pixel dengan dua cara:

- **tanpa pre-filter:** ambil satu sampel saja, seperti `resample_nearest`,
- **dengan pre-filter box:** rata-ratakan ke-16 sampel, seperti satu pixel sensor yang mengumpulkan cahaya.

Frekuensi hasilnya diukur dari puncak terkuat FFT.

| f asli | Prediksi \|f − fs\| | Tanpa pre-filter: f terukur | Kekuatan | Dengan box: f terukur | Kekuatan | Prediksi kekuatan box |
|---|---|---|---|---|---|---|
| 0,1 | 0,1 | 0,100 | 1,000 | 0,100 | 0,984 | 0,984 |
| 0,2 | 0,2 | 0,200 | 1,000 | 0,200 | 0,936 | 0,936 |
| 0,3 | 0,3 | 0,300 | 1,000 | 0,300 | 0,859 | 0,859 |
| 0,4 | 0,4 | 0,400 | 1,000 | 0,400 | 0,758 | 0,758 |
| 0,5 | 0,5 | 0,500 | 0,098 | 0,500 | 0,000 | tidak berlaku |
| **0,6** | **0,4** | **0,400** | 1,000 | 0,400 | 0,506 | 0,506 |
| **0,7** | **0,3** | **0,300** | 1,000 | 0,300 | 0,369 | 0,369 |
| **0,8** | **0,2** | **0,200** | 1,000 | 0,200 | 0,235 | 0,235 |
| **0,9** | **0,1** | **0,100** | 1,000 | 0,100 | 0,110 | 0,110 |

Prediksi kekuatan box memakai respons filter rata-rata 16 sampel, |sin(πf) / (16 · sin(πf/16))|, yang hampir sama dengan |sinc(f)|.

**Apa yang terlihat dari tabel:**

1. **Alias muncul di atas 0,5 cycles/pixel**, dan setiap frekuensi terukur persis di prediksinya: 0,6 menjadi 0,4, 0,7 menjadi 0,3 (contoh pagar di modul), 0,8 menjadi 0,2, dan 0,9 menjadi 0,1. Pola yang aslinya sangat rapat muncul sebagai pola yang renggang.
2. **Tepat di 0,5 hasilnya tergantung posisi sampel.** Sampel yang diambil kebetulan berada di fase 1,669 radian, sehingga kekuatannya hanya |cos(1,669)| = 0,098. Rata-rata box justru berpusat di titik nol gelombang, jadi hilang sama sekali. Ini alasan teorema Nyquist meminta laju sampling **lebih besar** dari 2f, bukan sama dengan.
3. **Pre-filter box hanya melemahkan alias, tidak menghapusnya.** Pola 0,6 masih tersisa 50,6%, pola 0,9 tinggal 11,0%, persis sesuai rumus responsnya. Box adalah low-pass yang lemah. Untuk membuang frekuensi di atas 0,5 lebih banyak lagi dibutuhkan filter yang lebih tajam, misalnya filter yang lebih lebar dari satu pixel.

Gambar `Source/report/aliasing_sweep.pgm` menunjukkan hal yang sama secara visual: garis-garis yang frekuensinya naik dari kiri (0,1) ke kanan (0,9). Pada strip atas (tanpa pre-filter), di sisi kanan garisnya justru tampak makin renggang dengan kontras penuh. Pada strip bawah (box), pola palsu itu masih ada tapi sudah pudar menjadi abu-abu.

## Test yang ditambahkan

- **cvd:** legenda proyek lolos dalam keempat cara melihat, dan pengamannya terbukti menolak palet merah-hijau.
- **aliasing:** semua frekuensi 0,1 sampai 0,9 (kecuali tepat 0,5) terukur persis di |f − fs|, dan kekuatan setelah box sama dengan prediksi.

`make test` sekarang berisi 16 pemeriksaan dan semuanya lolos. Pada 31 Oktober 2026 ditambah satu lagi, yaitu pembanding Machado 2009, sehingga totalnya 17 dan semuanya lolos.

## Pertanyaan yang mungkin muncul saat viva

**Commit mana yang memperbaiki bug-nya?** Commit diagnosis (prediksi) dibuat lebih dulu, lalu commit pembuktian perbaikan. Kode perbaikannya sendiri, langkah decode di `resample.py` baris 77, sudah disediakan di repo. Pekerjaan saya adalah membuktikan dari nilai pixel bahwa langkah itu yang hilang, lalu memverifikasi dengan acuan independen bahwa menyalakannya memulihkan cahaya sampai 100% sama.

**Kenapa pre-filter tidak menghapus alias seluruhnya?** Karena filter box mulai melemah perlahan, bukan memotong tajam di 0,5. Angkanya terlihat di tabel: di 0,6 masih 50,6%.

**Kenapa memilih cek CVD, bukan pre-filter atau asersi overflow?** Pre-filter sudah dibahas lengkap di demo aliasing, dan semua primitif yang menjumlahkan atau merata-ratakan nilai sudah menghitung dalam float64 sejak Fase 3. Cek CVD menutup celah yang benar-benar ada di starter: legenda yang runtuh tidak pernah membuat test gagal.
