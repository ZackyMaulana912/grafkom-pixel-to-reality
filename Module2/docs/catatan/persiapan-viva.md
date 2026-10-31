# Persiapan viva Modul 2

Viva meminta empat hal:

1. menjalankan `node tests.mjs` secara langsung;
2. membuka halaman yang ter-hosting;
3. menjelaskan satu commit saya sendiri;
4. menjawab "kenapa ini dan bukan itu?" serta "bagaimana kalau targetnya WebGPU atau canvas 4K?".

## Urutan demo (sekitar 3 menit)

1. `cd Module2/Source`, lalu `nvm use` dan `node tests.mjs`. Tunjukkan 23 baris `OK` dan `ALL CHECKS PASSED (23 ok, 0 fail)`.
2. Buka https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module2/Source/web/. Tunjukkan denah ruangan, lalu nyalakan "Simulasi deuteranopia": kelima kategori masih bisa dibedakan dari kecerahan, label, dan bentuk marker-nya.
3. Kalau diminta test yang bisa gagal: `node triangle_gap_bug.mjs --diagnose` menunjukkan 6 pixel dobel dan 6 celah tanpa aturan. Ceritakan juga bahwa 4 test baru terbukti gagal kalau `triangle()` starter dipasang kembali.

## Commit yang saya jelaskan

**Pilihan utama: perbaikan `triangle()` dengan fixed-point.**

- **Masalahnya:** bias −1 di aturan top-left starter membuang pixel yang jelas di dalam segitiga.
- **Bagaimana saya tahu:** saya membuat referensi independen yang menguji setiap pixel dengan aturan yang ditulis apa adanya, lalu membandingkannya di 1.934 segitiga acak. Hasilnya 34 segitiga kehilangan 42 pixel, dan semuanya punya nilai edge terkecil tepat 0,5.
- **Penyebabnya:** pusat pixel ada di x + 0,5, jadi E = Δx·k − Δy·m + (Δx − Δy)/2, dan bagian ½ muncul kalau Δx − Δy ganjil. Bias −1 hanya mengubah "≥ 0" menjadi "> 0" kalau E bilangan bulat. Contoh nyatanya pixel (2,14) di segitiga (16,0), (4,23), (2,12): E_BC = 0,5, lalu 0,5 − 1 < 0, jadi ditolak.
- **Perbaikannya:** vertex dibulatkan ke grid 1/256 pixel (GPU melakukan hal yang sama dengan bit sub-pixel), sehingga pusat pixel = 256x + 128 dan semua E bilangan bulat.
- **Buktinya:** diagnosis di-commit lebih dulu, lengkap dengan 5 prediksi, dan kelimanya tepat. Sweep 0 berbeda, `tri_t8_ref.ppm` max |diff| 0, dan referensi dosen tetap 144/144.

**Cadangan: perbaikan viewer (T3 dan T4).** Bukti angkanya: 71,48% identik sebelum diperbaiki, dan 99,985% sesudahnya.

## "Kenapa ini dan bukan itu?"

**Kenapa fixed-point 1/256, bukan cukup koordinat dikali 2?**
Dikali 2 hanya benar untuk vertex integer. Dengan 256, vertex pecahan (misalnya setelah zoom) juga punya nilai E yang bulat, dan cara ini sama dengan grid sub-pixel GPU. Batasnya aman: nilai terbesar di denah saya sekitar 10¹¹, sedangkan 2⁵³ ≈ 9 × 10¹⁵.

**Kenapa default `fillRule` tetap rumus modul, padahal GPU memakai cerminannya?**
Referensi `square_fill_ref.ppm` dari dosen dibuat dengan rumus modul, dan saya tidak mau mengubah test supaya lolos. Keduanya sama-sama rapat. Bedanya hanya siapa yang memiliki pixel tepat di tepi, dan opsi `"gpu"` terbukti cocok 144/144 dengan WebGL.

**Kenapa auto-flip winding sebagai perbaikan pitfall, bukan clamp bounding box atau antialiasing Wu?**
Clamp bounding box sudah ada di starter. Winding berhubungan langsung dengan denah saya: titik lantai di JSON berurutan berlawanan jarum jam, sehingga totalnya −135.200, dan `triangle()` starter menggambar **0** pixel. Masalah yang sama (segitiga membelakangi kamera) juga penyebab T3 di Three.js.

**Kenapa `DoubleSide`, bukan membalik urutan titik?**
`ShapeGeometry` membereskan arah outline sendiri (`isClockWise`, lalu `reverse`), jadi membalik urutan di JSON tidak berpengaruh. Yang membalik adalah kamera y-ke-bawah, dan denah datar tidak punya sisi belakang.

**Kenapa +0,5 hanya untuk garis, tidak untuk lantai?**
Pixel Bresenham (x, y) adalah sampel di (x + 0,5; y + 0,5), jadi garis harus lewat di situ. Sudut lantai harus tetap di batas pixel, supaya pixel diisi kalau pusatnya di dalam, sama dengan `triangle()`. Kalau lantai ikut digeser, sisi kanan dan bawahnya bertambah satu pixel.

**Kenapa forward untuk viewer?**
0,04 ms vs 25 ms di zoom 1×, sekitar 600 kali lebih cepat, dan biayanya mengikuti panjang garis. Backward 25 ms sudah melewati jatah 16,7 ms untuk 60 fps.

**Kenapa angka bench di PDF menunjukkan backward lebih cepat di 10×?**
Itu efek urutan pengukuran. Zoom yang diukur pertama ikut menanggung pemanasan JIT V8. Saya buktikan dengan membalik urutannya: yang pertama selalu lambat. Setelah diperbaiki, 1× dan 10× sama-sama sekitar 25 ms.

**Kenapa PPM, bukan PNG, untuk export Three.js?**
Membaca PNG di `compare.mjs` butuh package `pngjs`, sedangkan bagian dari-nol tidak boleh memakai package. Untuk README saya menulis encoder PNG sendiri dengan `node:zlib`.

**Kenapa matriks CVD dibaca dari `index.html`?**
Supaya yang diuji persis yang diterapkan halaman. Saya juga mencocokkan hasilnya dengan screenshot Chrome (selisih paling banyak 1 kode), dan dari situ ketahuan filter SVG bekerja di linear light, sedangkan `grayscale()` CSS bekerja di kode sRGB.

## "Bagaimana kalau targetnya WebGPU?"

Yang **tetap**:

- konvensi pusat pixel di +0,5 (sama dengan D3D10+, Vulkan, dan Metal);
- sample-centre, edge function, dan aturan tepi yang memberi pixel ke tepat satu segitiga;
- seluruh `raster.mjs` sebagai referensi untuk dicocokkan pixel demi pixel.

Yang **berubah**:

1. Tidak ada Three.js `WebGLRenderer`. Kalau tetap memakai Three.js, ada `WebGPURenderer`, dan kalau WebGPU mentah, saya menulis shader WGSL sendiri.
2. **Ruang koordinat.** Clip space WebGPU punya z 0..1, bukan −1..1. Framebuffer koordinatnya y ke bawah seperti `raster.mjs`, sedangkan WebGL y ke atas, jadi flip di export (`readPixels` bottom-up) tidak diperlukan lagi.
3. **Garis.** WebGPU hanya punya garis 1 pixel (`line-list`, `line-strip`), tanpa pengaturan ketebalan dan tanpa jaminan antialiasing garis. Untuk garis tebal harus membangun quad dari segitiga.
4. **Culling dan winding** diatur eksplisit lewat `frontFace` dan `cullMode`. Masalah T3 bisa muncul lagi dalam bentuk yang sama.
5. **Format warna.** Format canvas (`bgra8unorm` atau `rgba8unorm`) dan apakah view-nya `-srgb` menentukan apakah blending dan resolve MSAA terjadi di linear light atau di kode sRGB. Itu yang membuat campuran (43,10,53) vs sekitar 50.

## "Bagaimana kalau canvas 4K?"

3840 × 2160 = 8.294.400 pixel, 17,3 kali 800 × 600.

- **Memori framebuffer:** RGB 8-bit 24.883.200 B (24,88 MB = 23,73 MiB) per frame, dan RGBA (yang dipakai WebGL) 33.177.600 B. Dengan MSAA 4×, buffer warnanya 4 kali.
- **Backward** naik sebanding jumlah pixel: sekitar 17 × 25 ms ≈ 440 ms per frame untuk denah saya. Sama sekali tidak interaktif.
- **Forward** hampir tidak berubah kalau skala denahnya sama. Kalau denah diperbesar memenuhi layar 4K (skala sekitar 4 sampai 5 kali), langkah Bresenham ikut naik sekitar 4 sampai 5 kali, dan itu tetap di bawah 1 ms.
- **`devicePixelRatio`.** Di layar 4K yang di-scale 2×, canvas 800 × 600 CSS menjadi 1600 × 1200 pixel fisik. Karena itu `setPixelRatio(1)` dan `setSize` eksplisit tetap wajib sebelum export, kalau tidak `compare.mjs` akan menolak karena ukurannya berbeda.
- **Garis 1 pixel** di 4K terlihat sangat tipis, sehingga denah perlu garis tebal (`Line2` di Three.js), dan perbandingan pixel dengan Bresenham harus memakai rasteriser garis tebal juga.

## Pertanyaan lain yang mungkin muncul

**Kenapa denahnya ruangan, bukan bangunan bersejarah?** Subjek saya sejak Modul 1 adalah patung kuda milik sendiri, dan patung tidak punya denah. Ruangan tempat patung berdiri adalah denah nyata yang bisa saya ukur sendiri. Patungnya tetap ada di denah. Ini perlu saya konfirmasi ke dosen.

**Apa arti PSNR 52,7 dB di sini?** MSE-nya sangat kecil, karena hanya 71 dari 480.000 pixel yang berbeda. PSNR saja menyesatkan: dengan bug T4 nilainya masih 31,1 dB. Karena itu saya menjelaskan setiap pixel yang berbeda.

**Kenapa 0,5 bisa muncul sebagai nilai E?** E = Δx·(k + ½) − Δy·(m + ½) = bilangan bulat + (Δx − Δy)/2.

**Kenapa Bresenham saya berbeda dari starter di 6.725 segmen?** Itu kasus seri D = 0: dua pixel sama-sama berjarak 0,5 dari garis. Saya memilih tidak naik, starter memilih naik. Keduanya benar.
