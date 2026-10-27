# Fase 2: Foto saya dan budget memorinya (Lab 1)

Di fase ini saya memasukkan foto subjek saya sendiri ke dalam proyek, lalu menghitung berapa besar memori dan bandwidth yang dibutuhkan kalau foto-foto itu diproses tanpa kompresi. Semua angka di sini diambil dari program yang benar-benar dijalankan.

## Subjek dan pengambilan foto

Subjek saya adalah patung kuda berdiri milik saya sendiri, difoto di dalam rumah. Saya mengambil 28 foto dengan iPhone 17 Pro pada 27 Oktober 2026, pukul 11.33 sampai 11.36, sambil berjalan mengelilingi patung tanpa memindahkannya. Patungnya sengaja tidak diputar supaya latar belakangnya tetap konsisten antar foto, karena itu penting untuk rekonstruksi 3D di Modul 5.

| Pengaturan | Nilai (dibaca dari info EXIF foto) |
|---|---|
| Kamera | iPhone 17 Pro, kamera utama 6,765 mm, f/1.78 |
| Resolusi | 4536 × 8064 pixel (posisi portrait), sekitar 36,6 juta pixel |
| ISO | 250 sampai 400, berubah otomatis |
| Kecepatan rana | 1/33 sampai 1/40 detik |
| Format | JPG, dengan profil warna Display P3 |

Exposure tidak saya kunci, jadi ISO berubah antara 250 dan 400 mengikuti arah pandang. Ini saya catat sebagai keterbatasan.

## Dari 28 foto menjadi 24

Modul meminta tidak ada foto yang blur. Saya tidak mau menilai blur hanya dengan kesan, jadi setiap foto saya beri skor ketajaman: seberapa besar perubahan terang antar pixel yang bertetangga di bagian tengah foto (variance of Laplacian). Foto yang skornya di bawah setengah median saya periksa langsung pada potongan resolusi penuh, dibandingkan dengan foto di sebelahnya.

| Foto | Skor dibanding median | Hasil pemeriksaan |
|---|---|---|
| IMG_8881 | 25% | blur karena gerakan, dibuang |
| IMG_8885 | 28% | blur, dibuang |
| IMG_8888 | 33% | blur, dibuang |
| IMG_8891 | 48% | sedikit lembut, dibuang supaya aman |

Sisanya 24 foto tajam, dengan putaran 360 derajat yang tetap lengkap. Daftar ini dan alasannya tersimpan di `Source/photos/excluded.txt`.

## Menyiapkan foto untuk repo

Foto asli tidak masuk GitHub karena terlalu besar. Satu foto setelah dibuka (decode) memakan 104,65 MiB. Foto asli disimpan di `Source/photos/original/` yang diabaikan git, dan sebagai buktinya checksum SHA-256 ke-28 foto asli dicatat di `Source/photos/checksums.sha256`.

Yang masuk repo adalah versi kecil berukuran 907 × 1612 pixel di `Source/photos/small/`, dibuat oleh `Source/prepare_photos.py`. Ada tiga hal yang saya perhatikan di sini.

**1. Diperkecil dengan cara yang benar.** Foto diperkecil 5 kali dengan merata-ratakan setiap blok 5 × 5 pixel. Rata-ratanya dihitung di linear light, bukan langsung pada kode sRGB, karena itulah inti Modul 1: merata-ratakan kode sRGB membuat hasilnya terlalu gelap. Semua hitungan dikerjakan dengan NumPy dalam float64, lalu dibulatkan ke 0 sampai 255 hanya sekali di akhir.

**2. Warna diubah dari Display P3 ke sRGB.** iPhone menyimpan foto dalam Display P3, ruang warna yang lebih luas dari sRGB, sedangkan seluruh kode modul menganggap angkanya sRGB. Kurva gamma P3 sama dengan sRGB, yang berbeda hanya posisi tiga warna dasarnya. Jadi konversinya cukup: decode ke linear, kalikan dengan matriks 3 × 3, lalu lanjut. Matriksnya saya hitung dari koordinat warna dasar kedua ruang warna:

```
[ 1,224940  -0,224940   0,000000 ]
[-0,042057   1,042057   0,000000 ]
[-0,019638  -0,078636   1,098274 ]
```

Untuk memastikan matriks ini benar, hasilnya saya bandingkan dengan mesin konversi warna bawaan Pillow (ImageCms) pada potongan 512 × 512 pixel. Selisih terbesarnya 1 kode, rata-ratanya 0,017 kode, dan 100% pixel selisihnya paling banyak 1 kode. Warna yang berada di luar jangkauan sRGB lalu dipotong ke batasnya, jumlahnya 0,07% sampai 0,93% dari nilai channel per foto.

**3. Lokasi GPS dibuang.** Ke-28 foto asli menyimpan lokasi GPS tempat foto diambil, yaitu rumah saya. Versi kecil disimpan tanpa metadata sama sekali. Saya cek struktur file JPG-nya: isinya hanya bagian gambar standar, tanpa bagian EXIF, XMP, atau profil warna.

Setelah itu `make data` menjalankan `import_photos.py`, yang mengubah versi kecil menjadi file PPM di `data/` dan menambahkan satu baris per foto ke `data/manifest.csv`. Baris di manifest mencatat ukuran **asli** dari kamera (4536 × 8064, ukuran file asli), karena budget harus dihitung pada resolusi yang benar-benar ditulis kamera.

## Hitungan budget secara manual

Saya memakai MB = 10^6 byte dan MiB = 2^20 = 1.048.576 byte, dan setiap angka diberi label.

**Byte per foto setelah decode (RGB888, 3 byte per pixel)**
- Pixel: 4536 × 8064 = 36.578.304 pixel
- Byte: 36.578.304 × 3 = **109.734.912 B**
- = 109.734.912 / 10^6 = **109,7349 MB**
- = 109.734.912 / 1.048.576 = **104,6514 MiB**

**Working set seluruh set (24 foto)**
- 109.734.912 × 24 = **2.633.637.888 B**
- = 2.633.637.888 / 1.048.576 = **2.511,63 MiB** (= 2,4528 GiB)

Artinya, kalau ke-24 foto dibuka bersamaan di memori, butuh sekitar 2,45 GiB RAM. Bandingkan dengan ukuran filenya di disk yang totalnya hanya 163.004.791 B (155,45 MiB).

**Flythrough hipotetis 10 detik, 30 fps, tanpa kompresi**
- Jumlah frame: 10 × 30 = 300 frame
- Byte: 109.734.912 × 300 = **32.920.473.600 B**
- = 32.920.473.600 / 10^9 = **32,9205 GB**
- = 32.920.473.600 / 2^30 = **30,6596 GiB**

**Bandwidth**
- 109.734.912 × 30 = **3.292.047.360 B/s** = 3.292.047.360 / 10^6 = **3.292,05 MB/s**
- Dalam bit: 3.292.047.360 × 8 = 26.336.378.880 bit/s = **26.336,38 Mbit/s** (sekitar 26,3 Gbit/s)

### Dicocokkan dengan `budget.py`

Perintah `python budget.py --wh 4536 8064 --fps 30 --seconds 10` menghasilkan:

```
4536x8064, 24 bpp:
  bytes / frame : 109,734,912 B  =  109.735 MB  =  104.651 MiB  =  0.1022 GiB
  10 s @ 30 fps : 32,920,473,600 B  =  32920.474 MB  =  31395.410 MiB  =  30.6596 GiB
  bandwidth     : 3292.0 MB/s  =  26336.4 Mbit/s
```

Byte per frame (109.734.912 B) dan byte klip (32.920.473.600 B) sama persis sampai ke byte. Angka MB, MiB, GiB, dan bandwidth juga sama, hanya pembulatan tampilannya yang berbeda.

## Ukuran di disk vs ukuran setelah decode

Saya memilih tiga foto: yang filenya paling kecil, satu yang latarnya paling ramai secara kasat mata, dan yang filenya paling besar.

| Foto | Isi foto | Ukuran di disk | Setelah decode | Rasio kompresi |
|---|---|---|---|---|
| IMG_8884 | samping, latar dinding polos, ISO 250 | 5.971.188 B (5,97 MB) | 109.734.912 B | 109.734.912 / 5.971.188 = **18,38×** |
| IMG_8889 | belakang, latar rak dan barang ramai, ISO 320 | 6.855.280 B (6,86 MB) | 109.734.912 B | **16,01×** |
| IMG_8897 | samping, latar lemari, ISO 400 | 7.350.768 B (7,35 MB) | 109.734.912 B | **14,93×** |

Rata-rata ke-24 foto: 2.633.637.888 / 163.004.791 = **16,16×**.

**Kenapa rasionya berbeda?** JPEG menyimpan setiap blok 8 × 8 pixel sebagai kumpulan pola gelombang, lalu membuang dan menyederhanakan pola halus yang kurang terlihat. Area yang rata, seperti dinding polos atau langit, cukup dicatat dengan sedikit angka, jadi filenya kecil. Area yang penuh perubahan, seperti dedaunan, barang berserakan, atau butiran noise, butuh banyak angka, jadi filenya besar.

Saya menguji penjelasan ini dengan angka. Untuk setiap foto saya hitung rata-rata perubahan terang antar pixel yang bertetangga pada resolusi penuh (makin besar, makin banyak detail dan noise). Korelasinya dengan ukuran file **0,98**, hampir sempurna. Menariknya, kalau detail yang sama diukur pada versi kecil, korelasinya hanya 0,35. Artinya, yang membesarkan file adalah detail sangat halus di resolusi penuh, termasuk noise sensor, yang sudah hilang ketika fotonya diperkecil.

ISO juga ikut berperan. Rata-rata ukuran file: ISO 250 = 6.214.999 B, ISO 320 = 6.674.430 B, ISO 400 = 7.191.786 B. ISO yang lebih tinggi menambah noise, dan noise adalah detail yang sulit dikompres. Tapi ini tidak bisa saya pisahkan sepenuhnya, karena foto ber-ISO 400 kebetulan juga diambil dari sisi dengan latar yang berbeda. Jadi kesimpulan yang jujur: ukuran file mengikuti banyaknya detail halus di resolusi penuh, dan noise dari ISO tinggi kemungkinan besar ikut menyumbang.

Itulah sebabnya foto langit polos dan foto dedaunan ramai bisa berbeda ukurannya walaupun resolusinya sama persis: setelah dibuka, keduanya sama-sama 109.734.912 B, tapi yang tersimpan di disk tergantung seberapa "ramai" isinya.

## Bacaan referensi (Lab 1 nomor 5)

**Tulisan eksternal: desain viridis** (https://bids.github.io/colormap/ dan dokumentasi colormap matplotlib). Perbedaan terbesar dengan kode Modul 1 saya ada pada cara mengukur "seberapa beda" dua warna. Tim viridis mengukurnya di ruang warna perseptual CAM02-UCS, sehingga langkah warna yang sama besar memang terlihat sama besar oleh mata. Kode saya belum punya ruang perseptual sama sekali: `luma.py` hanya menghitung kecerahan dengan bobot Rec. 709, dan `cvd.py` mensimulasikan buta warna dengan satu matriks 3 × 3 pada RGB linear. Untuk tugas modul ini cukup, karena yang diuji adalah apakah dua warna runtuh menjadi sama. Tapi untuk merancang palet yang langkahnya rata, seperti viridis, kode saya perlu ruang warna perseptual seperti CAM02-UCS atau OKLab.

**Buku Marschner & Shirley Bab 3 (Raster Images):** *bagian ini saya isi setelah membaca babnya sendiri.*

## Refleksi kasus (Lab 1 nomor 6)

**(a) Cacat visual dan penyebabnya.** Pada kasus gamma (Gritz & d'Eon, GPU Gems 3 Bab 24, Agustus 2007), menghitung di ruang ter-encode gamma membuat level mipmap kecil tampak lebih gelap dan berdenyut saat berganti level (operasi filtering), membuat tepi blending salah (operasi blending), dan membuat bayangan terlalu tajam serta sudut terlalu gelap (operasi lighting). CSS Color 4 mencatat gejala yang sama pada gradien: interpolasi di ruang sRGB menghasilkan campuran yang "overly dark or greyish". Pada kasus colormap (matplotlib 2.0, 17 Januari 2017), jet membuat pita dan batas palsu karena kecerahannya naik-turun, dan sulit dibaca oleh penderita buta warna merah-hijau maupun ketika dicetak hitam putih.

**(b) Baris perbaikan di `resample.py`.** Perbaikannya ada di fungsi `box_downscale_2x`, baris 77:

```python
f = srgb_to_linear(f)                 # <-- the line the bug omits
```

Baris ini mengubah kode sRGB menjadi linear light sebelum dirata-ratakan, dan baris 83 (`f = linear_to_srgb(f)`) mengembalikannya ke sRGB setelahnya. Program `prepare_photos.py` saya memakai urutan yang sama untuk memperkecil foto.

**(c) Pemeriksaan untuk kasus colormap.** Ubah colormap ke grayscale dan plot kecerahannya dari ujung ke ujung: kalau garisnya naik-turun, colormap itu akan menipu. Lalu jalankan simulasi deuteranopia dan protanopia dengan `cvd.py`: kalau dua warna yang berbeda di data menjadi sama, colormap itu gagal.

**(d) Satu perubahan yang mengurangi risiko.** Tambahkan pemeriksaan buta warna ke `make test`, sehingga setiap palet atau chart di proyek ini otomatis diuji dengan simulasi deuteranopia dan protanopia, dan test gagal kalau dua kategori runtuh menjadi warna yang sama. Dengan begitu kesalahan seperti jet ketahuan sebelum hasilnya dilihat orang lain.

Sumber: Gritz, L. & d'Eon, E. (2007). "The Importance of Being Linear", GPU Gems 3 Bab 24; W3C CSS Color Module Level 4 §13.2; pengumuman rilis matplotlib 2.0.0 (17 Januari 2017); Smith, N. & van der Walt, S., "A Better Default Colormap for Matplotlib", SciPy 2015 (8 Juli 2015).

## Keterbatasan

1. Exposure tidak dikunci, jadi ISO berubah antara 250 dan 400. Kecerahan dan tingkat noise antar foto tidak sepenuhnya sama.
2. Pengaruh ISO dan pengaruh isi latar terhadap ukuran file tidak bisa dipisahkan dari data ini, karena foto ber-ISO tinggi juga yang latarnya berbeda.
3. Versi kerja di `data/` berukuran 907 × 1612, bukan resolusi asli, supaya repo tetap ringan. Hitungan budget tetap memakai resolusi asli 4536 × 8064.
