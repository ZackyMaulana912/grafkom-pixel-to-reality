# Fase 3: Primitif from-scratch (Lab 2 no 1)

## Penurunan sumbu terkunci untuk urutan Euler lain (ditulis sebelum cek numerik)

Bagian ini saya tulis dulu dengan tangan, sebelum menjalankan cek angkanya.

**Aturan umum.** Tulis urutan sebagai `M = R_luar(a) · R_tengah(b) · R_dalam(c)`. Matriks paling kanan bekerja paling dulu pada vektor. Kalau sumbu tengah diputar 90°, misalkan `R_tengah(90°)` mengirim sumbu dalam ke `s` kali sumbu luar, dengan `s = +1` atau `-1`. Memutar dengan sudut c terhadap sumbu dalam, lalu memutar seluruhnya dengan `R_tengah(90°)`, sama dengan lebih dulu memutar dengan `R_tengah(90°)` lalu memutar sejauh c terhadap bayangan sumbu dalam, yaitu `s` kali sumbu luar:

```
R_tengah(90°) · R_dalam(c) = R_luar(s·c) · R_tengah(90°)
M = R_luar(a) · R_luar(s·c) · R_tengah(90°) = R_luar(a + s·c) · R_tengah(90°)
```

Jadi saat sumbu tengah 90°, hanya kombinasi `a + s·c` yang terlihat, dan satu derajat kebebasan hilang. Yang terkunci selalu **sumbu tengah**.

**Urutan bawaan saya, ZYX = Rz(roll) · Ry(yaw) · Rx(pitch).** Sumbu tengahnya y. Kolom pertama Ry(90°) adalah (0, 0, -1), jadi sumbu x jatuh ke -z, dan `s = -1`. Hasilnya `M = Rz(roll - pitch) · Ry(90°)`. Ini sama dengan Studi Pendahuluan Q3(b).

**Urutan alternatif untuk Lab 2, XZY = Rx(pitch) · Rz(roll) · Ry(yaw).** Sumbu tengahnya z (roll), jadi prediksi saya: **yang terkunci adalah roll = 90°, bukan yaw.** Rz(90°) mengirim sumbu y ke (-sin 90°, cos 90°, 0) = (-1, 0, 0), yaitu -x. Sumbu dalam (y) jatuh ke minus sumbu luar (x), jadi `s = -1`:

```
M(roll = 90°) = Rx(pitch - yaw) · Rz(90°)
```

Prediksi yang bisa diuji:
1. Pada roll = 90°, pasangan (pitch, yaw) yang selisihnya sama, misalnya (20, 10), (15, 5), dan (10, 0), menghasilkan matriks yang sama sampai pembulatan float (kurang dari 1e-12).
2. Pada **yaw** = 90° dengan urutan yang sama, menjaga selisih pitch dan roll tetap **tidak** membuat matriksnya sama. Selisihnya harus jelas besar, jauh di atas pembulatan, karena yaw adalah sumbu dalam, bukan sumbu tengah.

**Urutan bawaan Godot, YXZ = Ry(yaw) · Rx(pitch) · Rz(roll)** (intrinsic YXZ menurut dokumentasi `Node3D`). Sumbu tengahnya x (pitch). Rx(90°) mengirim sumbu z ke (0, -sin 90°, cos 90°) = (0, -1, 0), yaitu -y, jadi `s = -1` dan `M(pitch = 90°) = Ry(yaw - roll) · Rx(90°)`. Prediksinya: di Godot yang terkunci adalah **pitch = 90°**, dengan hanya yaw - roll yang terlihat. Demo starter `gimbal_lock_demo.gd` justru mematok yaw = 90° dan menjaga pitch - roll, jadi kemungkinan besar demo itu tidak terkunci (temuan T4). Di fase ini prediksi tersebut baru saya cek dengan matriks Python. Bukti dari Godot sendiri (mencetak `Basis`) baru dikerjakan di Fase 5.

## Hasil cek numerik urutan Euler (dijalankan setelah penurunan di atas)

```
order ZYX: locks at yaw = 90, only roll - pitch survives
order XZY: locks at roll = 90, only pitch - yaw survives
order YXZ: locks at pitch = 90, only yaw - roll survives
```

Baris di atas dicetak `quaternion.py`. Fungsi `lock_rule()` menghitung bayangan sumbu dalam di bawah `R_tengah(90°)` dengan matriks, dan hasilnya sama dengan ketiga penurunan tangan (`s = -1` untuk ketiganya).

| Urutan | Pasangan yang dicek | Selisih matriks maksimum | Artinya |
|---|---|---|---|
| XZY | roll = 90°, (yaw, pitch) = (20, 10), (15, 5), (10, 0), pitch - yaw tetap | 1,11e-16 dan 1,06e-17 | terkunci, sesuai prediksi 1 |
| XZY | yaw = 90°, (pitch, roll) = (20, 10), (15, 5), (10, 0), pitch - roll tetap | 0,0865 dan 0,174 | tidak terkunci, sesuai prediksi 2 |
| XZY | roll = 90°, pitch + yaw tetap, (10, 20) vs (20, 10) | 0,347 | kombinasi yang salah memang terlihat |
| YXZ (Godot) | pitch = 90°, yaw - roll tetap | 1,11e-16 dan 1,06e-17 | terkunci di pitch |
| YXZ (Godot) | yaw = 90°, pitch - roll tetap (yang dipakai demo starter) | 0,0865 dan 0,174 | tidak terkunci, jadi T4 kemungkinan besar benar |

Kedua prediksi untuk XZY tepat. Angka 0,0865 dan 0,174 untuk YXZ sama dengan simulasi saat run awal (T4). Ini tetap simulasi Python. Buktinya dari Godot sendiri baru diambil di Fase 5.

## Cara saya menulis ulang tiap primitif

Starter sudah berisi kode yang jalan, jadi tujuan menulis ulang bukan sekadar mengganti nama variabel. Saya menyusun tiap file dengan cara yang paling dekat dengan konsep di modul, lalu membuktikan hasilnya tetap sama.

**`fk.py`: FK sebagai perkalian matriks lokal.** Setiap bone menyumbang satu matriks homogen 3 × 3 `R(θ) · T(l, 0)`, artinya putar sebesar sudut lokal lalu berjalan sepanjang sumbu x bone itu sendiri. Matriks dunia sendi ke-i adalah perkalian matriks dari root sampai bone i, persis seperti rantai `M` di Modul 3. Posisi sendi dibaca dari kolom translasi matriks itu. Sudut global tetap dihitung sebagai jumlah sudut lokal, karena itulah definisinya dan hasilnya pasti tepat. Test baru mengecek keduanya selalu sepakat pada 500 rantai acak (1 sampai 6 bone): selisih posisi dan sudut di bawah 1e-9. Konvensi seluruh modul ditulis sekali di docstring paling atas file ini.

**`ik.py`: aturan cosinus, menolak target tak terjangkau.** θ2 dihitung dari sudut dalam segitiga di siku (`θ2 = 180° - α`), sesuai penurunan di Studi Pendahuluan Q2(b). Target di luar cincin `|l1 - l2| ≤ d ≤ l1 + l2` selalu melempar `UnreachableTarget`. Clamp pada `acos` hanya dipakai untuk pembulatan float **setelah** reachability dicek. Solusi starter yang disebut "elbow-up" saya beri nama yang jujur, yaitu solusi θ2 ≥ 0, karena untuk target (4, 1) sikunya justru di bawah garis bahu-target (T7).

**`spline.py`: bobot basis Catmull-Rom.** Starter menulis rumusnya sebagai empat suku polinomial. Saya menuliskannya sebagai empat **bobot** untuk P0 sampai P3, yaitu baris matriks basis Catmull-Rom dikali (1, t, t², t³). Bentuk ini membuat sifat-sifatnya mudah dicek: bobotnya selalu berjumlah 1, di t = 0 bobotnya (0, 1, 0, 0), dan di t = 1 bobotnya (0, 0, 1, 0), jadi kurva pasti melewati P1 dan P2. Saya juga menambah `sample_spacing()` untuk mengukur jarak antar sampel (T8) dan `load_my_path()` untuk jalur saya.

**`quaternion.py`: perkalian, normalisasi, dan Euler dengan urutan sebagai parameter.** Fungsi baru: `quat_mul` (perkalian Hamilton), `quat_conj`, `quat_norm`, `quat_normalize`, `quat_rotate` (`q v q*`), dan `quat_to_matrix`. Euler sekarang dihitung `euler_to_matrix(pitch, yaw, roll, order)` dengan urutan berupa teks, misalnya "ZYX" atau "YXZ". `euler_xyz_to_matrix` tetap ada sebagai nama lama untuk "ZYX", dan docstring-nya sudah dibetulkan. Docstring starter menulis "Intrinsic X -> Y -> Z", padahal yang dihitung `Rz · Ry · Rx`, yaitu extrinsic X, Y, Z atau intrinsic Z, Y', X'' (T3). `slerp` tidak lagi menormalisasi hasilnya setiap kali: rumus sin/sin sudah menghasilkan quaternion satuan, dan normalisasi hanya dipakai di cabang blend linear untuk dua quaternion yang hampir sama. Test baru memastikan hasil slerp tetap ber-norm 1 sampai 1e-12.

### Bukti hasilnya sama dengan kode dosen

Saya menjalankan versi baru dan versi starter (diambil dari commit `8b7ff5d`) pada input acak yang sama, masing-masing 2000 kasus per fungsi dengan seed tetap. Tabel ini dari `ik.py` setelah perbaikan di bagian berikutnya:

| Fungsi | Jumlah angka dibandingkan | Selisih maksimum |
|---|---|---|
| `forward_kinematics` (1 sampai 5 bone) | 21.871 | 8,0e-15 |
| `solve_two_bone_ik` (1588 target tak terjangkau di kedua versi, tidak ada yang berbeda) | 2.412 | 1,2e-13 derajat |
| `catmull_rom_point` 3D | 6.000 | 4,4e-15 |
| `slerp` | 8.000 | 3,3e-16 |
| `euler_xyz_to_matrix` | 18.000 | 0 |
| `sample_path(camera_path.json)` | 123 | 1,8e-15 |

Semua contoh E1 sampai E4 tetap mencetak angka yang sama. Satu perubahan yang terlihat: `ik.py` versi baru mencetak `position error = 4.44e-16`, sama dengan PDF dan starter di Mac.

### Temuan: aturan cosinus di bahu kurang teliti saat lengan hampir lurus

Versi pertama `ik.py` saya menghitung sudut bahu juga dengan aturan cosinus (sudut dalam β di bahu, lalu θ1 = arah target - β). Contoh E2 lolos, tapi test baru yang menguji 20.000 target acak, termasuk target yang sangat dekat batas jangkauan, menunjukkan error IK lalu FK sampai **1,4e-7**, jauh di atas syarat 1e-9. Kode starter pada target yang sama hanya 5,7e-13. Kasus terburuknya lengan 0,33 dan 3,62 dengan target tepat di batas luar.

Penyebabnya: di dekat lengan lurus, nilai cosinus mendekati 1, dan `acos` di daerah itu sangat sensitif. Galat pembulatan sebesar 1e-16 pada argumen bisa menjadi galat sekitar 1e-8 radian pada sudut. Kalau θ1 dan θ2 masing-masing dihitung dengan `acos` sendiri, galatnya tidak saling menutupi, sehingga tangan meleset ke samping garis bahu-target. Perbaikannya: θ1 dihitung dari θ2 yang benar-benar dipakai, yaitu `θ1 = atan2(ty, tx) - atan2(l2 sin θ2, l1 + l2 cos θ2)`. Dengan begitu tangan selalu tepat di garis bahu-target, dan galat θ2 hanya menggeser tangan sepanjang garis itu, yang dampaknya jauh lebih kecil. Setelah diubah, error terburuknya **1,4e-12**. Ini memang bentuk yang sama dengan starter, tetapi sekarang saya tahu alasannya dari pengukuran, bukan karena menyalin.

## Rantai 3-bone saya

FK rantai 3-bone (lengan atas, lengan bawah, tangan) sudah dihitung dengan tangan di catatan Fase 2, dan `test_my_chain` mengeceknya: siku (28,970; -1,316), pergelangan (32,807; 22,376), ujung jari (26,860; 41,471). Test itu tetap hijau dengan `fk.py` versi matriks.

Saya juga menjalankan IK lalu FK pada lengan saya sendiri. Posisi pergelangan hasil FK (32,807; 22,376) cm saya jadikan target `solve_two_bone_ik(29, 24, ...)`, dan IK mengembalikan θ1 = -2,60° dan θ2 = 83,40°, yaitu sudut dari foto, dengan error FK 7,1e-15 cm. Solusi cerminnya θ1 = 71,19° dan θ2 = -83,40°, yaitu siku menekuk ke arah sebaliknya. Lengan saya sungguhan tidak bisa menekuk ke arah itu, jadi pemilihan solusi θ2 ≥ 0 memang cocok untuk siku manusia. Jangkauan lengan 2-bone saya adalah 5 cm ≤ d ≤ 53 cm.

![IK lengan saya](../img/ik_my_arm.png)

## Jalur kamera saya dan jarak antar sampel (T8)

Titik kontrol di `data/my_path.json` sudah disetujui. Ada 6 titik di lingkaran berjari-jari 0,6 m di sekitar patung kuda (x = -0,2, z = 0) dari model ruangan Modul 3, pada sudut 0°, 60°, ..., 300° dari +z, dengan tinggi 1,15 m (sama dengan tinggi mata kamera scene Modul 3). Kamera melihat ke (-0,2; 0,25; 0), yaitu tengah patung.

```
my_path.json: 6 control points -> 51 sampled points
  path start = (-0.200, 1.150, 0.600)
  path end   = (-0.720, 1.150, 0.300)
  sample spacing min 0.037, max 0.072 (equal t steps, unequal distance)
```

Kelima puluh satu titik sampelnya dicetak lengkap oleh `spline.py`.

![Jalur saya dari atas dan jarak antar sampel](../img/my_path.png)

Yang saya pelajari dari gambar dan angkanya:

- **Kurva memotong sedikit ke dalam lingkaran.** Jarak ke patung 0,551 sampai 0,6003 m. Catmull-Rom antar titik di lingkaran tidak mengikuti busur, tapi sedikit menyudut ke dalam. Angka 0,6003 terjadi karena titik 0,32 adalah pembulatan dari 0,3196. Test awal saya yang menuntut "tidak pernah keluar dari 0,6 m" gagal karena pembulatan ini, jadi saya ganti dengan syarat yang sebenarnya penting: jarak ke dinding dan lemari minimal 0,2 m. Hasilnya 0,215 m.
- **Langkah t sama besar, jarak tempuh tidak.** Jarak antar sampel di jalur saya antara 0,037 dan 0,072 m. Di `camera_path.json` dosen antara 0,373 dan 0,719. Langkah paling pendek ada di kedua ujung: karena titik pertama dan terakhir digandakan, tangen di ujung hanya separuh, jadi kamera mulai dan berhenti pelan. Kalau kamera Godot berjalan per indeks sampel, kecepatannya naik turun seperti grafik kanan. Kalau berjalan menurut panjang busur (`PathFollow3D.progress_ratio`), kecepatannya rata. Perbedaan ini dibahas lagi di Fase 5.
- **Jalurnya terbuka, tidak menutup.** `sample_path` memakai ujung yang digandakan, jadi jalur 300° ini berhenti di P5 dan tidak menyambung mulus ke P0. Untuk satu putaran penuh yang mulus dibutuhkan Catmull-Rom tertutup (titik tetangga diambil melingkar). Ini saya catat sebagai keterbatasan.

## Test baru

`tests.py` sekarang mencetak `ALL CHECKS PASSED (109 ok)`, dari 40 di starter dan 52 setelah Fase 2. Yang ditambah:

| Test | Isi |
|---|---|
| `test_ik_more` | batas dalam (d = 0,5 dan 0,999) dan batas luar (5,001 dan 6) melempar `UnreachableTarget`; tepat di batas luar θ2 = 0°, tepat di batas dalam θ2 = 180°; error IK lalu FK di bawah 1e-9 untuk 20.000 target acak, termasuk yang mepet batas |
| `test_my_chain` (tambahan) | IK dari posisi pergelangan saya mengembalikan sudut foto (-2,6° dan 83,4°) sampai 1e-9 |
| `test_fk_matrices` | perkalian matriks sama dengan definisi jumlah sudut, 500 rantai acak |
| `test_my_path` | 6 titik menjadi 51 sampel; sampel ke-0, 10, ..., 50 tepat di titik kontrol; jarak ke dinding dan lemari minimal 0,2 m; bobot Catmull-Rom berjumlah 1 |
| `test_camera_path_copies` | `control_points` di `data/` dan `godot_project/data/` identik (K11) |
| `test_euler_orders` | XZY terkunci di roll = 90° dan tidak di yaw = 90°; YXZ (Godot) terkunci di pitch = 90° dan tidak di yaw = 90°; `lock_rule` untuk ketiga urutan |
| `test_quaternion_algebra` | q(z, 30°) · q(z, 60°) = q(z, 90°); `quat_to_matrix` sama dengan Rx, Ry, Rz; quaternion ber-norm 1,01 memperbesar vektor 1,0201 kali; hasil slerp ber-norm 1 |
| `test_stdlib_only` | file from-scratch (`fk`, `ik`, `spline`, `quaternion`, `foot_slide_bug`, `my_chain`) hanya meng-import standard library dan satu sama lain, dibaca dengan modul `ast` (K2) |

Toleransi test gimbal lock starter saya **perketat** dari 1e-9 menjadi 1e-12, sesuai target di modul. Tidak ada test yang dilonggarkan.

Saya juga membuktikan `test_stdlib_only` benar-benar bisa gagal: setelah `import numpy` saya sisipkan sementara ke `spline.py`, test langsung mencetak `[FAIL] spline.py imports only ...: got=['numpy']`. Setelah dikembalikan, test hijau lagi.

## Gambar

`figures.py --set readme` sekarang membuat `docs/img/my_chain_fk.png`, `docs/img/ik_my_arm.png`, dan `docs/img/my_path.png`. Dua gambar Studi Pendahuluan (`q3_slerp_vs_linear.png` dan `q3_spline_vs_linear.png`) ikut saya buat ulang dengan kode baru. Perbedaannya hanya 141 pixel dan 2 pixel, dengan selisih warna paling besar 2 dari 255 (pembulatan float di urutan 1e-15 yang menggeser antialiasing). Saya tetap meng-commit versi barunya, supaya file di repo sama persis dengan yang dihasilkan kode sekarang.

## Tambahan 31 Oktober 2026: Catmull-Rom tertutup

Di atas saya mencatat keterbatasan bahwa `sample_path` hanya bisa membuat jalur terbuka: titik pertama dan terakhir digandakan, jadi jalur 300° saya berhenti di P5 dan tidak menyambung ke P0. Di Godot kamera akhirnya harus bolak-balik. Sekarang `spline.py` punya `sample_closed_path()`. Bedanya hanya pada cara mengambil titik tetangga: segmen ke-i memakai P(i-1), P(i), P(i+1), P(i+2) dengan indeks yang berputar (setelah P5 kembali ke P0), sehingga ada satu segmen tambahan dari P5 kembali ke P0. Enam titik menjadi 6 segmen dan 60 sampel. Sampel ke-60 akan sama dengan sampel ke-0, jadi tidak ikut ditulis.

Supaya kehalusannya bisa dibuktikan, saya juga menambah `catmull_rom_tangent()`: turunan q'(t) yang memakai turunan keempat bobot basis. Hasil cek dari `tests.py`:

| Pemeriksaan | Hasil |
|---|---|
| sampel ke-0, 10, ..., 50 tepat di titik kontrol | selisih 0 (bobot di t = 0 tepat (0, 1, 0, 0)) |
| tangen di ujung segmen yang datang = tangen di awal segmen yang pergi, di keenam sambungan termasuk P5 ke P0 | selisih 0 |
| tangen di setiap titik = (titik berikutnya - titik sebelumnya) / 2 | selisih 0 |
| `catmull_rom_tangent` vs beda hingga dari `catmull_rom_point` | 6e-11 |
| jarak terdekat ke dinding dan lemari (1200 sampel) | 0,215 m |
| jarak ke patung | 0,585 sampai 0,6003 m |
| jarak antar sampel | 5,45 sampai 6,73 cm (terbuka: 3,71 sampai 7,18 cm) |

Jalur tertutup lebih rata, karena tidak ada lagi titik yang digandakan. Langkah paling pendek di ujung jalur terbuka (setengah tangen) hilang, dan rasio langkah terpanjang ke terpendek turun dari 1,94 menjadi 1,23. Kurva juga memotong ke dalam lingkaran lebih sedikit (paling dekat 0,585 m, sebelumnya 0,551 m), karena segmen P5 ke P0 dan P0 ke P1 sekarang punya tetangga yang sebenarnya. Keterbatasan C1 tetap ada: percepatannya masih bisa melompat di titik kontrol, karena Catmull-Rom bukan C2.

![Jalur terbuka, tertutup, dan jarak antar sampel](../img/my_path.png)

Test bertambah dari 134 menjadi 158 (`test_closed_path`).
