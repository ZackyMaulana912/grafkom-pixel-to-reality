# Fase 2: Model sendiri dan telusuran space (Lab 1)

## 1. Model dan scene

Model saya adalah ruangan patung kuda: 394 segitiga, bertexture foto saya sendiri. Asal setiap angka dan texture-nya ada di [`docs/model/README.md`](../model/README.md).

Semua kamera, model, lampu, dan texture untuk satu model saya tulis di satu file scene (keputusan K13). Di starter, nilai-nilai ini ditulis mati di tiga tempat (`raster3d.py`, `raytrace.py`, `web/viewer.js`), jadi mudah sekali satu renderer memakai kamera yang sedikit berbeda tanpa ketahuan.

| File | Isi |
|---|---|
| `scenes/temple.json` | nilai starter apa adanya. `scene.model_matrix()` untuk file ini terbukti sama persis (`np.array_equal`) dengan `translate((0,0,0)) @ rot_y(35) @ scale((1.4,1.4,1.4))` dari starter |
| `scenes/mymodel.json` | model saya |

**Pilihan world dan kamera di `mymodel.json`.**

- Matriks model `M = T(1, 0, −2)`. Model saya dibuat dengan titik asal di tengah lantai. Setelah digeser (1, 0, −2), titik asal world jatuh di **pojok kiri sisi masuk**, sama dengan titik asal denah Modul 2. Sumbu x world = sumbu x denah, dan sumbu y denah (masuk ke ruangan) = −z world. Jadi koordinat world model 3D bisa langsung dibandingkan dengan `myplan.json`.
- Kamera berdiri di dalam ruangan dekat dinding kiri, mata setinggi 1,15 m di (0,15; 1,15; −0,8), menghadap patung dan pintu lemari di (0,85; 0,3; −2,1). fovy 55°, near 0,1 m, far 10 m.
- Kenapa di dalam ruangan: ruangannya tinggi (3,5 m) dan sempit (2 m). Dari luar atau dari atas, yang terlihat hanya dinding dan bagian atas lemari, sedangkan patungnya tampak sebesar beberapa pixel. Saya sudah mencoba tiga posisi kamera di luar dan tiga di dalam sebelum memilih yang ini.
- Efek samping yang menguntungkan: 71 segitiga (dinding dan lantai di dekat kamera) memotong near plane, dan 51 segitiga seluruhnya ada di belakang kamera. Near clipping di rasteriser benar-benar teruji, bukan cuma teori.

## 2. Telusuran satu vertex (Lab 1 no 3, A1)

Saya memilih **vertex 134**, ujung telinga patung (titik tertinggi garis luar, sisi +x badan patung). Alasannya, posisinya mudah dikenali di render.

```
.venv/bin/python worked_example.py --scene scenes/mymodel.json --vertex 134
```

### Dua langkah pertama dengan tangan

**Langkah 1: object → world, `M p`.** `M = T(1, 0, −2)`, dan rotasi serta skalanya identitas.

```
p     = (−0,170000;  0,450000; −0,019259; 1)
M p   = (−0,17 + 1;  0,45 + 0;  −0,019259 − 2; 1) = (0,830000; 0,450000; −2,019259; 1)
```

**Langkah 2: world → view, `V (M p)`.** `V = lookAt(eye, center, up)` dengan eye `e = (0,15; 1,15; −0,8)` dan center `c = (0,85; 0,3; −2,1)`.

1. Arah pandang `f = c − e = (0,7; −0,85; −1,3)`. Panjangnya √(0,49 + 0,7225 + 1,69) = √2,9025 = 1,703672. Jadi `f̂ = (0,410877; −0,498922; −0,763058)`.
2. Sumbu kanan `s = f̂ × (0, 1, 0) = (−f̂z, 0, f̂x) = (0,763058; 0; 0,410877)`. Panjangnya √0,751077 = 0,866647, jadi `ŝ = (0,880472; 0; 0,474099)`.
3. Sumbu atas `û = ŝ × f̂ = (0,236538; 0,866647; −0,439287)`.
4. Baris V adalah ŝ, û, −f̂, dan kolom 4 adalah −(baris · e). Mengalikan `V` dengan titik world sama dengan memproyeksikan `d = world − e` ke ketiga sumbu itu:

```
d     = (0,83 − 0,15;  0,45 − 1,15;  −2,019259 + 0,8) = (0,68; −0,70; −1,219259)
x_eye =  ŝ · d = 0,880472·0,68 + 0 + 0,474099·(−1,219259)                    = 0,598721 − 0,578049           =  0,020672
y_eye =  û · d = 0,236538·0,68 + 0,866647·(−0,70) + (−0,439287)·(−1,219259) = 0,160846 − 0,606653 + 0,535605 =  0,089798
z_eye = −f̂ · d = −(0,279396 + 0,349245 + 0,930365)                                                           = −1,559006
```

### Perbandingan dengan program

| Space | Hitungan tangan | `worked_example.py` (6 desimal) | Cocok |
|---|---|---|---|
| Object | (−0,170000; 0,450000; −0,019259) | (−0,17; 0,45; −0,019259) | ✓ |
| World `M p` | (0,830000; 0,450000; −2,019259) | (0,83; 0,45; −2,019259) | ✓ |
| View `V M p` | (0,020672; 0,089798; −1,559006) | (0,020670; 0,089798; −1,559007) | ✓ sampai 5 desimal |
| Clip `P V M p` | | (0,039706; 0,172500; 1,388481; 1,559007) | |
| NDC (÷ w) | | (0,025469; 0,110647; 0,890619) | |
| Screen 512 × 512 | | (262,52; 227,67) → pixel (262, 227), depth 0..1 = 0,9453 | |

Selisih di desimal ke-6 berasal dari pembulatan nilai antara saya (6 desimal), bukan dari kodenya.

Yang perlu diperhatikan:

- **`w = −z_eye = 1,559007`.** Telinga patung 1,56 m di depan kamera, jadi `w` memang bernilai `−z`, seperti yang diharapkan.
- **Titiknya di dalam frustum:** −w ≤ x, y, z ≤ w terpenuhi.
- **Depth NDC 0,8906** padahal telinga baru 15% dari jalan menuju far plane (1,56 dari 10 m). Inilah peremukan 1/z di scene saya sendiri.
- Titik itu jatuh di pixel (262, 227). Di render, lingkaran merah memang tepat di ujung telinga patung (`docs/model/render_kamera_bawaan.png`).

## 3. Membaca kolom M dan V (Lab 1 no 4)

```
M = | 1 0 0  1 |      V = | 0,8805  0,0000  0,4741  0,2472 |
    | 0 1 0  0 |          | 0,2365  0,8666 −0,4393 −1,3836 |
    | 0 0 1 −2 |          |−0,4109  0,4989  0,7631  0,0983 |
    | 0 0 0  1 |          | 0       0       0       1      |
```

**M.** Kolom 1 sampai 3 adalah sumbu identitas: model tidak diputar dan tidak di-scale, jadi +x, +y, +z model sama dengan sumbu world. Kolom 4 = (1, 0, −2): titik asal model (tengah lantai) pindah ke (1, 0, −2) di world. Itu tengah ruangan 2 × 4 m kalau pojok jalan masuk ada di (0, 0, 0). Det(M) = 1, positif, jadi tidak ada cermin.

Konfirmasi di render: lemari ada di x model = +0,6 sampai +1,0, jadi di world x = 1,6 sampai 2,0, yaitu **di sisi kanan** ruangan kalau dilihat dari jalan masuk ke arah dalam (−z). Di render, kamera dekat dinding kiri menghadap ke kanan-dalam, dan pintu lemari memang tampak di sebelah kanan. Dinding belakang (z world = −4) tampak di kiri atas sebagai dinding polos.

**V.** Ada dua cara membacanya, dan dua-duanya saya pakai:

- **Baris** V adalah sumbu kamera yang dinyatakan di world. Baris 1 (0,8805; 0; 0,4741) adalah arah "kanan" kamera: kebanyakan +x world (ke arah lemari) dan sedikit +z. Baris 3 (−0,4109; 0,4989; 0,7631) adalah arah "belakang" kamera, jadi kamera menghadap (0,4109; −0,4989; −0,7631): ke kanan, ke bawah, dan masuk ke ruangan.
- **Kolom** V adalah ke mana sumbu world pergi kalau dilihat dari kamera. Kolom 2 (0; 0,8666; 0,4989): sumbu +y world (ke atas) tampak sebagian besar sebagai "atas" di layar (0,8666), dan sedikit mengarah ke kamera (+0,4989), karena kamera menunduk sekitar 30°. Kolom 4 (0,2472; −1,3836; 0,0983) adalah titik asal world (pojok jalan masuk) dilihat dari kamera: sedikit ke kanan, 1,38 m di bawah mata, dan 0,098 m di **belakang** bidang kamera (z positif). Benar, karena pojok jalan masuk ada di belakang kamera.
- `V⁻¹` kolom 4 = (0,15; 1,15; −0,8), tepat posisi kamera. Ini membuktikan `V = pose⁻¹`.

## 4. Bacaan Lab 1 no 5: bab "Coordinate Systems" di learnopengl.com

Saya membaca bab "Coordinate Systems" di learnopengl.com. Rantainya sama dengan `transforms.py`: local → world → view → clip → screen, dengan vertex shader `gl_Position = projection * view * model * vec4(aPos, 1.0)`. Urutannya juga dibaca dari kanan ke kiri, sama seperti di proyek saya.

**Satu hal yang dilakukan berbeda: cara membuat view matrix.** Di bab itu, view matrix dibuat dengan `glm::translate(view, glm::vec3(0.0f, 0.0f, -3.0f))`, yaitu dengan **menggeser seluruh scene** sejauh −3 di z, bukan dengan meletakkan kamera. Alasannya disebut sendiri di bab itu: menggerakkan kamera ke belakang sama dengan menggerakkan scene ke depan. Ini dualitas yang sama dengan Contoh E2. `transforms.py` memakai `look_at(eye, center, up)`, yang membangun pose kamera dari tiga vektor lalu langsung mengembalikan inversnya. Menurut saya ada dua alasan perbedaan itu:

1. Bab itu masih di tahap awal tutorial, jadi translasi saja sudah cukup dan lebih mudah dipahami. `lookAt` baru dibahas di bab berikutnya (Camera).
2. Proyek saya butuh kamera yang bisa diletakkan di mana saja dan menghadap ke mana saja, termasuk menunduk ke patung. Itu tidak bisa dibuat dengan satu translasi.

Ada catatan penting lain di bab itu: OpenGL right-handed di world dan view space, tapi **NDC-nya left-handed**, karena matriks proyeksi membalik sumbu z (near → −1, far → +1, jadi z NDC bertambah **menjauhi** kamera). `transforms.py` mengikuti hal yang sama tanpa menyebutnya. Baru setelah membaca bab ini saya sadar bahwa "right-handed" di bagian atas `transforms.py` hanya berlaku sampai view space.

## 5. Refleksi Lab 1 no 6: akurasi punya taruhan

**(a) Peremukan 1/z dengan angka dari scene saya.** Scene saya memakai near 0,1 m dan far 10 m. Dengan `perspective()` dan depth jendela `(NDC + 1)/2`:

- depth di 1 m = **0,9091** dan di 2 m = 0,9596. Artinya **90,9% kode** depth dipakai untuk meter pertama, padahal tidak ada apa-apa di sana selain ujung dinding;
- di jarak patung (1,56 m), satu langkah kode depth 24-bit setara **0,0014 mm**, sedangkan dengan 16-bit setara **0,37 mm**. Di 4 m (dinding belakang), satu langkah 24-bit sudah 0,0094 mm.

Untuk ruangan sekecil ini, 24-bit masih jauh lebih dari cukup. Scene `zfight` (near 0,001, benda di 15 m, 16-bit) adalah kebalikannya: satu langkah kode sekitar 3,4 m, sehingga dua quad yang berjarak beberapa sentimeter tidak bisa dibedakan. Rumus yang dipakai (Reed 2015) dan reverse-Z (Outerra 2012) dijelaskan di Studi Pendahuluan Q4(a).

**(b) Tabel empat konvensi:** sama dengan Studi Pendahuluan Q4(b). Proyek saya: right-handed, column vector `P·V·M·p`, NDC z `[−1, 1]`, origin UV kiri bawah di file OBJ (dibalik sekali di loader menjadi kiri atas, mengikuti baris gambar). Direct3D: left-handed, row vector `p·M·V·P`, NDC z `[0, 1]`, origin texture kiri atas.

**(c) Scene uji yang mengungkap masing-masing bug:**

- presisi depth: dua quad besar hampir coplanar yang jauh dari kamera (scene `zfight`);
- handedness: model saya sendiri. Kalau tercermin, lemari pindah ke kiri dan kepala kuda menghadap ke arah lain;
- winding: render dengan back-face culling menyala dibandingkan dengan render tanpa culling. Cara ini yang membongkar winding candi starter (temuan T13).

**(d) Satu perubahan yang menangkap pembalikan handedness otomatis:** test yang memeriksa `det(M[:3,:3]) > 0` untuk setiap file scene, dan **signed volume** model tertutup harus positif (semua face CCW dari luar). Badan patung saya adalah model tertutup dengan signed volume positif, sedangkan candi starter negatif. Kedua test ini masuk ke `tests.py` di Fase 3.

Sumber: Reed, "Depth Precision Visualized", 3 Juli 2015. Outerra, "Maximizing Depth Buffer Range and Precision", 28 November 2012. Microsoft Learn, "Coordinate Systems (Direct3D 9)", "Viewports and Clipping (Direct3D 9)", "Coordinate Systems (Direct3D 10)". learnopengl.com, "Coordinate Systems", dibaca 29 Oktober 2026.
