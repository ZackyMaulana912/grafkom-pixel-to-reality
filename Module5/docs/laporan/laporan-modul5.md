# Laporan Modul 5: AI Graphics, NeRF, World Models & Augmented Reality

Zacky Maulana (NIM 20241337034), S1 Informatika UMSurabaya
Praktikum Grafika Komputer

Subjek saya sama dengan Modul 1 sampai 4, yaitu patung kuda milik saya. Semua angka di laporan ini adalah keluaran program yang benar-benar saya jalankan. Perintah, transkrip, dan penjelasan lengkapnya ada di `docs/catatan/`, sedangkan prediksi yang di-commit sebelum hasilnya ada di `docs/prediksi/`.

**Toolchain (Lab 1 no 1).**
- Mac17,2 (Apple M5), macOS 27.0.1 (26A434).
- Python 3.11.8 di `Module5/Source/.venv`: NumPy 2.4.6, pygltflib 1.16.5, matplotlib 3.11.2 (hanya untuk gambar), Playwright 1.64.1 dengan Chrome Headless Shell 156.
- Blender 5.2.2 LTS dan Apple RealityKit (Object Capture), untuk aset AR saja.
- Browser dan perangkat uji AR: Safari di iPhone 17 Pro, iOS 27.2.
- Dicatat 2 sampai 4 November 2026.

Di repo ini, folder `code/Module5/` dari modul adalah `Module5/Source/`. Bahan awal dosen ter-commit utuh di `a522d3c`, jadi semua pekerjaan saya terlihat dengan `git diff a522d3c`.

---

## 1. Capture saya dan ray dengan tangan (A1)

**Capture.** 28 foto patung kuda yang saya ambil sendiri dengan iPhone 17 Pro (lensa 6,765 mm, setara 24 mm, 4536 × 8064 px) pada 27 Oktober 2026, sambil berjalan mengelilingi patung sekitar satu putaran. Ada celah sudut antara foto terakhir dan foto pertama. Foto aslinya tidak di-commit. Yang masuk repo adalah daftar, checksum, dan contact sheet tanpa EXIF (`Source/data/my_capture/`). Jarak dan tinggi HP tidak tercatat saat memotret.

**Ray dengan tangan** untuk pixel pilihan saya `(1200, 6100)`, yang jatuh di lantai tepat di kiri alas patung pada `IMG_8878`.

Focal length dalam pixel adalah perkiraan dari EXIF, dengan tiga asumsi yang saya tulis di `fase2-capture-ray.md`:
- setara 35 mm dicocokkan pada diagonal: `f = 24 × 10080 / 43,2666 = 5591,38 px`;
- foto adalah potongan frame sensor 6048 × 8064 dengan skala pixel yang sama;
- principal point di tengah, `(2268, 4032)`.

```
x = (1200 - 2268) / 5591,38 = -0,19101
y = -(6100 - 4032) / 5591,38 = -0,36986
z = -1
panjang = √1,17328 = 1,08318   →   arah = (-0,17634; -0,34145; -0,92321), 22,6° dari sumbu optik
```

| | Tangan | `my_ray.py` |
|---|---|---|
| tak ternormalisasi | (-0,19101; -0,36986; -1) | (-0.19101, -0.36986, -1.00000) |
| ternormalisasi | (-0,17634; -0,34145; -0,92321) | (-0.17634, -0.34145, -0.92321) |

Hasilnya cocok sampai 5 desimal (syaratnya 3). `test_my_ray` menguji angka ini, dan terbukti gagal kalau focal length dihitung dari lebar 36 mm, kalau tanda minus y dibuang, atau kalau principal point digeser setengah pixel.

**Bacaan (Lab 1 no 3).** Halaman "Camera Models" nerfstudio (dicocokkan dengan sumber rilis v1.1.5). Bedanya dengan `ray_generator.py`:
- distorsi lensa (`k1` sampai `k4`, `p1`, `p2`) dikoreksi sebelum ray dibuat;
- ada kamera fisheye dan equirectangular;
- ray lewat pusat pixel secara default;
- `fx` dan `fy` disimpan terpisah.

Lensa HP yang kecil dan bersudut lebar membuat garis lurus melengkung di tepi foto. Tanpa model distorsi, titik yang sama akan terlihat di tempat berbeda dari foto ke foto.

**Refleksi insiden (Lab 1 no 5).** Ringkasan, tanggal, dan sumbernya ada di Studi Pendahuluan Q4.
- **ArtStation:** sejak 3 September 2026, perlindungan NoAI menyala secara default. Izin seniman sekarang menjadi keadaan awal, bukan pengecualian.
- **Nefertiti:** scan resmi museum dibuka dengan lisensi yang terukir di model 3D-nya.

Baris provenance saya ada di bagian 4. Pengecekan otomatis yang saya usulkan sudah jadi test: `tests.py` gagal kalau ada aset AR tanpa baris provenance yang lengkap.

## 2. Renderer from-scratch, verifikasi gradien, dan bentuk saya (A2)

**E1 dan E2**, dari `tests.py`:
- ray `(0,8; 0; -1)`, ternormalisasi `(0,625; 0; -0,781)`;
- bobot `(0,5; 0,25; 0,25)`, sisa latar 0, jumlah 1, warna `(0,5; 0,25; 0,25)`.

Variasi saya di Studi Pendahuluan:
- ray `f = 120`, pixel `(200, 330)` menghasilkan `(-1; -0,75; -1)`;
- `α = (0,2; 0,6; 0,5)` menghasilkan bobot `0,2 / 0,48 / 0,16`, sisa latar 0,16, dan warna di atas latar putih `(0,36; 0,64; 0,32)`.

Satu catatan notasi: sisa latar yang ditulis `T_N` di modul sebenarnya `T(N+1)` (T13).

**Satu konvensi pixel (K12).** Starter punya dua konvensi tanpa penjelasan (T4) dan salinan pembuat ray di `nerf_toy.py`. Sekarang hanya ada satu rumus, yang ditulis sekali di atas `ray_generator.py`:
- `(u, v)` kontinu untuk satu titik;
- `kolom + 0,5` untuk gambar penuh.

Hasilnya dibuktikan identik dengan starter pada 300 kasus acak.

**Gradien diturunkan sendiri.** Bentuk yang saya dapat:

```
dC/dα_k = T_k (c_k - B_k),   B_k = warna yang terlihat dari tepat di belakang sampel k
```

Bentuk ini sama dengan rumus modul, tetapi tidak pernah membagi dengan `1 - α`. Sampel yang padat penuh tidak butuh cabang khusus, jadi pitfall 12.4 (pembagian dengan nol) tidak bisa terjadi.
- **Cek finite difference starter:** selisih terburuk dengan kode saya `4.89e-11`. Modul menulis sekitar `3e-11`; saya memakai angka dari run saya sendiri.
- **Rusak dengan sengaja:** kalau suku "yang di belakang" dibuang, cek itu gagal dengan `1.91e-01`. Membuang turunan sigmoid warna memberi `3.25e-01`, dan membuang turunan softplus memberi `3.84e-02`. Semua jauh di atas ambang `1e-6`. Jadi cek ini memang punya gigi.
- **Temuan: rumus starter salah di kondisi ekstrem.** Saat sampel hampir kosong, salahnya 23%. Saat hampir padat, salahnya 300% dengan tanda terbalik: finite difference `+4.40e-08`, starter `-8.79e-08`. Ini membuktikan celah T3 di panduan. Cek starter tidak menangkapnya karena hanya menguji σ_raw di sekitar 0. Test baru saya mengecek setiap voxel yang disentuh sampel di empat kondisi (normal, hampir kosong, hampir padat, padat penuh), dan rumus starter gagal di sana.

**Bentuk saya: patung kuda mini** dari empat kotak di teras depan candi, di dalam kubus `[-1, 1]³` dan tidak menembus candi (dicek dengan 200.000 titik acak). Kuda terlihat di 7 dari 8 view latih, tertutup candi di 225°.

**Data latih dari file PPM (K17).** Sebelumnya, file PPM ditulis tetapi tidak pernah dibaca (T5).

| Scene dan target | PSNR latih | PSNR baru 22,5° |
|---|---|---|
| candi saja, render pas (starter) | 20.69 | 14.44 |
| candi + kuda, render pas | 20.31 | 14.84 |
| candi + kuda, PPM 8 bit (dipakai) | 20.32 | 14.85 |

Pembulatan 8 bit hanya menggeser 0,01 dB. Perubahan sisanya berasal dari kuda.

`tests.py` tumbuh dari 17 menjadi **81 check**, dan setiap test baru terbukti bisa gagal. Yang ditambahkan antara lain:
- konvensi pixel;
- gradien di setiap voxel dan di kondisi ekstrem;
- komposit per ray;
- `poses.json` dengan toleransi;
- `load_ppm`;
- larangan import selain NumPy;
- aset AR dan provenance;
- dasar uji occlusion;
- arah segitiga candi.

## 3. Diagnosa dan perbaikan, dengan bukti (A3)

**Sebelum melihat hasil.** `nerf_bug.py --diagnose` hanya melatih model 2 view (0° dan 20°): kurva MSE turun mulus dari `0.14035` ke `0.00836`, dan PSNR latih 21,13 dB, lebih tinggi dari model 8 view. Dari angka latih saja, saya tidak akan curiga. Kecurigaan baru muncul dari cara capture-nya:
- ada 6912 parameter, sedangkan dua gambar hanya memberi 1920 angka;
- ray kedua view menembus hampir semua voxel, tetapi dari arah yang hanya berbeda 20°, sehingga kedalaman warna tidak bisa dipastikan.

Prediksi saya di-commit di `319add1` sebelum sudut baru diukur. Di file itu juga saya tulis apa yang sudah saya ketahui sebelumnya: tabel T7 panduan, dan satu angka 190° yang sudah terlanjur tercetak.

**Hasil** (`nerf_bug.py --sweep`):

| Sudut baru | 2 view | 8 view | Selisih |
|---|---|---|---|
| 10 | 10.23 | 12.11 | +1.88 |
| 22,5 | 15.97 | 14.26 | -1.71 |
| 60 | 10.56 | 15.56 | +5.00 |
| 100 | 9.10 | 11.88 | +2.78 |
| 160 | 9.36 | 13.31 | +3.95 |
| 190 | 9.39 | 12.05 | +2.66 |
| 250 | 9.34 | 13.10 | +3.76 |
| 340 | 10.02 | 12.94 | +2.92 |
| 270 (view latih 8 view, bukan bukti) | 9.32 | 21.02 | +11.70 |

**Rekonsiliasi: 5 dari 7 prediksi tepat.**
- **Tepat:** model 8 view menang di sudut jauh; model 2 view menang di 22,5° (2,5° dari view latihnya); kalah di 10° walaupun 10° ada di antara kedua view latihnya; kalah di 340°; dan model 8 view lebih rata di sudut yang diuji.
- **Meleset:** PSNR model 8 view di 270° lebih tinggi dari tebakan saya (21,02 dB). Patung kuda mini juga ternyata sama buruknya di kedua model, karena hanya selebar 1 sampai 2 voxel grid 12³. Tambahan view tidak menolong detail yang tidak bisa disimpan grid itu.

Grafik 144 sudut juga menunjukkan hal yang tidak saya prediksi: model 8 view pun turun ke sekitar 11,6 dB di sela dua view latihnya. Dengan 8 view, model hanya punya lebih banyak titik pegangan, bukan pemahaman bentuk.

Kaitannya dengan pitfall:
- **12.2:** PSNR latih tidak bisa membedakan model yang paham bentuk 3D dari model yang menghafal dua gambar.
- **12.3:** yang menentukan adalah sebaran sudut, bukan jumlah foto.

Hasil di 22,5° membuktikan bahwa satu sudut uji bisa membalik kesimpulan.

**Perbaikan (Lab 2 no 4), dua-duanya** (`pitfall_fix.py`):
- **(a) Nilai awal density, pitfall 12.1.** Di lr 5, `sigma_raw = -5` benar-benar macet: MSE hanya turun `0.0003` dalam 300 iterasi, sedangkan dengan nilai awal 0 turun `0.0587`. Penyebabnya, `sigmoid(-5) = 0,0067` mengecilkan gradien sekitar 150 kali. Di lr 100 tidak macet, hanya terlambat. Jadi klaim modul hanya terbukti di learning rate kecil (T8). "Mulai dari 0 selalu terbaik" juga tidak benar: di lr 5, nilai awal -2 dan +2 berakhir lebih rendah.
- **(b) Satu view ketiga.** Saya coba enam posisi, karena modul tidak menjelaskan arti "intermediate". Di seluruh lingkaran, view di 5° (tepat di sebelah foto lama) hanya menambah +0,27 dB, sedangkan view di 135° menambah +1,16 dB, sekitar seperempat dari selisih dengan model 8 view. Kalau diukur di 8 sudut uji, pemenangnya malah 5°, karena dua sudut uji kebetulan bersebelahan dengan view itu. Ini pitfall 12.3 dalam angka.

## 4. AR app, keputusan occlusion, dan integrasi (A4)

**Model saya (Lab 3 no 1, pilihan a).** Scan photogrammetry patung kuda dari ke-28 foto, memakai Apple Object Capture (`tools/photogrammetry.swift`):
- detail full, 224 detik, 105.665 segitiga;
- satu potongan utuh, dengan 80 dari 83 tepi terbuka berada di bawah alas.

`tools/scan_to_glb.py` (Blender) lalu:
- meluruskan model 1,59°, karena dinding alas harus tegak;
- menaruh lantai di bawah alas, bukan di titik nyasar 1 cm lebih rendah;
- menskalakan model ke ukuran yang saya ukur sendiri (bawah);
- memperkecil tekstur ke 4096 px. Hasilnya `kuda.glb` 4,41 MB.

| | Saya ukur | Model |
|---|---|---|
| panjang alas | 46 cm | 46,0 (patokan) |
| tinggi | 63 cm | 62,8 (-0,4%) |
| lebar alas | 15 cm | 14,7 (-1,9%) |
| tebal alas | 6 cm | 6,4 |

```
Aset: kuda.glb | sumber: scan photogrammetry dari 28 foto saya sendiri dengan Apple Object Capture | pembuat: Zacky Maulana; pembuat patung aslinya tidak diketahui | lisensi: CC BY-NC 4.0 | dibuat: 3 November 2026 | dibuat dengan AI: tidak
```

**Model kedua.** "Aston Martin F1 AMR23 2023" karya Redgrund (Sketchfab, CC BY 4.0). Skalanya diambil dari FIA 2023 Formula 1 Technical Regulations, Issue 7:
- **patokan:** ban 725 mm (pasal 10.8.1c);
- **pengecek:** lebar 2,006 m (batas 2000 mm, pasal 3.4.1) dan wheelbase 3,387 m (batas 3600 mm, pasal 3.4.2);
- dirampingkan ke 161.184 segitiga, 7,67 MB;
- di AR boleh dicubit (`ar-scale="auto"`), sedangkan kuda dikunci 100%.

Logo di livery adalah merek dagang dan tidak tercakup lisensi CC. Hal ini dicatat di LICENSE.md, footer, dan hotspot. Candi dosen dikeluarkan dari app atas keputusan saya, tetapi filenya tetap di repo.

**Hotspot.** Masing-masing model punya lima hotspot dua bahasa, bertema cara model dibuat dan diskalakan. Semua angkanya dari data saya sendiri atau dari dokumen yang saya baca. Posisinya dihitung dengan ray dari mesh yang sama dengan geometrinya, jadi tidak mungkin melayang (paling jauh 1,7 mm dari permukaan kuda).

**Keputusan occlusion (Lab 3 no 2).** Prediksi di-commit di `24bd4c0`: surai adalah hotspot yang paling sulit. Pengujiannya membandingkan `<model-viewer>` dengan kebenaran ray di 76 sudut kamera.
- Dari kode `<model-viewer>` 3.5.0 sendiri: hotspot disembunyikan hanya kalau `dot(arah kamera, normal) < 0`. Tidak ada pengecekan bagian model yang menghalangi.
- Hotspot yang disembunyikan hanya diredupkan ke 25% dan masih bisa diketuk. Aturan CSS starter untuk itu tidak pernah aktif.
- Dari 380 keputusan, 11 salah, semuanya "tampil padahal tertutup". Prediksi surai sebagian tepat (salah tampil di 70°). Kaki ternyata paling sering salah (255 sampai 270°, dari sisi ekor), padahal saya prediksi hampir selalu benar. Normal kaki condong ke arah ekor.
- **Perbaikannya:**
  - hotspot tersembunyi tidak bisa diketuk lagi;
  - normal dipilih dari 288 kamera latih yang terpisah dari kamera uji;
  - titik kaki dipindah 1,8 cm ke titik yang visibilitasnya bisa diwakili satu normal.
- **Hasil:** 11 menjadi 1 (hampir menyamping), dan 0 yang tampil padahal tertutup. Untuk mobil, 2 kasus hampir menyamping, 0 tertutup.

Dalam proses ini saya juga menemukan dan memperbaiki tiga kesalahan alat uji saya sendiri: titik awal ray, waktu membaca status hotspot, dan kamera yang digoyang *interaction prompt*.

**Dua bug starter, dibuktikan dulu lalu diperbaiki:**
- **T10:** puncak candi tembus pandang. 6 dari 6 segitiga stupa menghadap ke dalam. Ada screenshot sebelum dan sesudah.
- **T11:** tombol bahasa tidak mengganti panel yang sedang terbuka. Check baru yang tidak mengklik ulang hotspot gagal di `app.js` starter dan lolos setelah diperbaiki.

`verify_ar_app.py`: **17 ok**, di lokal, di clone bersih, maupun langsung ke GitHub Pages.

**Hosting dan perangkat (Lab 3 no 3).** GitHub Pages dari branch `main`: https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module5/Source/ar_app/index.html. File yang dilayani identik dengan repo. Uji di iPhone 17 Pro (iOS 27.2, Safari, Quick Look): kuda menempel di permukaan, bertekstur, dan ukurannya terlihat sama dengan patung asli yang berdiri di sampingnya. Ukuran ini dinilai dengan mata, tidak diukur dengan meteran di AR.

**Integrasi (Lab 3 no 5).** Mengganti model di halaman ini sudah saya lakukan dua kali: candi diganti kuda, lalu ditambah mobil. Yang berubah hanya aset dan satu entri konfigurasi `MODELS` di `app.js` (file `.glb`, kamera awal, file hotspot, skala AR). HTML, CSS, panel, bahasa, quiz, dan tombol AR tidak berubah.
- **Model Modul 3:** perlu dikonversi ke GLB dan dikalibrasi ulang. Ukuran patung di catatan Modul 3 (30 × 8 cm, tinggi sekitar 45 cm) ternyata tidak cocok dengan patungnya.
- **Knight Modul 4:** `<model-viewer>` bisa memutar klipnya (`animation-name`, `autoplay`), tetapi Knight akan berjalan di tempat. Gerak majunya di Modul 4 dihitung script Godot dari kaki yang menapak.
- **Di kedua kasus:** posisi hotspot dihitung ulang dengan ray, dan normalnya dipilih ulang.

**Refleksi (Lab 3 no 6).** `<model-viewer>` mengambil alih sesi AR di tiga platform, termasuk membuat USDZ otomatis untuk Quick Look, ditambah render, kamera, dan penempatan hotspot di layar. Yang tetap harus saya benahi sendiri: isi yang benar, skala (`ar-scale="fixed"` hanya mengunci ukuran yang ada di file), provenance, letak dan normal hotspot, dan bug di bahan yang terlihat sudah jadi (T10, T11). Rinciannya ada di `fase5-ar-app.md` bagian 11.

## 5. Keterbatasan

- **Model terlalu berat untuk HP lama.** Mobil (7,7 MB, 161 ribu segitiga, tekstur 4096 px) terbukti jalan di iPhone 17 Pro, tetapi di HP dengan GPU dan memori kecil bisa lambat atau gagal dimuat. Kalau itu terjadi, versi tekstur 2048 px (5,9 MB) atau subdivisi 0 harus dipakai.
- **Bagian yang hanya terlihat dari dalam atau dari bawah.** Bawah alas kuda tidak pernah terfoto (di sana letak 80 tepi terbuka). Bidikan pertama saya di dalam kokpit mobil salah di 86 dari 288 kamera latih, sampai titiknya dipindah. Hotspot di bagian seperti itu tidak bisa diandalkan, karena `<model-viewer>` hanya memeriksa normal.
- **Browser tanpa WebXR atau Quick Look.** Di browser desktop atau browser HP tanpa dukungan AR, tombol "View in your space" tidak membuka sesi AR. Model tetap bisa diputar di halaman. Android (Scene Viewer) belum saya uji.
- **Normal hotspot dipilih untuk kamera otomatis `<model-viewer>` di layar portrait 390 × 800.** Di AR sungguhan kamera bisa berada jauh lebih dekat, jadi hasil occlusion bisa berbeda.
- **Pipeline NeRF sungguhan (nerfstudio, COLMAP, GPU CUDA) tidak dijalankan** (Optional Extension, I15). Rekonstruksi di laporan ini adalah grid voxel 12³ dari gambar sintetis 20 × 16 px. Foto HP saya dipakai untuk kamera, ray, dan scan photogrammetry, bukan untuk NeRF.
- **Belum pasti secara hukum.** Hak cipta desain patung kuda (pembuatnya tidak diketahui) dan penayangan logo merek di mobil lewat halaman publik ditandai "This needs verification" di LICENSE.md.

## 6. Reproduksi (A5)

Transkrip lengkap ada di `docs/catatan/fase6-reproduksi.md`. Dari clone bersih dengan `.venv` baru:
- `pip install -r requirements.txt` (freeze sama persis);
- `capture.py`, `make_temple_glb.py`;
- `tests.py` **81 ok**;
- `fit_nerf_toy.py` 20.32 / 14.85 dB, `nerf_bug.py` +2.66 dB, `my_ray.py` sama sampai 5 desimal;
- `verify_ar_app.py` **17 ok**, dengan server di `127.0.0.1`.

Setelah dua file dosen disimpan dalam versi hasil generate Mac, `git status` di clone tetap bersih. `kuda.glb` dan `amr23.glb` adalah hasil jadi dari sumber besar yang tidak di-commit. Script dan checksum sumbernya ada di repo, dan dari sumber yang sama hasilnya identik byte per byte.

**AR app:** https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module5/Source/ar_app/index.html, diuji di iPhone 17 Pro, iOS 27.2, Safari.

## 7. Penyimpangan dari modul

- **Path:** `code/Module5/` di modul adalah `Module5/Source/` di repo ini (K1).
- **Pipeline:** toy pipeline NumPy menggantikan nerfstudio, COLMAP, dan GPU. Optional Extension tidak dijalankan.
- **`nerf_bug.py --diagnose`:** ditambahkan, dan penjelasan dosen yang membocorkan jawaban dipindah ke catatan (K14).
- **Data latih:** dibaca dari PPM, bukan render ulang (T5, K17).
- **Temuan starter yang dibuktikan:**
  - T2 (17 ok bukan ukuran cakupan);
  - T3 (gradien salah di kondisi ekstrem);
  - T4 (dua konvensi pixel);
  - T7 (pelajaran view coverage bergantung pada sudut uji);
  - T8 (pitfall init bergantung learning rate);
  - T9 (diukur ulang di Mac: 55.776 dari 81.920 sampel, 68,1%, berada di luar kubus grid; dampaknya pada kualitas tidak saya klaim);
  - T10 (stupa terbalik);
  - T11 (tombol bahasa);
  - T13 (`T_N` vs `T(N+1)`).
- **Catatan bacaan:** modul menyebut Marschner & Shirley "Bab 13 (kamera)", padahal Bab 13 edisi 5 berjudul *Sampling* menurut daftar isi penerbit.
- **AR app:** memakai model saya sendiri dan model CC BY dengan skala dari regulasi resmi. Candi dosen tidak lagi ditampilkan.
