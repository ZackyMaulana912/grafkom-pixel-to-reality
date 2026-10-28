# Laporan Modul 3: Transformasi 3D, Proyeksi, Texture & Real-Time Rendering

Zacky Maulana (NIM 20241337034)
Praktikum Grafika Komputer, S1 Informatika UMSurabaya

Semua angka di laporan ini adalah keluaran program yang saya jalankan di Mac saya (Apple M5, macOS 27.0.1, Python 3.11.8, NumPy 2.4.6, Pillow 13.0.0), kecuali yang ditandai lain. Perintah untuk mengulang setiap angka ada di `Module3/Source/README.md`, dan penjelasan rinci per fase ada di `Module3/docs/catatan/`.

---

## 1. Model dan telusuran satu vertex (A1)

**Model.** Subjek saya patung kuda milik saya sendiri. Di Modul 2 saya menelusuri denah ruangan tempat patung itu berdiri, dan di Modul 3 ruangan itu menjadi model 3D low-poly:

- 394 segitiga: lantai, tiga dinding, lemari 8 pintu, sekat berlubang, alas patung, dan badan patung;
- badan patung adalah garis luar 55 titik yang saya telusuri di foto IMG_8882, lalu diberi ketebalan;
- texture-nya atlas 512 × 512 dari foto saya sendiri di Modul 1, dengan UV sungguhan. Sisi patung memakai foto patung itu sendiri, dipetakan tepat ke garis luarnya.

Ukuran ruangan dan tingginya adalah ukuran saya. Tinggi patung (45 cm), tebal alas dan badan patung, letak patung, dan susunan rak sekat adalah perkiraan, dan ditandai begitu di `docs/model/README.md`. Model ditulis oleh skrip saya sendiri (`make_mymodel.py`) dari satu file ukuran, lalu diperiksa dengan Blender 5.2.2: terbaca 394 face dengan 1 layer UV.

**Telusuran vertex 134 (ujung telinga patung).** Matriks model `M = T(1, 0, −2)` menaruh titik asal world di pojok jalan masuk, sama dengan denah Modul 2. Kamera ada di (0,15; 1,15; −0,8), menghadap (0,85; 0,3; −2,1), fovy 55°, near 0,1 m, far 10 m.

| Space | Hitungan tangan | `worked_example.py` |
|---|---|---|
| Object | (−0,170000; 0,450000; −0,019259) | sama |
| World `M p` | (0,830000; 0,450000; −2,019259) | (0,83; 0,45; −2,019259) |
| View `V M p` | (0,020672; 0,089798; −1,559006) | (0,020670; 0,089798; −1,559007) |
| Clip | | (0,039706; 0,172500; 1,388481; 1,559007) |
| NDC | | (0,025469; 0,110647; 0,890619) |
| Screen | | (262,52; 227,67), pixel (262, 227), depth 0,9453 |

Hitungan tangan `M p` dan `V (M p)` cocok sampai 5 desimal. `w = 1,559007 = −z_eye`, seperti yang diharapkan. Di render, titik itu memang jatuh di ujung telinga patung.

**Telusuran kolom.** Kolom 1–3 `M` adalah sumbu identitas (tanpa rotasi atau skala), dan kolom 4 `(1, 0, −2)` adalah ke mana titik asal model (tengah lantai) pindah. Baris 1–3 `V` adalah sumbu kanan, atas, dan belakang kamera di world. Baris 3 `(−0,41; 0,50; 0,76)` berarti kamera menghadap ke kanan, menunduk sekitar 30°, dan masuk ke ruangan. Kolom 4 `V` `(0,25; −1,38; 0,10)` adalah pojok jalan masuk dilihat dari kamera: 1,38 m di bawah mata dan sedikit di belakang kamera, sesuai dengan posisinya. `V⁻¹` kolom 4 tepat sama dengan posisi kamera.

## 2. Pipeline from-scratch dan kecocokan dengan referensi (A2)

`transforms.py`, `objio.py`, `raster3d.py`, dan `raytrace.py` saya tulis ulang, ditambah `mipmap.py` dan file scene. Konvensinya dipatok sekali di atas `transforms.py`.

**Contoh E1–E5 di `tests.py`** (17 check, semuanya OK):

- E1: (2, 3, 4) → (3, 3, −3) → (2, 2), dan urutan sebaliknya memberi (5, 3, −3);
- E2: kamera +1 di x sama dengan model −1 di x, keduanya (4, 0, 0);
- E3: z = −n → −1, z = −f → +1, z = −3 → 0,5;
- E4 lewat fungsi rasteriser `perspective_correct`: **u = 0,1**, sedangkan naif 0,5;
- E5 lewat `bary_mix`: 0,625.

Di starter, E4 dan E5 hanya menguji `np.interp` dan penjumlahan, tanpa memanggil rasteriser sama sekali.

**Kecocokan:**

| Perbandingan | Hasil |
|---|---|
| Raster saya vs `ref/temple_ref.ppm` (dibuat kode dosen yang belum diubah, di-commit terpisah) | **identik byte per byte** |
| Raster vs ray tracer, model saya, 512 × 512 | **identik byte per byte** (PSNR inf) |
| Raster vs ray tracer, candi, 256 × 256 / 512 × 512 | 78,6 dB (2 pixel) / 69,1 dB (3 pixel), SSIM 1,000 |

**Residu raster vs ray tracer di candi (temuan T14).** Semua pixel yang berbeda punya u = 1 persis. Sampler starter memakai `np.mod(u, 1)`, sehingga 1,0 menjadi 0,0 (kolom texture paling kiri), sedangkan 0,9999999999999999 tetap di kolom paling kanan. Apakah sebuah pixel jatuh di 1,0 atau di 0,999… ditentukan oleh pembulatan di digit terakhir. Itulah kenapa kode dosen yang sama memberi 68,1 dB di Mac saya, 76,5 dB di Linux, dan 76,9 dB di PDF. Model saya tidak terkena, karena UV-nya tidak pernah menyentuh 0 atau 1.

## 3. Diagnosis dan perbaikan, tiga bug (A3)

Diagnosis ditulis dari bukti saja (`diagnose_scene.py`: render, citra depth, matriks, histogram depth) dan di-commit lebih dulu: `docs/prediksi/diagnosis-scene-rusak.md`.

| Bug | Diagnosis sebelum perbaikan (bukti) | Satu perubahan | SSIM sebelum → sesudah | Pitfall |
|---|---|---|---|---|
| inside-out | signed volume mesh −2,976, jadi semua face menghadap ke dalam. Dengan culling, depth lebih jauh dari kebenaran di 19.029/19.029 pixel. Scene yang disebut "rusak" oleh starter justru identik dengan kebenaran | loader membalik mesh bersigned volume negatif | 0,790 → **1,000** (PSNR inf) | §12.6 |
| zfight | near 0,001, far 200, 16-bit: kedua quad jatuh di **satu** kode depth (65532), quad biru tampak di 0 pixel | near → 1 | 0,763 → 0,984; pixel salah 2.852 → **184**, semuanya di baris 94–95 (garis potong) | §12.2 |
| stretched | panjang kolom M 3,08 / 0,70 / 1,40 (seharusnya 1,4 semua): ada skala tidak seragam di ruang model | buang diag(2,2; 0,5; 1) | 0,594 → **1,000** (PSNR inf) | §12.1 |

Histogram depth zfight: sebelum perbaikan 1 kode untuk semua 5.704 pixel, sesudahnya 13 kode (`docs/img/bug_zfight_hist_*.png`). Semua prediksi di dokumen diagnosis terbukti, termasuk letak sisa pixel salah di garis potong.

**Dua catatan tentang starter.**

- **Label inside-out terbalik (T13).** `make_model.py` mengklaim face-nya CCW dari luar, padahal semuanya searah jarum jam. Kesalahan ini tidak pernah terlihat, karena referensi, ray tracer, dan viewer tidak memakai culling.
- **Label stretched kurang tepat (T9).** Bug ini disebut "urutan matriks tertukar", padahal menukar skala seragam dengan rotasi tidak mengubah apa pun. Penyebabnya faktor skala tambahan.

**Perbaikan pitfall (Lab 2 no 5).** Scene zfight saya jalankan ulang dengan near tetap 0,001:

| Depth buffer | Pixel salah |
|---|---|
| 16-bit fixed (bug aslinya) | 2.852 |
| 24-bit fixed | 828 |
| float32, NDC biasa | 92 |
| float32, reverse-Z | **0** |
| 16-bit fixed, reverse-Z | 2.852 |

Reverse-Z hanya menolong bila dipasangkan dengan float, sesuai penjelasan Reed (2015).

## 4. Texture dan sampling (A5)

**Perspective-correct vs naif.** Contoh E4 dalam render sungguhan: u di tengah tepi = 0,1008 (perspective-correct) vs 0,5022 (naif). Pada lantai bergaris dilihat menyamping, u naif rata-rata meleset 2,70 m dari posisi lantai yang benar. Saat kamera maju 10 cm, texture naif **meluncur rata-rata 27,2 cm (maksimum 56,8 cm)** di atas lantai, sedangkan yang perspective-correct 0,00 cm. Gambar: `docs/img/floor_{naive,pc}.png`.

**Mipmap.** Piramida 4 level, rata-rata 2 × 2 di linear light, level of detail dari turunan UV, dan trilinear. Candi ditarik mundur 5 kali, lalu dibandingkan dengan supersampling 8 × 8:

| | Kelap-kelip (geser 1%) | Energi frekuensi tinggi | PSNR terhadap kebenaran |
|---|---|---|---|
| tanpa mipmap | 49,26 | 177,5 | 15,7 dB |
| dengan mipmap | **1,12** | 54,4 | **28,3 dB** |
| kebenaran | | 34,6 | |

## 5. Keputusan rasterisation vs ray tracing (A4)

**Prediksi** (ditulis dan di-commit sebelum ada `bench.py`): raster 0,4 s (0,2–1,0), ray tracer 5 s (3–12), rasio sekitar 12× (5–30×). Ray tracer memberi shadow lebih tepat.

**Pengukuran** (median 5 run, 512 × 512, model saya): raster **0,162 s**, ray tracer **1,499 s**, rasio **9,3×**. Dengan hard shadow: 0,254 s (shadow map) vs 3,756 s (shadow ray).

**Rekonsiliasi.**

- Yang terbukti: rasio masuk rentang. Rasio model saya (9,3×) lebih besar dari candi (6,2×). Frame 4× pixel membuat ray tracer naik 3,97× tapi raster hanya 2,5×. Shadow map menambah 1,57×.
- Yang meleset: waktu absolutnya saya perkirakan 2,5 sampai 3,3 kali terlalu lambat. Ray tracer di M5 mengerjakan sekitar 69 juta uji ray-segitiga per detik, jauh di atas tebakan saya. Shadow ray menambah 2,5×, bukan 2×, karena tidak berhenti di hit pertama. Bayangan patung yang saya kira paling terlihat ternyata tidak muncul, karena patungnya sudah berada di dalam bayangan dinding setinggi 3,5 m.
- Kualitas shadow: raster vs ray tracer 40,9 dB, dan selisihnya hanya garis 1 pixel di tepi bayangan (resolusi shadow map 4–6 mm per texel, ditambah bias).

**Pilihan.**

- **Viewer real-time: rasterisation di GPU (WebGL).** Satu draw call per frame, dan semua tahap berat dikerjakan hardware.
- **Beauty shot marketing: ray tracing.** Bayangan tepat per pixel, dan pantulan cukup dengan satu ray tambahan.

**Kondisi di mana pilihannya berbalik:**

1. **Jumlah segitiga sangat besar dengan BVH:** ray tracer ber-BVH tumbuh kira-kira logaritmik terhadap jumlah segitiga, sedangkan rasteriser tumbuh linear. Untuk scene puluhan juta segitiga yang hampir semuanya tertutup, ray tracing bisa lebih murah per frame.
2. **Butuh pantulan, refraksi, atau global illumination yang benar:** rasterisation hanya bisa mendekatinya (environment map, screen-space reflection). Ray tracing menjadi pilihan, bahkan untuk real-time.
3. **GPU dengan RT core** (RTX, DXR, Apple M3 ke atas): ray tracing hybrid untuk bayangan dan pantulan sudah real-time. Pilihannya menjadi raster + ray tracing, bukan salah satu.
4. **Target frame rate rendah atau gambar diam:** untuk render satu gambar per beberapa detik, kecepatan rasteriser tidak lagi penting, dan ray tracing menang karena kualitasnya.

## 6. Real-time di browser (Lab 3 no 1, 2, 4)

Viewer `web/` membaca file scene yang sama dengan kedua renderer NumPy. Viewer starter apa adanya hanya mendapat **11,4 dB** terhadap raster, karena tiga penyebab yang saya buktikan dari kode sumber Three.js 0.160.0:

| Perbaikan | Model saya PSNR |
|---|---|
| viewer seperti starter | 11,4 dB |
| (a) lampu × π (`BRDF_Lambert` = albedo/π, lampu fisik sejak r155) | 38,3 dB |
| (b) `LinearFilter` (default `DataTexture` nearest) | 39,5 dB |
| (c) pusat texel disamakan lewat `repeat`/`offset` | **40,4 dB**, SSIM 0,998 |

Candi: 14,8 → 35,3 dB. Setiap region yang tidak cocok sudah dijelaskan:

- 92% error kuadrat ada di **tepi segitiga** (MSAA);
- bagian dalam berbeda rata-rata +0,49 kode, karena rasteriser memotong ke uint8 sedangkan GPU membulatkan. Terbukti: dengan pembulatan, biasnya −0,002;
- 33 pixel dalam candi yang berbeda jauh semuanya ada di jahitan u = 1 (T14).

Tidak ada pergeseran region di bagian dalam.

## 7. Keterbatasan

1. **Ukuran model sebagian perkiraan.** Tinggi patung, tebal alas dan badan, letak dan arah patung, serta susunan rak sekat tidak diukur dengan meteran. Bentuk patung adalah siluet yang diberi ketebalan, bukan bentuk 3D sebenarnya.
2. **Referensi candi adalah referensi regresi.** `ref/temple_ref.ppm` hanya membuktikan bahwa kode saya sama dengan kode dosen. Pembanding independennya adalah ray tracer dan WebGL.
3. **Konvensi starter saya pertahankan meski kurang ideal:** sampler dengan `mod` (T14) dan pemotongan ke uint8 (T15). Alasannya, referensi bergantung pada keduanya. Akibatnya terukur dan dijelaskan, bukan disembunyikan.
4. **Perbaikan winding memakai satu tanda global** (signed volume). Ini hanya benar untuk mesh tertutup dengan winding yang konsisten di dalam mesh itu.
5. **Semua pengujian di satu Mac.** Viewer diuji dengan Chrome headless di GPU Apple M5. Browser lain, GPU lain, Windows, dan Linux belum diuji, dan PSNR raster vs WebGL bisa sedikit berbeda di GPU lain (pola MSAA berbeda).
6. **Frame time hanya dari NumPy di satu mesin.** Rasio dan skalanya bisa dipindah ke mesin lain, tapi angka detiknya tidak.

## 8. Penyimpangan dari PDF dan alasannya

| PDF | Di repo saya | Alasan |
|---|---|---|
| `code/Module3/` | `Module3/Source/` | struktur repo sejak Modul 1 (K1) |
| `npx serve web` | `python -m http.server 8000 --bind 127.0.0.1` dari `Source/` | `web/` saja tidak bisa memuat `../data` (T8), `serve` terbuka ke jaringan, dan Python sudah tersedia tanpa unduhan (K10) |
| `tests.py` membuat `ref/temple_ref.ppm` sendiri saat run pertama | referensi dibuat sekali dari kode dosen yang belum diubah, di-commit terpisah | tanpa itu test-nya melingkar (T2, K12) |
| kamera dan model ditulis mati di tiga file | satu file scene per model | perbandingan hanya bermakna kalau parameternya identik (K13) |
| `broken_scene.py` mencetak penyebab dan perbaikan | `diagnose_scene.py` hanya bukti, `broken_scene.py` ditulis ulang | supaya diagnosis berasal dari bukti (T10, K14) |
| label inside-out | dibalik | data candinya ber-winding ke dalam (T13) |
| catatan ✓ di Contoh E1 menulis (4, 3, −4) untuk urutan sebaliknya | (5, 3, −3) | PDF menerapkan R_y pada (3, 3, 3), bukan pada (2, 3, 4) |
| `tests.py` "7 ok" (PDF) / "9 ok" (README starter) | 8 check di starter, 17 setelah saya tambah | dihitung dari keluaran |

## 9. Reproducibility (A6)

**Salinan bersih.** Saya menyalin hanya file Modul 3 yang akan masuk git (tanpa `.venv` dan `out/`) ke folder baru, lalu:

```
$ python3 -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt
numpy==2.4.6
pillow==13.0.0
$ python --version
Python 3.11.8
$ python make_model.py
wrote data/pusaka_model.obj  (120 verts, 180 triangles)
wrote data/relief.ppm  (256x256, 196623 bytes)
$ python tests.py
OK   E1  running point (2,3,4) -> (3,3,-3); divide d=2 -> (2,2); other order (5,3,-3)
...  (17 baris OK)
ALL CHECKS PASSED (17 ok, 0 fail)
$ python -m http.server 8000 --bind 127.0.0.1
127.0.0.1:8000 (LISTEN)
GET /web/ -> 200    GET /web/viewer.js -> 200    GET /scenes/mymodel.json -> 200
GET /data/mymodel.obj -> 200    GET /data/mymodel_tex.ppm -> 200
```

`make_model.py` menghasilkan file yang sama byte per byte dengan yang di-commit (sha256 identik). Viewer dari salinan itu termuat tanpa error di Chrome 156 headless, bisa di-orbit, dan Export PPM-nya identik byte per byte dengan export sebelumnya. Setelah itu server dimatikan dan folder ujinya dihapus.

**Clone dari GitHub** (commit `b10843f`, folder baru, `.venv` baru): `pip install` memasang `numpy==2.4.6` dan `pillow==13.0.0`, dan `make_model.py` menghasilkan file yang sama persis dengan yang di-commit (`git status` tetap bersih). `tests.py`: `ALL CHECKS PASSED (17 ok, 0 fail)`.

**GitHub Pages:** https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module3/Source/web/

- semua file yang dibutuhkan viewer berstatus 200 dengan tipe MIME yang benar;
- `viewer.js` dan texture yang disajikan identik dengan isi repo;
- di Chrome 156 headless: 0 error console, halaman, maupun jaringan, dan model bisa di-orbit;
- Export PPM dari halaman Pages identik byte per byte dengan export dari server lokal, baik untuk model saya maupun candi.
