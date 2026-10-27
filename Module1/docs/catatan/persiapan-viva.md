# Persiapan viva Modul 1

Viva meminta empat hal: membuka `report.html`, menjalankan `make test` secara langsung, menjelaskan satu commit saya sendiri, dan menjawab "kenapa ini dan bukan itu?" serta "bagaimana kalau targetnya display HDR 10-bit?". Catatan ini berisi urutan demo dan jawaban yang sudah saya siapkan, lengkap dengan angkanya.

## Urutan demo (sekitar 3 menit)

1. `cd Module1/Source`, lalu `make test`. Tunjukkan 16 baris `OK` dan `ALL CHECKS PASSED`.
2. Buka `Source/report/report.html` di browser. Tunjukkan tiga hal: tabel budget, triptych naif/benar/selisih (relief dan tepi patung), dan legenda CVD sebelum dan sesudah.
3. Kalau diminta menunjukkan test yang bisa gagal: tunjukkan bahwa palet merah-hijau ditolak dengan pesan `deuteranopia 17.7, protanopia 10.5, grayscale 0.0`.

## Commit yang saya jelaskan

**Pilihan utama: perbaikan bilinear di tepi gambar** (pesannya: "Perbaiki perbesaran gambar yang membuat pixel paling pinggir salah nilai, sekarang hasilnya sama dengan Pillow").

- **Apa masalahnya:** memperbesar [0, 100] dua kali di starter menghasilkan [75, 25, 75, 100]. Pixel pertama seharusnya 0.
- **Bagaimana saya tahu starter yang salah, bukan saya:** saya memakai Pillow sebagai pihak ketiga, lalu mengecilkan kasusnya sampai dua sampel saja, sehingga jawabannya bisa dihitung tangan.
- **Penyebabnya:** pusat pixel output pertama jatuh di −0,25. Starter menjepit index kiri ke 0 lebih dulu, lalu mengambil index 1 sebagai tetangga kanan, padahal bobotnya tetap 0,75. Hasilnya 0,25 × 0 + 0,75 × 100 = 75.
- **Perbaikannya:** tentukan dulu kedua tetangga (−1 dan 0), baru jepit. Keduanya menjadi index 0, sehingga hasilnya tepat 0.
- **Buktinya:** test baru `bilinear: identity, constant, edge clamp` lolos di kode saya dan gagal di kode starter.

**Cadangan: dua commit diagnosis lalu perbaikan gamma.** Riwayat git menunjukkan diagnosis di-commit lebih dulu. Diagnosis itu menyatakan "thumbnail = rata-rata kode, 100% persis", lalu commit berikutnya membuktikan bahwa menyalakan langkah decode memulihkan cahaya, dari −23,54% menjadi −0,001%.

## "Kenapa ini dan bukan itu?"

**Kenapa merata-ratakan di linear light, bukan langsung di kode?**
Karena yang dijumlahkan seharusnya cahaya. Kode sRGB 128 hanya sekitar 22% cahaya. Bukti di repo: rata-rata kode membuat thumbnail kehilangan 23,5% cahaya dan lebih gelap 20,24 kode.

**Kenapa Bayer dither, bukan Floyd-Steinberg?**
Bayer tidak memakai angka acak, jadi hasilnya selalu sama, dan bisa dihitung sekaligus untuk seluruh gambar. Floyd-Steinberg menyebarkan sisa pembulatan ke tetangga, jadi harus diproses pixel per pixel. Untuk tujuan menunjukkan banding hilang, Bayer sudah cukup: error lokal turun dari 1,58 ke 0,36 kode.

**Kenapa PNG untuk arsip, bukan AVIF yang 36 kali lebih kecil?**
AVIF q40 membuang informasi untuk selamanya. Arsip harus bisa dipakai untuk apa pun nanti. PNG satu-satunya pilihan dengan PSNR tak hingga yang didukung luas. WebP lossless 27% lebih kecil, tapi dukungannya untuk jangka panjang kalah luas.

**Kenapa WebP q92 untuk hero image, bukan JPG q92?**
Di crop surai, WebP q92 berukuran 15.984 B dengan 41,2 dB, sedangkan JPG q92 19.208 B dengan 40,5 dB. WebP lebih kecil sekaligus lebih tajam.

**Kenapa cek CVD sebagai perbaikan pitfall, bukan pre-filter atau asersi overflow?**
Pre-filter sudah dibahas lengkap di demo aliasing, dan semua primitif yang merata-ratakan sudah memakai float64. Cek CVD menutup celah yang benar-benar ada di starter: legenda yang runtuh tidak pernah membuat test gagal.

**Kenapa versi kecil foto dibuat sendiri dengan NumPy, bukan `Image.resize` Pillow?**
Karena saya membuktikan bahwa Pillow `Image.BOX` meniru bug gamma: hasilnya paling banyak beda 1 kode dari cara naif, dan berbeda sampai 26 kode dari cara benar di tepi patung. Saya juga perlu mengonversi Display P3 ke sRGB, dan konversi saya hanya beda paling banyak 1 kode dari mesin warna Pillow.

**Kenapa summed-area table untuk blur 3×3, bukan loop 9 tetangga?**
Hasilnya sama persis, tapi setiap jumlah jendela hanya butuh 4 angka, dan caranya tetap sama untuk jendela yang lebih besar.

**Kenapa histogram mengurutkan dulu?**
Supaya tidak perlu loop per pixel dan bisa menerima jumlah bin berapa pun. Hasilnya cocok dengan numpy untuk semua 1 sampai 256 bin, dan sekitar 6,6 kali lebih cepat dari starter pada foto saya.

## "Bagaimana kalau targetnya display HDR 10-bit?"

Yang **tetap**: prinsipnya. Operasi seperti merata-ratakan, blending, dan lighting tetap harus dikerjakan di linear light, dengan nilai antara dalam presisi tinggi (float), dan dibulatkan sekali di akhir.

Yang **berubah**:

1. **Kurva transfernya bukan sRGB lagi.** Display HDR memakai kurva lain, misalnya PQ (SMPTE ST 2084) atau HLG. Fungsi `srgb_to_linear` dan `linear_to_srgb` harus diganti dengan decode dan encode untuk kurva itu. Kalau tetap memakai rumus sRGB, hasilnya salah dengan cara yang sama seperti bug thumbnail.
2. **Bit depth naik ke 10.** L = 2^10 = 1024 level, step q = 1/1023 ≈ 0,00098, empat kali lebih halus dari 8-bit (1/255 ≈ 0,0039). Gradien 512 pixel di 10-bit tidak lagi punya pita sama sekali, karena levelnya lebih banyak daripada pixelnya: setiap pixel mendapat level sendiri.
3. **Budget memori naik.** Untuk 1920 × 1080: RGB888 6.220.800 B; RGB 10-bit rapat (30 bit per pixel) 7.776.000 B; format umum RGB10A2 (10 bit per warna plus 2 bit alpha dalam 4 byte) 8.294.400 B. Untuk resolusi foto saya, satu frame RGB 10-bit rapat 137.168.640 B (130,81 MiB), dan flythrough 10 detik 30 fps menjadi 41,15 GB, dari sebelumnya 32,92 GB.
4. **Ruang warnanya lebih luas.** HDR biasanya memakai primary Rec. 2020 atau P3. Foto saya aslinya Display P3, dan sekarang saya potong ke sRGB (0,07% sampai 0,93% nilai terpotong). Untuk target HDR, warna itu sebaiknya dipertahankan, bukan dipotong.
5. **Pilihan format berubah.** JPEG baseline hanya 8 bit per channel, jadi tidak cocok. AVIF mendukung 10-bit dan HDR, dan untuk video perlu codec 10-bit seperti HEVC Main 10, bukan H.264 8-bit biasa.
6. **Test-nya ikut berubah.** Angka seperti "kode 128 = 22% cahaya" atau "naif 128 vs benar 188" khusus untuk sRGB 8-bit. Untuk PQ 10-bit, angka acuannya harus dihitung ulang dari kurva PQ.

## Pertanyaan lain yang mungkin muncul

**Berapa byte satu foto kamu setelah dibuka?** 4536 × 8064 × 3 = 109.734.912 B = 109,73 MB = 104,65 MiB. Di disk IMG_8884 hanya 5.971.188 B, rasionya 18,38×.

**Kenapa MB dan MiB harus dibedakan?** MB = 10^6 byte, dipakai untuk storage dan jaringan. MiB = 2^20 byte, dipakai untuk RAM dan VRAM. Selisihnya sekitar 4,9%, cukup untuk menyembunyikan overflow sungguhan.

**Pola 0,7 cycles/pixel jadi apa?** 0,3 cycles/pixel, karena |0,7 − 1| = 0,3. Terukur persis 0,300 di demo aliasing.

**Kenapa pre-filter box tidak menghapus alias?** Box melemah perlahan, tidak memotong tajam di 0,5. Di 0,6 kekuatannya masih 50,6%, persis sesuai rumus |sin(πf) / (16 sin(πf/16))|.

**Kenapa fotomu dikonversi dari P3 ke sRGB?** iPhone menyimpan Display P3, sedangkan semua kode modul menganggap angkanya sRGB. Kurva gamma keduanya sama, yang berbeda hanya primary-nya, jadi cukup satu matriks 3 × 3 di linear light.

**Kenapa empat foto dibuang?** Skor ketajamannya di bawah setengah median (25%, 28%, 33%, dan 48%), dan potongan resolusi penuhnya memang blur. Modul meminta tidak ada foto yang blur.

**Apa keterbatasan terbesar pekerjaanmu?** Exposure tidak saya kunci saat memotret, jadi ISO berubah antara 250 dan 400. Kebijakan format juga dibuat dari crop versi kerja yang noise-nya jauh lebih rendah daripada foto asli (0,49 vs 1,78 kode).
