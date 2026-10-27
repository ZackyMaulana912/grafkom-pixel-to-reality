# Kebijakan format (Lab 3 nomor 3)

Dasar angka: `format_compare.py` pada dua crop 256 × 256 dari foto saya (`report/formats_crop_dinding.md` dan `report/formats_crop_surai.md`), dan `downscale_compare.py` (`report/downscale_compare.md`). Ukuran setelah decode setiap crop 196.608 B.

| Kegunaan | Format | Kualitas | Alasan (dengan angka) |
|---|---|---|---|
| Arsip | PNG, ditambah file JPG asli dari kamera yang disimpan tanpa diubah | lossless | Satu-satunya pilihan dengan PSNR tak hingga. Arsip harus bisa dipakai ulang untuk apa pun, jadi tidak boleh ada yang hilang, walaupun di crop surai PNG hanya 1,97× (99.593 B). WebP lossless 27% lebih kecil (73.108 B), tapi PNG lebih luas didukung untuk jangka panjang. |
| Hero image web | WebP | q92 | Di crop surai WebP q92 berukuran 15.984 B dengan PSNR 41,2 dB, lebih kecil 17% dan lebih tajam daripada JPG q92 (19.208 B, 40,5 dB). Di crop dinding hanya 908 B (216×). |
| Thumbnail | JPG | q75, diperkecil dulu dengan cara linear | Di crop surai 10.136 B (19,4×) dengan PSNR 36,8 dB, dan artefaknya baru samar. Perkecilnya wajib di linear light, karena Pillow `Image.BOX` meniru bug gamma (beda paling banyak 1 kode dari cara naif) dan hasilnya berbeda sampai 26 kode dari cara benar di tepi patung pada IMG_8884. |
| Sumber texture Modul 3 | PNG 8-bit sRGB | lossless | Texture akan di-resample dan dibuat mipmap berkali-kali, jadi artefak lossy ikut menumpuk. Di JPG q40 loncatan di batas blok 8 × 8 sudah 6,52 kode, dibanding 3,73 kode di dalam blok. Kompresi untuk GPU baru dilakukan di Modul 3. |
| Video flythrough | MP4 / H.264 | sekitar 8 Mbit/s pada 1920 × 1080, 30 fps | Satu-satunya pilihan di daftar yang menyimpan video. Tanpa kompresi, flythrough 10 detik pada resolusi foto saya butuh 26.336,38 Mbit/s (32,92 GB). Menurut contoh E6 di modul, H.264 sekitar 187 kali lebih kecil daripada video 1080p tanpa kompresi. Format ini tidak saya ukur sendiri di lab ini. |

**Kenapa jawaban arsip berbeda dari jawaban termurah.** Format termurah di kedua crop adalah AVIF q40 (2.788 B di surai, 70,5×), sedangkan untuk arsip saya memilih PNG yang 36 kali lebih besar (99.593 B). Arsip menjaga **kemungkinan** di masa depan: kalau suatu saat foto ini perlu dipotong, diwarnai ulang, atau dijadikan texture, semua informasinya masih ada. File lossy hanya menjaga **tampilan** untuk satu ukuran layar. Setelah informasi dibuang, tidak ada cara untuk mengembalikannya.
