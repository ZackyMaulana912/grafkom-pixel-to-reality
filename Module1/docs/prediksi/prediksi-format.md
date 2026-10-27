# Prediksi format (ditulis sebelum mengukur)

File ini saya tulis **sebelum** menjalankan `format_compare.py` pada crop dari foto saya. Pengukurannya baru dijalankan setelah file ini di-commit, supaya riwayat git menunjukkan prediksinya lebih dulu. Prediksi yang meleset tidak akan saya ubah. Saya akan menjelaskan kenapa meleset di catatan Fase 5.

## Dua crop yang dipakai

Keduanya berukuran 256 × 256 pixel, sehingga setelah dibuka (decode) sama-sama 196.608 B (256 × 256 × 3). Keduanya dipotong dari versi kerja foto saya (907 × 1612, sRGB).

| Crop | Asal | Isi |
|---|---|---|
| `crop_dinding` | IMG_8884, x 100, y 50 | dinding polos krem di belakang patung, warnanya hampir rata dengan sedikit noise sensor (simpangan sekitar 5 sampai 6 kode per channel) |
| `crop_surai` | IMG_8893, x 300, y 400 | surai patung yang berukir, penuh guratan pahat sejajar yang berulang, dengan tepi terang-gelap yang tajam |

Format yang diuji `format_compare.py`: PNG, WebP lossless, JPG q92, WebP q92, JPG q75, JPG q40, dan AVIF q40.

## Prediksi untuk crop dinding (halus)

1. **Format terkecil: AVIF q40**, lalu JPG q40. Semua format lossy akan jauh lebih kecil dari format lossless.
2. **PNG dan WebP lossless tidak akan sekecil yang dibayangkan untuk dinding "polos".** Dinding ini tidak benar-benar rata, karena ada noise sensor beberapa kode di setiap pixel, dan noise tidak pernah berulang persis. Perkiraan saya, rasio PNG hanya sekitar 2× sampai 4×, dan WebP lossless sedikit lebih baik dari PNG.
3. **JPG q92 sekitar 10× sampai 25×**, dengan PSNR di atas 40 dB. **JPG q40 di atas 40×**, dengan PSNR sekitar 35 sampai 40 dB.
4. **Artefak:** hampir tidak terlihat di q92 dan q75. Di q40 mungkin mulai muncul kotak-kotak 8 × 8 yang samar (blocking) di gradasi dinding, karena noise halusnya dibuang dan setiap blok menjadi rata.

## Prediksi untuk crop surai (berfrekuensi tinggi)

1. **Format terkecil tetap AVIF q40**, lalu JPG q40. Tapi setiap format akan menghasilkan file yang **jauh lebih besar** daripada crop dinding pada pengaturan yang sama, menurut saya minimal 3 kali lipat.
2. **PNG dan WebP lossless hanya sekitar 1,5× sampai 2×.** Guratan pahat adalah informasi sungguhan, bukan pola yang berulang persis, jadi kompresi lossless hampir tidak bisa memadatkannya.
3. **JPG q92 sekitar 4× sampai 8×** dengan PSNR sekitar 36 sampai 40 dB. **JPG q75 sekitar 8× sampai 15×**, sekitar 32 sampai 36 dB. **JPG q40 sekitar 15× sampai 30×**, sekitar 28 sampai 32 dB.
4. **Artefak JPEG yang saya perkirakan:**
   - *ringing* (bayangan bergelombang) di sepanjang tepi setiap guratan, karena tepi tajam butuh frekuensi tinggi yang dibuang JPEG,
   - *blocking* pada grid 8 × 8, terutama di bagian surai yang gelap,
   - guratan yang paling halus menjadi rata atau menyatu,
   - warna jingga di sela guratan sedikit meluber, karena informasi warna disimpan dengan resolusi lebih rendah.
5. **Kualitas saat artefak mulai terlihat:** samar di q75, dan jelas di q40. Di q92 seharusnya belum terlihat dengan mata biasa.

## Urutan ukuran file yang saya perkirakan (sama untuk kedua crop)

PNG > WebP lossless > JPG q92 > WebP q92 > JPG q75 > JPG q40 > AVIF q40

Bagian yang paling tidak saya yakini adalah posisi WebP q92 terhadap JPG q92. Saya menebak WebP lebih kecil pada angka kualitas yang sama, tapi angka kualitas di kedua format tidak berarti hal yang sama persis.

## Prediksi untuk perbandingan downscale (Lab 3 nomor 2)

Saya juga akan memperkecil satu foto 2× dengan tiga cara: cara benar di linear light, cara naif pada kode sRGB, dan `resize(Image.BOX)` bawaan Pillow. Prediksi saya, **Pillow BOX akan meniru bug-nya**, karena Pillow merata-ratakan nilai 8-bit apa adanya tanpa decode ke linear. Hasilnya akan hampir sama dengan cara naif (paling banyak beda 1 kode karena pembulatan), dan PSNR keduanya terhadap cara benar akan sama-sama rendah.
