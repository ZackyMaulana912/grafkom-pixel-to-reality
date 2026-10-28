# Fase 2: Input denah dan pipeline (Lab 1)

## 1. Denah saya (Lab 1 no 2)

Sumber dan ukurannya ada di `docs/denah/README.md`. Ringkasnya: ruangan 2 × 4 m tempat patung kuda saya berdiri, dengan lemari 8 pintu di dinding kanan, sekat berlubang di sisi masuk, dan jalan masuk di pojok kiri. File-nya `Source/myplan.json`, dengan skema yang sama dengan `pusaka_plan.json` ditambah satu blok `legend`. Hasilnya 14 polyline dan 20 segmen.

![Denah saya, from-scratch](../img/plan_scratch.png)

Dua test baru menjaga file ini:

- semua titik `myplan.json`, setelah `worldToScreen`, berada di dalam 800 × 600;
- lantai mengisi tepat 260 × 520 = 135.200 pixel, setiap pixel sekali, tanpa segitiga yang luasnya nol.

### Urutan warna legenda dan kontras

Lima kategori memakai ramp viridis yang sama dengan starter: ungu gelap, biru, teal, hijau, kuning terang. Awalnya saya urutkan dinding, lemari, sekat, patung, jalan masuk. Setelah denahnya dirender, **panah jalan masuk (kuning) hampir tidak terlihat** di atas lantai yang terang.

Saya menghitung kontrasnya dengan rumus WCAG (luminansi relatif, rasio (L1 + 0,05) / (L2 + 0,05)):

| Kategori | Warna | Di atas lantai (230,236,245) | Di atas latar (18,18,22) |
|---|---|---|---|
| patung | (68,1,84) | 12,83 | 1,23 |
| lemari | (59,82,139) | 6,39 | 2,46 |
| dinding | (33,145,140) | 3,22 | 4,89 |
| sekat berlubang | (94,201,98) | 1,77 | 8,90 |
| jalan masuk | (253,231,37) | 1,06 | 14,80 |

Tidak ada satu warna latar yang cocok untuk kelima warna viridis sekaligus, karena ramp-nya memang membentang dari sangat gelap sampai sangat terang. Jadi urutannya saya atur sesuai **di mana benda itu digambar**:

- patung dan lemari ada di atas lantai, jadi mendapat warna paling gelap;
- dinding ada di batas lantai dan latar, jadi mendapat warna tengah, yang cukup kontras di kedua sisi;
- sekat dan jalan masuk ada di sisi depan yang berbatasan dengan latar gelap, jadi mendapat warna paling terang. Panahnya juga saya pindahkan ke **luar** ruangan, di area latar.

## 2. Satu segmen dinding melewati tujuh tahap (Lab 1 no 3, A1)

Angka di bawah ini adalah output `node walkthrough.mjs` (dinding belakang, `outer_wall` segmen 1):

```
1 application      "outer_wall" segment 1: (0,4) m -> (2,4) m, category "wall"
2 vertex processing x_px = (x_m + 2) * 130,  y_px = 599 - (y_m + 0.3) * 130
                   (260,40) -> rounded (260,40)
                   (520,40) -> rounded (520,40)
3 assembly/clipping two vertices -> one line primitive; both inside 800x600: true (nothing clipped)
4 rasterisation    Bresenham: dx=260 dy=0, 261 pixels = max(dx,dy)+1, first (260,40) last (520,40)
                   (260,40) (261,40) (262,40) (263,40) ... (517,40) (518,40) (519,40) (520,40)
5 fragment shading flat colour of "wall" = rgb(33,145,140)  (viridis step, no lighting)
6 per-fragment ops no depth test, no blending: the later write wins (lines are drawn after the fill)
7 framebuffer      (390,40) = rgb(33,145,140)  neighbours (390,39) = rgb(18,18,22)  (390,41) = rgb(230,236,245)
```

| Tahap | Yang terjadi pada dinding belakang |
|---|---|
| 1. Application | JSON menyimpan dua titik dalam meter, (0, 4) dan (2, 4), dengan kategori `wall` |
| 2. Vertex processing | `makeWorldToScreen()` mengalikan dengan 130 px/m, menggeser dengan origin, dan membalik y. Hasilnya (260, 40) dan (520, 40). Di sini kebetulan tidak ada pembulatan |
| 3. Primitive assembly & clipping | Dua titik dirangkai menjadi satu garis. Keduanya di dalam canvas, jadi tidak ada yang dipotong |
| 4. Rasterisation | Bresenham menyalakan 261 pixel di baris 40, dari x = 260 sampai 520. Ujungnya ikut dihitung, jadi max(Δx, Δy) + 1 |
| 5. Fragment shading | Setiap pixel mendapat warna rata kategori dinding (33,145,140) |
| 6. Per-fragment operations | Tidak ada depth test atau blending. Yang ditulis belakangan menang, dan garis digambar setelah lantai |
| 7. Framebuffer | Pixel (390, 40) berisi warna dinding. Di atasnya latar gelap, di bawahnya lantai |

Contoh lain yang lebih menarik di tahap 2: alas patung 0,08 m menjadi 10,4 pixel. Titiknya (358,8; 319,5) dan (369,2; 319,5) dibulatkan menjadi (359, 320) dan (369, 320). Jadi lebarnya 10 pixel dan garisnya 11 pixel, dan pembulatan menggeser setiap titik paling banyak setengah pixel. Nilai 319,5 kebetulan tepat di tengah, dan `Math.round` membulatkannya ke atas.

### Kalau satu tahap dilewati (A1)

Misalnya **tahap 2 (vertex processing) dilewati**, sehingga angka meter langsung dipakai sebagai pixel. Ruangan 2 × 4 m hanya akan menjadi kotak 3 × 5 pixel di pojok kiri atas canvas. Karena y tidak dibalik, jalan masuk muncul di atas, bukan di bawah. Semua detail yang lebih kecil dari 1 m (patung, pintu lemari, panah) menyusut menjadi satu atau dua pixel, karena Bresenham memotong koordinat ke integer. Semua tahap setelahnya tetap jalan dengan benar, jadi kerusakannya tidak memunculkan error apa pun, dan gambarnya hanya terlihat "kosong". Itu sebabnya test `worldToScreen` yang mengecek satu titik yang diketahui tetap penting.

## 3. Prediksi forward vs backward (Lab 1 no 4)

Ditulis di `docs/prediksi/prediksi-forward-backward.md` dan di-commit **sebelum** `bench.mjs` dijalankan. Hasil dan rekonsiliasinya ada di catatan Fase 5.

## 4. Bacaan: kode sumber `Line` di Three.js (Lab 1 no 5)

Saya membaca `src/objects/Line.js`, `src/materials/LineBasicMaterial.js`, dan bagian `renderBufferDirect` di `src/renderers/WebGLRenderer.js` dari `three@0.160.0`.

**Yang berbeda dari `raster.mjs`:** Three.js **tidak** melakukan rasterisation garis sama sekali. `Line` hanya menyimpan titik-titik float di buffer. Saat digambar, renderer memilih mode `gl.LINE_STRIP` (atau `gl.LINES` untuk `LineSegments`, `gl.LINE_LOOP` untuk `LineLoop`), lalu menyerahkannya ke GPU. Pixel mana yang menyala diputuskan oleh hardware, bukan oleh JavaScript. Sebaliknya, `raster.mjs` membulatkan ujung garis ke pixel integer, lalu Bresenham memutuskan setiap pixel sendiri, termasuk kedua ujungnya.

Ini punya tiga akibat yang saya lihat langsung di Fase 5:

1. **Posisi sub-pixel.** Titik dikirim dalam float, jadi garis bisa jatuh di antara dua baris pixel (temuan T4). Bresenham tidak bisa mengalami ini, karena ia selalu berjalan di pusat pixel.
2. **Ujung dan sambungan.** GPU menggambar garis dengan aturannya sendiri: ujung garis tidak selalu ikut, dan dengan antialiasing (MSAA) sambungan dua garis hanya tertutup sebagian. Semua ketidakcocokan yang tersisa setelah perbaikan memang ada di ujung dan sambungan (lihat Fase 5).
3. **Ketebalan.** `LineBasicMaterial` punya properti `linewidth` (default 1), tapi di GPU saya `ALIASED_LINE_WIDTH_RANGE` = [1, 1], jadi garis selalu 1 pixel berapa pun nilainya. Three.js menyediakan `Line2` dan `LineMaterial` di `examples/jsm/lines/` untuk garis tebal, yang membangun garis dari segitiga.

**Kenapa dibuat begitu:** Three.js adalah pustaka untuk GPU, dan rasterisation garis adalah tahap fixed-function. Menyerahkannya ke hardware membuat jutaan garis bisa digambar cepat. Harganya, kita harus tahu konvensi pusat pixel GPU-nya sendiri, dan itulah yang dibuktikan oleh T4.

## 5. Refleksi kasus half-pixel (Lab 1 no 6)

Sumber: Microsoft Learn, "Directly Mapping Texels to Pixels (Direct3D 9)" dan "Coordinate Systems (Direct3D 10)" (keduanya bertanggal dokumen 31 Mei 2018), serta Pranckevičius, "Solving DX9 Half-Pixel Offset" (8 April 2016). Detailnya ada di Studi Pendahuluan Q4.

**(a) Offset dan letak pusat pixel.** Di Direct3D 9, pusat pixel ada di koordinat integer, sehingga blit 2D perlu menggeser vertex −0,5 di x dan y. Di Direct3D 10, titik asal ada di sudut pixel dan pusat pixel ada di (x + 0,5; y + 0,5), sehingga offset itu tidak perlu lagi.

**(b) Baris yang mengodekan konvensi pusat di `raster.mjs`:**

- di `triangleNaive()`: `const px = x + 0.5, py = y + 0.5;`
- di `triangle()`: `const half = SUB / 2;` lalu `edge(..., minX * SUB + half, minY * SUB + half)`, yaitu (x + 0,5) × SUB dalam satuan fixed-point;
- di `fillRect()`: `centre: (x, lo, hi) => x + 0.5 >= lo && x + 0.5 < hi`.

**(c) Citra uji yang membuat bug-nya jelas:** checkerboard 1 pixel hitam-putih yang di-blit 1:1. Kalau offset-nya salah, setiap sampel jatuh di sudut empat texel, yaitu 2 hitam dan 2 putih, jadi seluruh gambar menjadi abu-abu rata (0 + 255 + 0 + 255) / 4 = 127,5. Polanya hilang total. Garis horizontal 1 pixel juga cukup. Itulah yang saya temukan di viewer starter (T4): garis dinding jatuh di batas baris 39 dan 40, sehingga **dua** baris masing-masing mendapat 50%, yaitu (26,82,81) di atas latar dan (131,191,192) di atas lantai, padahal seharusnya satu baris berwarna (33,145,140).

**(d) Satu perubahan pada Studi Kasus yang akan menangkapnya.** Studi Kasus hanya meminta "PSNR tinggi tapi tidak tak hingga" dan menganggap semua ketidakcocokan adalah antialiasing. Itu terlalu longgar: dengan bug T4, PSNR denah saya masih 31,1 dB, yang terlihat wajar. Perubahan yang saya buat adalah `diff_pixels.mjs`. Program ini mengelompokkan setiap pixel yang tidak cocok sebagai ujung/sambungan garis, garis diagonal, atau "lainnya", dengan syarat kelompok "lainnya" harus **0**. Dengan bug T4 ada **5.015** pixel "lainnya", semuanya di sepanjang garis lurus. Setelah offset +0,5, jumlahnya **0**.
