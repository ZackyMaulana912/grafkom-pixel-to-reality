# Persiapan viva Modul 3

## Yang akan diminta langsung

1. **Jalankan `python tests.py`** dari `Module3/Source` (aktifkan `.venv` dulu). Hasilnya harus `ALL CHECKS PASSED (17 ok, 0 fail)` dalam sekitar 1 detik. Kalau `data/pusaka_model.obj` belum ada, jalankan `python make_model.py` dulu.
2. **Orbit model di halaman ter-hosting.** Buka URL GitHub Pages, seret untuk memutar, scroll untuk zoom, lalu tekan "Kamera awal" untuk kembali ke kamera yang sama dengan render NumPy.
3. **Jelaskan satu commit.** Pilihan terbaik: commit yang berisi diagnosis dan prediksi, karena menunjukkan urutan kerja yang diminta modul (bukti dulu, tulis diagnosis, baru perbaikan). Setelah itu commit perbaikan yang membalik label inside-out (T13).

## Pertanyaan yang mungkin muncul

**Kenapa urutannya `P · V · M · p`?**
Column vector, jadi dibaca dari kanan: titik dipindah dulu ke world (M), lalu ke ruang kamera (V), lalu ke clip space (P). Di dalam M sendiri urutannya `T · Ry · S`: skala dulu di ruang model, lalu putar, lalu pindahkan. Kalau skala dikerjakan setelah rotasi, ia meregang di sumbu world, bukan di sumbu model. Bug stretched saya temukan justru dengan membaca panjang kolom M.

**Kenapa handedness ini?**
Mengikuti OpenGL dan Three.js: right-handed, kamera menghadap −z. Viewer saya memakai Three.js, jadi konvensinya harus sama supaya frame-nya bisa dibandingkan pixel demi pixel. Konsekuensinya, titik di depan kamera punya z negatif, sehingga `w = −z`, dan segitiga sebangun memberi `dx/|z|`, bukan `dx/z`. NDC sendiri left-handed, karena proyeksi membalik z (near −1, far +1).

**Apakah `w` benar-benar `−z`?**
Ya, dan sudah saya cek di satu vertex: telinga patung punya z_eye = −1,559007 dan w = 1,559007. Baris 4 matriks proyeksi adalah (0, 0, −1, 0). Mutasi test membuktikannya juga: kalau baris itu diubah menjadi `w = +z`, E3 gagal.

**Kenapa near = 0,1 m dan far = 10 m?**
Far 10 m sudah cukup untuk ruangan 4 m. Near 0,1 m karena kamera berdiri di dalam ruangan dekat dinding: near yang lebih besar akan memotong dinding di dekat kamera dan membuat lubang. Harganya, 90,9% kode depth habis di meter pertama. Tapi di jarak patung (1,56 m) satu langkah depth 24-bit masih 0,0014 mm, jauh lebih kecil dari benda apa pun di scene. Kalau scene-nya dibuat jauh lebih besar, near harus dinaikkan, atau pakai reverse-Z + float (0 pixel salah di scene zfight).

**Kenapa clipping sebelum pembagian w?**
Di belakang kamera w ≤ 0, jadi x/w meledak atau berbalik tanda, dan segitiga tercoreng di seluruh layar. Di clip space semuanya masih linear, jadi titik potong dengan `z + w = 0` bisa dihitung dengan interpolasi biasa. Di model saya, 71 segitiga benar-benar terpotong dan 51 seluruhnya di belakang kamera.

**Kenapa depth diinterpolasi linear tapi UV tidak?**
NDC z = A + B/w, affine terhadap 1/w, dan 1/w linear di layar. UV tidak linear di layar, jadi yang diinterpolasi adalah u/w dan 1/w, lalu dibagi. Contoh E4: 0,1 bukan 0,5. Di lantai saya, UV naif membuat texture meluncur 27 cm saat kamera maju 10 cm.

**Bagaimana kalau targetnya Direct3D?**
Ada empat hal yang berubah:

1. **Handedness:** D3D left-handed. Balik urutan vertex (v0, v2, v1) dan skala z dengan −1 di view matrix, sesuai dokumen Microsoft "Coordinate Systems (Direct3D 9)".
2. **Urutan matriks:** row vector, jadi `p · M · V · P` dan matriksnya ditranspose.
3. **Rentang NDC z:** [0, 1], jadi baris 3 matriks proyeksi berubah.
4. **Origin UV:** kiri atas, jadi flip v di loader dihapus.

Test `det(M) > 0` dan signed volume di `tests.py` akan menangkap kalau salah satu langkah port terlewat dan dunianya tercermin.

**Bagaimana kalau canvas-nya 4K?**
Pixel naik 64 kali dibanding 512 × 512. Dari pengukuran saya, ray tracer naik hampir sebanding dengan jumlah pixel (3,97× untuk 4× pixel), jadi sekitar 1,5 s × 64 ≈ 96 s per frame. Raster naik lebih pelan, karena ongkos per segitiga tetap (2,5× untuk 4× pixel). Tiga kali lipat 2,5× memberi 0,162 × 2,5³ ≈ 2,5 s, dan batas atasnya 0,162 × 64 ≈ 10 s kalau seluruh biayanya bergantung pada pixel. Jadi perkiraannya sekitar 2,5–10 s. Ini perkiraan dari skala yang terukur, belum diuji langsung di 4K. Di WebGL, 4K masih real-time untuk 394 segitiga. Yang perlu diperhatikan adalah `setPixelRatio`: di layar retina, canvas bisa diam-diam 2 kali lebih besar, jadi saya memasang `setPixelRatio(1)` dan `setSize` eksplisit sebelum Export PPM.

**Kenapa raster vs ray tracer di candi tidak identik, padahal di model saya identik?**
Temuan T14: di candi ada sisi kotak dengan u = 1 persis. `np.mod(1.0, 1)` = 0, sehingga sampel diambil dari sisi texture yang berseberangan, sedangkan ray tracer bisa mendapat 0,9999999999999999. Hasilnya ditentukan pembulatan floating-point, jadi berbeda di Mac saya (68,1 dB), di Linux (76,5 dB), dan di PDF (76,9 dB). UV model saya dimundurkan 1 texel dari tepi atlas, jadi tidak pernah menyentuh 0 atau 1.

**Kenapa WebGL starter tiga kali lebih gelap?**
Three.js sejak r155 memakai lampu fisik: `BRDF_Lambert` = albedo/π (saya baca di `three.module.js` r160), sedangkan rasteriser memakai albedo · cos. Di Mac saya rasionya 3,12 di linear light. Perbaikannya: intensitas lampu dikali π. Ditambah filter linear dan pusat texel yang disamakan, PSNR naik dari 11,4 ke 40,4 dB.

**Apa yang membuat diagnosismu berbeda dari jawaban starter?**
Untuk inside-out, starter salah: yang disebut rusak justru identik dengan kebenaran, karena data candinya ber-winding ke dalam (signed volume −2,976). Untuk stretched, starter menyebut "urutan tertukar", padahal menukar skala seragam dan rotasi tidak mengubah apa pun. Penyebabnya faktor skala tidak seragam, yang terbaca dari panjang kolom 3,08 / 0,70 / 1,40.

**Kenapa memilih reverse-Z untuk perbaikan pitfall?**
Karena `cull_back` sudah ada di starter, dan perbaikan normal matrix tidak akan terlihat di rasteriser ini (normal dihitung dari posisi world yang sudah ditransformasi). Reverse-Z + float32 menyelesaikan scene zfight tanpa mengubah near: 2.852 → 0 pixel salah. Reverse-Z dengan 16-bit fixed tetap 2.852, karena fixed point berjarak sama rata. Jadi kedua perubahan Reed harus dipakai bersamaan.

**Kalau modelnya 200.000 segitiga?**
Yang rusak pertama adalah renderer NumPy: loop Python per segitiga sekitar 0,4 ms, jadi sekitar 80 s per frame untuk raster dan sekitar 13 menit untuk ray tracer tanpa BVH. WebGL tetap real-time. Yang terasa di WebGL adalah memuat dan mem-parse OBJ teks yang besar, jadi format biner (glTF) lebih tepat.

**Dari mana ukuran modelmu?**
Ukuran ruangan, tinggi dinding, lemari, sekat, dan alas patung adalah ukuran saya. Tinggi patung 45 cm diperkirakan dari foto dengan panjang alas 30 cm sebagai penggaris. Tebal badan, letak, dan arah patung, serta susunan rak sekat adalah perkiraan. Semuanya ditandai di `docs/model/README.md`.
