# Prediksi: rasterisation vs ray tracing pada model saya (ditulis sebelum diukur)

Lab 3 no 3 meminta prediksi tertulis **sebelum** menjalankan pengukuran. File ini saya commit sebelum `raytrace.py` dipakai untuk merender model saya dan sebelum `bench.py` ada. Urutan commit di git menjadi buktinya.

Yang sudah saya jalankan sebelum menulis ini, dan apa yang tidak:

- **Sudah:** `raster3d.py` (kode asli dosen) untuk memilih kamera model saya, tanpa mencatat waktu. Ray tracer hanya untuk candi bawaan (mencocokkan dengan PDF), juga tanpa mencatat waktu.
- **Belum:** frame time apa pun, dan render ray tracer untuk model saya.
- PDF modul **tidak memberi angka frame time**, hanya PSNR/SSIM. Jadi tidak ada angka dari mesin dosen yang bisa saya contek.

## Fakta model yang dipakai untuk menghitung

Scene `scenes/mymodel.json`, frame 512 × 512 = 262.144 pixel. Angka di bawah dihitung dari geometri (proyeksi titik saja), bukan dari pengukuran waktu.

| | Model saya | Candi bawaan |
|---|---|---|
| Segitiga | 394 | 180 |
| Segitiga yang seluruhnya di depan near plane | 272 | 180 |
| Segitiga yang memotong near plane (harus di-clip) | 71 | 0 |
| Segitiga yang seluruhnya di belakang kamera | 51 | 0 |
| Total luas kotak pembatas di layar (segitiga yang tidak di-clip) | 1.103.670 pixel | 1.255.845 pixel |
| Uji ray-segitiga untuk ray tracer (pixel × segitiga) | 103.284.736 | 47.185.920 |

## Model biaya

**Rasteriser (`raster3d.py`).** Ada satu loop Python per segitiga. Untuk tiap segitiga, NumPy menghitung edge function, depth, `1/w`, dan UV di **seluruh kotak pembatasnya**, lalu mengambil sampel texture. Biayanya kira-kira:

> waktu ≈ (jumlah segitiga × ongkos tetap per segitiga) + (total luas kotak pembatas × ongkos per pixel)

Segitiga yang memotong near plane di-clip dulu dan bisa menjadi dua segitiga. Di model saya, segitiga-segitiga itu adalah dinding dan lantai di dekat kamera, dan setelah di-clip kotaknya bisa hampir selebar layar. Jadi total luas kotak sebenarnya lebih besar dari 1,1 juta. Perkiraan saya 1,5 sampai 2 juta pixel.

**Ray tracer (`raytrace.py`).** Juga satu loop Python per segitiga, tapi setiap segitiga diuji terhadap **semua** 262.144 ray (Möller–Trumbore tervektorisasi). Biayanya:

> waktu ≈ jumlah segitiga × jumlah pixel × ongkos per uji

Tidak ada struktur percepatan (BVH atau grid), jadi segitiga kecil di pojok layar sama mahalnya dengan lantai yang memenuhi layar.

Perbedaan pentingnya: biaya rasteriser mengikuti **seberapa besar segitiga di layar**, sedangkan biaya ray tracer mengikuti **jumlah segitiga dikali jumlah pixel**. Model saya punya banyak segitiga kecil (rak sekat 108 segitiga, badan patung 216 segitiga), dan masing-masing tetap menelan 262.144 uji di ray tracer.

## Prediksi (i): frame time pada 512 × 512 di Mac saya (Apple M5)

| Renderer | Prediksi | Alasan |
|---|---|---|
| `raster3d.py` | **0,4 s** (rentang 0,2 sampai 1,0 s) | 394 iterasi loop, sekitar 1,5 sampai 2 juta pixel kotak, sekitar 20 operasi array per pixel |
| `raytrace.py` | **5 s** (rentang 3 sampai 12 s) | 103 juta uji. Satu uji butuh beberapa operasi array (cross product, dua dot product, empat pembanding), dan setiap segitiga juga memperbarui buffer UV untuk 262.144 pixel |
| Rasio ray tracer / raster | **sekitar 12×** (rentang 5× sampai 30×) | |

Prediksi tambahan:

- **Rasio di model saya lebih besar daripada di candi** pada ukuran yang sama. Uji ray tracer naik 2,2 kali (394 vs 180 segitiga), sedangkan luas kotak rasteriser hampir sama.
- **Kalau ukuran frame dinaikkan 2 kali per sisi** (4 kali pixel), ray tracer naik hampir tepat 4 kali, sedangkan rasteriser naik kurang dari 4 kali, karena ongkos tetap per segitiga tidak ikut membesar.

## Prediksi (ii): shadow dan reflection

- **Ray tracer memberi shadow dan reflection yang lebih baik.** Hard shadow cukup satu ray tambahan dari titik kena ke arah lampu. Hasilnya tepat per pixel, tanpa resolusi peta bayangan, tanpa shadow acne, dan tanpa tepi bergerigi. Reflection juga sama: satu ray pantul. Biayanya, setiap efek menambah satu putaran uji lagi. Hard shadow saya perkirakan membuat ray tracer **sekitar 2 kali lebih lambat**, karena ray bayangan juga diuji ke semua 394 segitiga.
- **Rasteriser butuh trik untuk shadow:** render tambahan dari arah lampu ke shadow map, lalu setiap fragment dibandingkan dengan peta itu. Kualitasnya bergantung pada resolusi peta dan bias. Saya perkirakan muncul tepi bergerigi dan bayangan yang sedikit bergeser di kaki patung dan rak. Tambahan waktunya kecil, kira-kira satu render depth lagi, jadi **sekitar 1,3 sampai 1,6 kali**. Reflection yang tepat tidak bisa dibuat dengan rasterisation biasa. Yang ada hanya pendekatan (environment map, screen-space reflection).
- Di scene saya, bayangan yang paling terlihat seharusnya bayangan patung di lantai dan bayangan rak sekat. Lampunya datang dari kiri atas, arah (−0,4; 0,9; 0,5).

## Pilihan yang saya perkirakan

- **Viewer real-time:** rasterisation (di browser lewat WebGL/GPU). Bahkan di NumPy pun rasteriser sudah sekitar 10 kali lebih cepat, dan di GPU ia tinggal satu draw call.
- **Beauty shot untuk marketing:** ray tracing, karena satu frame boleh lama asal bayangan dan pantulannya benar.

Setelah file ini di-commit, saya akan membuat `bench.py`, mengukur median beberapa run, lalu menulis bagian mana yang meleset dan kenapa.
