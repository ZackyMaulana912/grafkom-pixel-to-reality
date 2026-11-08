# Persiapan viva Modul 5

Yang diminta modul (A5): menjalankan `python tests.py` langsung, membuka AR app di HP dan memicu AR, menjelaskan satu commit, dan menjawab dua pertanyaan dari modul. Jawaban di bawah memakai angka dari run saya sendiri.

## Yang dijalankan saat viva

```
cd Module5/Source && source .venv/bin/activate
python tests.py          # ALL CHECKS PASSED (81 ok), sekitar 14 detik
python my_ray.py         # ray dari pixel (1200, 6100) foto iPhone saya
python nerf_bug.py --sweep
```

AR app di HP: buka https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module5/Source/ar_app/index.html di Safari, lalu ketuk "View in your space (AR)". Patung muncul seukuran aslinya, 63 cm. Tombol Model berganti ke mobil, yang boleh dicubit.

**Commit yang paling enak dijelaskan:** `cfd7ec3` (rumus gradien saya, `T_k (c_k - B_k)`). Ceritanya: menurunkan rumus sendiri, membuktikannya sama dengan rumus modul, lalu menemukan bahwa rumus starter salah tanda di kondisi hampir padat. Cadangannya `24bd4c0` lalu `30582ae`: prediksi occlusion di-commit dulu, baru diuji.

## Dua pertanyaan dari modul

**"Kenapa fungsi aktivasi ini di sini?"**
- **Softplus pada density:** density harus tidak negatif. Dengan density negatif, `α = 1 - exp(-σδ)` jadi negatif. Contoh saya: σ = -1 dan δ = ln 2 memberi α = -1, transmittance naik ke 2, dan warna akhirnya `(2; -1; 0)`.
- **Sigmoid pada warna:** warna harus berada di [0, 1].
- **Kenapa softplus, bukan ReLU** (NeRF asli memakai ReLU): turunan softplus adalah `sigmoid(x)`, yang tidak pernah nol, jadi voxel yang terlanjur negatif tetap bisa pulih. Tapi sinyalnya bisa sangat kecil: `sigmoid(-5) = 0,0067`. Karena itu nilai awal -5 macet di lr 5. Di eksperimen saya, MSE hanya turun 0,0003 dalam 300 iterasi.

**"Apa yang terjadi kalau model ini punya lubang yang bisa dilewati ray sampai tembus?"**
- **Di volume rendering:** ray yang lewat lubang hanya melewati sampel ber-density rendah, jadi transmittance-nya tetap tinggi sampai ujung. Sisa `T(N+1)` menjadi besar, dan pixel itu menampilkan warna latar. Bobot ditambah sisa latar tetap berjumlah tepat 1, jadi tidak ada cahaya yang hilang atau tercipta.
- **Saat latihan:** kalau foto latih memperlihatkan latar di situ, gradiennya akan menurunkan density voxel di sepanjang ray itu. Kalau foto tidak pernah melihat lubang itu, grid bisa saja mengisinya dengan density palsu, persis masalah view coverage.
- **Di model AR saya:** scan kuda punya 83 tepi terbuka, 80 di antaranya di bawah alas. Celah itu tidak terlihat karena alas berdiri di lantai. Kalau ada lubang di bagian yang terlihat, ray `occlusion.py` akan lewat, dan hotspot di belakangnya dianggap terlihat. `<model-viewer>` tidak peduli lubang itu, karena ia hanya melihat normal.

## Pertanyaan tambahan yang mungkin muncul

**Kenapa harus held-out view, dan kenapa satu sudut tidak cukup?**
PSNR latih mengukur seberapa baik model menghafal yang ia lihat. Model 2 view punya PSNR latih 21,13 dB, lebih tinggi dari model 8 view (19,13), padahal kalah di 7 dari 8 sudut baru. Satu sudut bisa menyesatkan: di 22,5° model 2 view justru menang 1,71 dB, karena sudut itu hanya 2,5° dari view latihnya. Untuk view ketiga, kesimpulannya juga terbalik kalau hanya diukur di 8 sudut, dibanding diukur di seluruh lingkaran.

**Kenapa gradien perlu dicek dengan finite difference, dan apa yang terjadi kalau suku `suffix` hilang?**
Turunan yang ditulis tangan adalah klaim. Finite difference menggeser satu parameter sedikit, lalu mengukur perubahan loss secara langsung, tanpa mempercayai rumusnya. Kalau suku "yang di belakang" (suffix, `B_k` di rumus saya) dibuang, rumus hanya menghitung bahwa sampel k jadi lebih terlihat, dan lupa bahwa yang di belakangnya jadi lebih tertutup. Cek starter gagal dengan `1.91e-01`, jauh di atas ambang `1e-6`. Tetapi cek starter tidak menangkap bug rumus starter di kondisi ekstrem. Itu yang ditangkap test saya yang mengecek setiap voxel.

**Kenapa `1 - α` perlu dijaga?**
Rumus modul membagi dengan `1 - α`, yang nol untuk sampel padat. Starter menjepit penyebut di `1e-6` dan memakai cabang khusus untuk `α ≥ 1 - 1e-9`. Di antara dua batas itu hasilnya salah sampai tandanya terbalik. Rumus saya tidak membagi sama sekali, jadi tidak ada yang perlu dijaga.

**Kenapa bobot tidak pernah lebih dari satu, dan kenapa jumlahnya 1?**
`w_i = T_i α_i`, dengan `0 ≤ α ≤ 1` dan T tidak pernah naik. Setiap sampel hanya mengambil bagian dari cahaya yang belum diambil sampel di depannya, dan sisanya menjadi milik latar. Totalnya selalu 1, dan `test_composite_image_matches_composite` mengecek ini di setiap ray.

**Kenapa skala model harus dalam meter?**
glTF memakai meter, dan `ar-scale="fixed"` mengunci ukuran yang ada di file. Hasil scan dari foto tidak punya ukuran: kudanya 1,015 "unit". Karena itu saya mengukur alas 46 cm dengan tangan, lalu tinggi 62,8 cm vs 63 cm membuktikan skalanya benar. Untuk mobil, skalanya dari aturan FIA: ban 725 mm, lalu lebar 2,006 m mengecek. Di iPhone, kuda terlihat seukuran aslinya.

**Kenapa normal hotspot boleh tidak sama dengan normal permukaan?**
`<model-viewer>` hanya memakai normal untuk memutuskan dari arah mana hotspot terlihat (terbukti dari kodenya). Jadi normal itu saya pilih supaya keputusannya cocok dengan occlusion sebenarnya, dengan kamera latih yang terpisah dari kamera uji supaya tidak curang. Hasilnya, hotspot yang tampil padahal tertutup turun dari 7 menjadi 0.

**Apa beda AR berbasis marker dan markerless?**
Marker memberi posisi, arah, dan skala dari pola cetak yang ukurannya diketahui. Markerless (SLAM) memetakan lantai dari kamera dan sensor gerak, lalu menaruh model lewat ray hit test. Yang dipakai Quick Look di iPhone saya adalah markerless.

**Kenapa memilih Object Capture, dan apa kelemahannya?**
Object Capture ada di macOS, tanpa GPU CUDA, dan hasilnya jauh lebih detail dari model pipih Modul 3. Kelemahannya: hasil dari JPG tidak punya ukuran, sehingga harus dikalibrasi dengan tangan. Bawah alas juga tidak pernah terfoto. Dan apakah scan ulang menghasilkan file yang sama belum saya uji.

**Kenapa app menampilkan pesan merah kalau file gagal dimuat?**
Starter hanya menulis error ke console, yang tidak dilihat pengguna HP. Model yang hilang membuat layar tertahan di "Loading the model…" selamanya, dan file hotspot yang hilang membuat patung tampil tanpa titik info tanpa penjelasan apa pun. Pesan merah menyebut file mana yang gagal dan apa yang perlu dicek, dalam bahasa yang sedang dipilih. `verify_ar_app.py` membuktikannya dengan menyajikan file itu sebagai 404 (20 ok).

**Apa yang belum diuji?**
- Android (Scene Viewer);
- ukuran AR dengan meteran (selama ini hanya dengan mata);
- pipeline nerfstudio di GPU;
- uji mobil di HP.
