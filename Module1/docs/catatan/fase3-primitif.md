# Fase 3: Primitif from-scratch (Lab 2 nomor 1 dan 3)

Di fase ini saya menulis ulang fungsi-fungsi dasar pengolahan citra dengan cara saya sendiri, hanya memakai NumPy, lalu membuktikan setiap fungsi cocok dengan satu pembanding. Nama fungsinya sengaja sama dengan starter supaya program lain di repo tetap jalan, tapi isinya saya tulis ulang dengan pendekatan yang berbeda. Semua angka di catatan ini berasal dari program yang dijalankan.

Satu hal sengaja tidak saya sentuh: fungsi `box_downscale_2x` di `resample.py`. Fungsi itu bagian dari diagnosis bug di Fase 4, dan modul meminta diagnosisnya ditulis dari nilai pixel dulu sebelum melihat perbaikannya.

## 1. Histogram (`histogram.py`)

**Tugasnya:** menghitung berapa pixel yang jatuh di setiap rentang nilai (bin).

**Cara saya:** semua nilai pixel saya urutkan dulu dari kecil ke besar. Setelah urut, jumlah pixel di satu bin sama dengan jarak antara posisi nilai pertama bin itu dan posisi nilai pertama bin berikutnya. Bayangkan kartu nilai ujian yang sudah diurutkan: untuk tahu berapa kartu bernilai 60 sampai 69, cukup cari di mana kartu 60 pertama dan kartu 70 pertama, lalu kurangkan posisinya.

Nilai pertama setiap bin saya hitung dengan bilangan bulat saja, yaitu ceil(k × 256 / jumlah bin). Dengan begitu tidak ada pembulatan desimal yang bisa membuat satu nilai masuk ke bin yang salah.

**Kenapa hasilnya pasti cocok:** saya membuat data uji berisi setiap kode 0 sampai 255, masing-masing muncul dengan jumlah yang berbeda (kode 0 sekali, kode 1 dua kali, dan seterusnya sampai 256 kali). Kalau ada satu kode saja yang masuk ke bin yang salah, jumlah bin itu pasti berubah. Hasilnya dibandingkan dengan `numpy.histogram` untuk **setiap** jumlah bin dari 1 sampai 256, dan selisih terbesarnya **0**.

**Bedanya dengan starter:** starter menghitung pixel satu per satu dengan loop dan hanya menerima jumlah bin yang membagi habis 256 (2, 4, 8, ...). Versi saya menerima jumlah bin berapa pun, dan pada foto saya (1.462.084 pixel) selesai dalam 19,7 ms dibanding 130 ms, dengan hasil yang sama persis.

## 2. Box blur (`boxblur.py`)

**Blur 2×2:** setiap blok 2×2 diganti rata-ratanya, sehingga gambar menjadi setengah ukuran. Keempat pixel di setiap blok saya ambil sebagai empat "anyaman" yang terpisah: semua pixel kiri-atas, semua kanan-atas, semua kiri-bawah, dan semua kanan-bawah. Keempat anyaman dijumlahkan lalu dibagi 4.

Pada patch Contoh E1 hasilnya persis:

```
[[  6, 22, 38, 54],
 [ 22, 38, 54, 70],
 [ 38, 54, 70, 86],
 [ 54, 70, 86,102]]
```

dan rata-rata patch-nya 54. Nilainya dihitung dalam float64, karena menjumlahkan empat angka uint8 bisa melewati 255 dan "berputar" kembali ke angka kecil.

**Blur 3×3:** setiap pixel diganti rata-rata dirinya dan 8 tetangganya. Di pinggir gambar, pixel tepi dianggap berulang ke luar. Saya memakai *summed-area table*, yaitu tabel yang setiap selnya berisi jumlah semua pixel di atas dan di kirinya. Dengan tabel ini, jumlah kotak 3×3 di mana pun cukup diambil dari 4 angka: pojok kanan-bawah, dikurangi pojok kanan-atas dan pojok kiri-bawah, ditambah pojok kiri-atas. Cara ini juga tetap cepat untuk kotak yang lebih besar.

**Dicocokkan dengan hitungan tangan** pada patch E1:

| Posisi | Tetangga yang dirata-rata | Hitungan | Hasil |
|---|---|---|---|
| (1,1) | 0, 4, 16, 8, 12, 24, 16, 20, 32 | 132 / 9 = 14,67 | 15 |
| (0,0), pojok | 0, 0, 4, 0, 0, 4, 8, 8, 12 (pinggir diulang) | 36 / 9 = 4,00 | 4 |
| (2,3) | 24, 28, 40, 32, 36, 48, 40, 44, 56 | 348 / 9 = 38,67 | 39 |

Ketiganya cocok. Pada foto saya, hasil 2×2 dan 3×3 juga identik dengan versi starter walaupun caranya berbeda.

## 3. Resample nearest dan bilinear (`resample.py`)

**Nearest:** untuk memperkecil 2×, ambil pixel kiri-atas dari setiap blok dan buang tiga sisanya. Pada patch E1 hasilnya persis a_ij = 16(i + j). Inilah *decimation*: tiga dari empat sampel dibuang, dan itulah yang menyebabkan aliasing.

**Bilinear:** nilai di antara dua sampel ditebak dengan garis lurus: nilai = kiri + t × (kanan − kiri), dengan t adalah posisi di antara keduanya (0 sampai 1). Untuk sampel [0, 100]:

- t = 0,25 → 0 + 0,25 × 100 = **25**
- t = 0,5 → **50**
- t = 0,75 → **75**

Untuk gambar 2D, saya memakai sifat bilinear yang bisa dipisah: interpolasi dulu ke arah horizontal untuk semua baris, lalu hasilnya diinterpolasi ke arah vertikal. Hasilnya sama dengan rumus empat pojok, tapi kodenya cukup memakai satu fungsi 1D yang dipakai dua kali.

**Bug yang saya temukan di starter.** Saat membandingkan versi saya dengan starter, hasil perbesaran 2× berbeda sampai 35 kode. Saya tidak langsung menganggap starter salah. Saya bandingkan keduanya dengan Pillow `BILINEAR` sebagai pihak ketiga, lalu mencari contoh terkecil yang menunjukkan bedanya:

| Sinyal [0, 100] diperbesar 2× | Hasil |
|---|---|
| Versi saya | [0, 25, 75, 100] |
| Pillow | [0, 25, 75, 100] |
| Starter | **[75, 25, 75, 100]** |

Pixel pertama starter salah. Saat diperbesar, pusat pixel output pertama jatuh di posisi −0,25, di luar gambar. Tetangga kirinya seharusnya index −1 dan tetangga kanannya index 0, dengan bobot 0,75 untuk yang kanan. Starter menjepit index kiri ke 0 **lebih dulu**, lalu mengambil index 1 sebagai tetangga kanan, padahal bobotnya tetap 0,75. Hasilnya 0,25 × 0 + 0,75 × 100 = 75. Versi saya menjepit kedua index **setelah** tetangganya ditentukan, sehingga index −1 dan 0 sama-sama menjadi index 0, pixel tepi itu sendiri, dan hasilnya tepat 0.

Bug ini hanya ada di baris dan kolom pertama saat memperbesar. Pada potongan 200 × 200 dari foto saya, starter berbeda sampai 10 kode dari Pillow di tepi, sedangkan di luar baris dan kolom pertama bedanya paling banyak 1 kode. Versi saya paling banyak 1 kode dari Pillow di seluruh gambar (rata-rata 0,149 kode). Saya menambahkan test baru untuk kasus ini, dan sudah saya pastikan test itu memang gagal kalau dijalankan pada kode starter.

## 4. RGB ke abu-abu (`luma.py`)

**Resep yang benar:** ubah kode sRGB ke linear light, jumlahkan dengan bobot Rec. 709 (0,2126 R + 0,7152 G + 0,0722 B), lalu ubah kembali ke sRGB. Bobotnya tidak sama karena mata jauh lebih peka pada hijau daripada biru.

Saya menyusun ketiga variannya dari satu fungsi penjumlahan berbobot yang sama. Bedanya hanya dua hal: penjumlahan dilakukan di linear light atau langsung pada kode, dan bobot apa yang dipakai. Dengan begitu perbedaan antara cara benar dan cara keliru terlihat jelas di kode.

**Dicocokkan dengan Pillow `convert("L")`:** untuk ke-256 warna abu-abu datar (R = G = B, dari 0 sampai 255), selisihnya **0** di semuanya, lebih baik dari syarat ±1 kode. Ini masuk akal: kalau R = G = B, bobot apa pun yang jumlahnya 1 memberi hasil yang sama.

**Celah pada warna jenuh (Contoh E5), pixel (200, 100, 50):**

| Cara | Hasil |
|---|---|
| Benar, kurva sRGB asli | 128 |
| Benar, pendekatan gamma-2 (hitungan tangan modul) | 126 |
| Pillow `convert("L")` | 124 |
| Bobot Rec. 709 langsung pada kode (bug umum) | 118 |
| Rata-rata biasa | 117 |

Celah dengan Pillow 4 kode, dan itu wajar: Pillow memakai bobot Rec. 601 langsung pada kode gamma, bukan luminansi di linear light. Pada foto saya rata-rata selisihnya 0,51 kode dengan maksimum 7 kode.

## 5. Banding dan dithering (`dither.py`, baru)

**Mengukur lebar pita.** Program membuat gradien hitam ke putih selebar 512 pixel, lalu mengukur panjang setiap deretan pixel yang nilainya sama:

| Gradien | Jumlah level | Lebar pita |
|---|---|---|
| 8-bit | 256 | semuanya **2 px** |
| 5-bit, setiap level dapat jatah sama | 32 | semuanya **16 px** |
| 5-bit, rumus pembulatan modul round(v × 31) | 32 | 9 px di kedua ujung, 16 sampai 17 px di tengah |

Angka 2 px dan 16 px cocok dengan Contoh E2. Catatan jujurnya, rumus pembulatan memberi pita ujung yang hanya setengah jatah, karena pembulatan memberi nilai 0 dan 31 hanya setengah rentang.

**Dithering.** Saya memakai *ordered dithering* dengan matriks Bayer 4×4. Sebelum dibulatkan ke level terdekat, setiap pixel diberi ambang yang berbeda menurut pola 4×4 yang berulang. Nilai yang jatuh di antara dua level tidak lagi selalu dibulatkan ke arah yang sama, tapi menjadi campuran titik-titik kedua level. Dari jauh mata merata-ratakan campuran itu kembali menjadi nilai di antaranya, sehingga undakan pita tidak terlihat lagi.

Saya memilih Bayer, bukan Floyd-Steinberg, karena Bayer tidak memakai angka acak (hasilnya selalu sama), bisa dihitung sekaligus untuk seluruh gambar, dan polanya mudah dijelaskan. Floyd-Steinberg menyebarkan sisa pembulatan setiap pixel ke tetangganya, sehingga harus memproses pixel satu per satu secara berurutan.

**Hasil yang terukur:**

- **Histogram berubah.** Tanpa dither, setiap kode 5-bit dipakai tepat 1.024 pixel (16 px × 64 baris). Setelah dither, enam kode pertama dipakai 512, 1.152, 1.024, 1.088, 1.024, dan 1.024 pixel. Kodenya tetap 32 kode yang sama, tidak ada warna baru, yang berubah hanya cara mencampurnya.
- **Pita datar menghilang.** Deretan datar terpanjang turun dari 16 px menjadi 12 px. Sisa deretan 10 sampai 12 px itu muncul tepat di titik ketika nilai idealnya sama persis dengan salah satu level (misalnya kode 8). Di titik itu memang tidak ada yang perlu dicampur, jadi datarnya benar. Yang hilang adalah lompatan tajam antar pita.
- **Rata-rata lokal lebih dekat ke gradien asli.** Saya merata-ratakan setiap blok 4×4 pixel, mirip mata yang menyatukan titik-titik yang berdekatan, lalu membandingkannya dengan gradien ideal. Error rata-ratanya turun dari 1,58 kode (dibulatkan biasa) menjadi **0,36 kode** setelah dither.

Gambar perbandingannya tersimpan di `Source/report/gradient_8vs5.pgm`: 8-bit di atas, 5-bit di tengah, dan 5-bit yang di-dither di bawah.

## Test yang ditambahkan

Test lama tidak ada yang diubah. Saya hanya menambahkan empat test baru ke `make test`:

1. **dither:** pita 2 px dan 16 px, lalu dither memecah pita tanpa menambah warna baru dan menurunkan error rata-rata lokal.
2. **box blur 3×3:** sama dengan rata-rata tetangga yang saya hitung tangan di posisi (2,3).
3. **bilinear:** skala 1 tidak mengubah gambar, warna rata tetap rata, dan tepi [0, 100] menjadi [0, 25, 75, 100].
4. **luma:** ke-256 abu-abu datar sama dengan Pillow dalam 1 kode.

Hasil akhirnya, ke-14 pemeriksaan lolos dan muncul `ALL CHECKS PASSED`.

## Pertanyaan yang mungkin muncul saat viva

**Kenapa histogram kamu mengurutkan dulu, bukan menghitung satu per satu?** Mengurutkan dikerjakan NumPy sekaligus untuk semua pixel, dan setelah urut jumlah per bin tinggal dibaca dari posisi. Hasilnya sama persis, tapi tidak perlu loop per pixel.

**Bagaimana kamu yakin starter yang salah di bilinear, bukan kamu?** Saya tidak memakai versi saya sebagai patokan. Saya memakai Pillow sebagai pihak ketiga dan mengecilkan kasusnya sampai cuma dua sampel, [0, 100], sehingga jawabannya bisa dihitung tangan: pixel pertama berada di luar gambar dan seharusnya sama dengan pixel tepi, yaitu 0.

**Kenapa hasil abu-abu kamu beda dengan Pillow?** Pillow menghitung luma dengan bobot Rec. 601 langsung pada kode gamma. Saya menghitung luminansi di linear light dengan bobot Rec. 709. Pada abu-abu datar keduanya sama persis. Pada warna jenuh berbeda, dan itu memang yang diminta modul untuk dilaporkan.
