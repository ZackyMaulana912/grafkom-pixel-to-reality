# Fase 5: Godot, dari reproduksi angka sampai scene saya

Semua perintah dijalankan dari `Module4/Source` dengan Godot 4.7.2 (`$GODOT` = `/Applications/Godot.app/Contents/MacOS/Godot`).

## 1. Membuka proyek di editor tanpa mengubah file

Sebelum mengubah apa pun di scene, saya membuka proyek dengan editor Godot dalam mode tanpa jendela, supaya semua file diimpor seperti saat dibuka biasa:

```
$GODOT --headless --editor --path godot_project --quit
```

Hasilnya: kode keluar 0, tidak ada baris error atau warning di log, dan `git status` tidak menunjukkan satu pun file dosen yang berubah (`project.godot`, `Main.tscn`, dan kelima script tetap sama). Editor hanya membuat folder cache `.godot/` (di-ignore) dan `tools/cek_basis.gd.uid` untuk script pemeriksa baru saya. File `.uid` itu ikut di-commit, karena Godot 4.4 ke atas memakainya untuk mengenali script. Ini membuktikan proyek starter cocok dengan Godot 4.7.2 tanpa konversi otomatis. Tampilannya di jendela editor tetap harus saya cek sendiri dengan mata.

## 2. Reproduksi FK/IK di Godot (Lab 2 no 3)

### Yang saya ubah di `arm_kinematics.gd`

- **Angka dicetak dan ditampilkan.** Saat game jalan, script mencetak baris `ARM_FK`, `ARM_IK`, dan `ARM_REACH` ke log, dan sebuah `Label3D` di bawah lengan menampilkan sudut serta posisi siku dan tangan untuk pose yang sedang aktif. Starter tidak mencetak angka apa pun (T5).
- **Target tak terjangkau tidak lagi di-clamp diam-diam (T5).** Starter memaksa jarak target masuk ke rentang terjangkau (`d = clamp(...)`), jadi lengan seolah "berhasil" mencapai target yang mustahil. Sekarang `is_reachable()` mengecek `|l1 - l2| ≤ d ≤ l1 + l2` lebih dulu, sama dengan `ik.py`. Kalau target di luar jangkauan, lengan diluruskan ke arah target, bola target menjadi merah, dan label menulis `TARGET DI LUAR JANGKAUAN` beserta jarak dan batasnya. Clamp pada `acos` hanya tersisa untuk pembulatan float, setelah reachability dicek. Tombol **U** memindahkan target ke (5,5; 0) dan kembali, supaya peringatan ini bisa dilihat saat dimainkan.
- **Rumus IK disamakan dengan `ik.py`**, yaitu θ2 dari sudut dalam siku dan θ1 dari arah target dikurangi arah jangkauan.
- **Hitungan memakai float 64-bit.** Versi pertama saya mengembalikan sudut sebagai `Vector2`. Ternyata `Vector2` di Godot menyimpan float 32-bit, dan `Vector2.length()` juga dihitung 32-bit, sehingga θ2 berbeda 6,3e-6 derajat dari Python. Angka itu masih di bawah 1e-5, tapi penyebabnya penyimpanan, bukan rumus. Setelah semua hitungan memakai `float` biasa GDScript (64-bit, sama dengan Python) dan hasilnya dikumpulkan di `PackedFloat64Array`, selisihnya turun ke 3e-13, yang hanya sisa pembulatan karena dicetak dengan 12 desimal. `Vector3` (32-bit) sekarang hanya dipakai untuk meletakkan mesh di layar.

### Bukti

```
$ $GODOT --headless --path godot_project --quit-after 30 | .venv/bin/python godot_check.py
[ok] FK lokal 30/60: siku dan tangan: selisih 3.17e-13 (toleransi 1e-09)
[ok] IK target (4.0, 1.0): theta1, theta2, tangan vs target: selisih 3.13e-13 (toleransi 1e-09)
[ok] jangkauan (5.5, 0) = false: selisih 0.00e+00 (toleransi 1e-09)
[ok] jangkauan (0.5, 0) = false: selisih 0.00e+00 (toleransi 1e-09)
[ok] jangkauan (4, 1) = true: selisih 0.00e+00 (toleransi 1e-09)
5 baris dibandingkan, 0 di atas toleransinya
```

Baris log dari Godot yang dibandingkan:

```
ARM_FK local=30.000000000000,60.000000000000 elbow=2.598076211353,1.500000000000 hand=2.598076211353,3.500000000000
ARM_IK target=4.000000000000,1.000000000000 theta=-13.178679239300,70.528779365509 hand=4.000000000000,1.000000000000
ARM_REACH target=5.500000000000,0.000000000000 reachable=false
ARM_REACH target=0.500000000000,0.000000000000 reachable=false
ARM_REACH target=4.000000000000,1.000000000000 reachable=true
```

| | Godot 4.7.2 | Python (`fk.py`, `ik.py`) |
|---|---|---|
| siku FK | (2,598076211353; 1,500000000000) | (2,598076211353316; 1,4999999999999998) |
| tangan FK | (2,598076211353; 3,500000000000) | (2,598076211353316; 3,5) |
| θ1, θ2 IK | -13,178679239300; 70,528779365509 | -13,178679239299779; 70,52877936550931 |
| (5,5; 0) dan (0,5; 0) | tidak terjangkau | `UnreachableTarget` |

Tombol Space dan U juga saya uji tanpa jendela. Di sebuah **salinan** proyek (bukan di repo), script pemeriksa mengirim tekanan tombol palsu dengan `Input.parse_input_event`, lalu membaca isi `Label3D` dan warna bola target:

```
f=3   FK  lokal 30.0 / 60.0 deg / siku (2.598, 1.500)  tangan (2.598, 3.500)    target tidak tampil
f=13  IK  theta1 -13.18  theta2 70.53 deg / siku (2.921, -0.684)  tangan (4.000, 1.000)    target hijau
f=23  IK  TARGET DI LUAR JANGKAUAN / d = 5.500, batas [1.000, 5.000]    target merah
f=33  IK  theta1 -13.18  theta2 70.53 deg / siku (2.921, -0.684)  tangan (4.000, 1.000)    target hijau
```

Urutannya: awal (FK), setelah Space (IK), setelah U (target di luar jangkauan), dan setelah U sekali lagi (kembali ke target semula). Siku IK di (2,921; -0,684) berada di bawah garis bahu-target, sama dengan Python (T7). Yang belum terbukti dengan cara ini adalah tampilannya di layar, yaitu posisi label dan apakah lengan terlihat jelas. Itu saya cek sendiri di editor.

**Toleransi.** `godot_check.py` memakai dua toleransi, karena Godot punya dua jenis angka. Hitungan lengan memakai float 64-bit, sama dengan Python, jadi harus cocok sampai 1e-9. Komponen `Basis`, `Vector2`, dan `Vector3` disimpan sebagai float 32-bit, yang membulatkan angka sebesar paling banyak 1 dengan galat sekitar 6e-8, jadi `Basis` dibandingkan dengan toleransi 1e-5. Batas ini masih jauh di bawah perbedaan yang sungguhan: pasangan T4 yang tidak terkunci berselisih lebih dari 0,08. Saya juga membuktikan pembandingnya bisa gagal: baris FK yang sengaja saya geser 0,002 ditandai `BEDA` dan programnya keluar dengan kode 1. `tests.py` juga punya test untuk ini (`test_godot_check_parser`).

## 3. Bukti T4 dari Godot sendiri

Di Fase 3 saya memprediksi dari matriks Python bahwa urutan bawaan Godot (intrinsic YXZ = Ry · Rx · Rz) terkunci di **pitch** = 90°, sehingga demo starter, yang mematok **yaw** = 90° dan menjaga pitch - roll tetap, tidak terkunci. Sekarang saya mengambil buktinya dari Godot.

Script `tools/cek_basis.gd` membuat sebuah `Node3D`, mengisi `rotation` dengan beberapa kombinasi sudut, lalu mencetak `Basis` yang dibangun Godot, untuk urutan bawaan dan untuk `EULER_ORDER_ZYX`:

```
$ $GODOT --headless --path godot_project --script res://tools/cek_basis.gd
CEK rotation_order_default=2 EULER_ORDER_YXZ=2 EULER_ORDER_ZYX=5
BASIS yaw90_beda10 order=2 deg=20.0,90.0,10.0 m=0.059391126,0.336824059,0.939692616,...
BASIS yaw90_beda10 order=2 deg=15.0,90.0,5.0 m=0.022557521,0.257834166,0.965925813,...
BASIS yaw90_beda10 order=2 deg=10.0,90.0,0.0 m=-0.000000044,0.173648179,0.984807730,...
...
```

Pertama, `rotation_order` bawaan sebuah `Node3D` memang 2, yaitu `EULER_ORDER_YXZ`, sesuai dokumentasi. Kedua, setiap `Basis` dari Godot cocok dengan `euler_to_matrix` Python untuk urutan yang sesuai ("YXZ" untuk 2, "ZYX" untuk 5). Selisih terbesar dari 16 matriks adalah 7,6e-8, sebesar pembulatan float 32-bit. Jadi urutan Godot terbukti sama dengan `Ry · Rx · Rz`.

Selisih antar pasangan, dihitung dari matriks Godot:

| Urutan Godot | Pasangan | Selisih terhadap pasangan pertama | Artinya |
|---|---|---|---|
| bawaan (YXZ) | yaw = 90°, (pitch, roll) = (20, 10), (15, 5), (10, 0) | 0,0865 dan 0,174 | **tidak terkunci** |
| bawaan (YXZ) | pitch = 90°, (yaw, roll) = (20, 10), (15, 5), (10, 0) | 4,4e-8 dan 3,0e-8 | terkunci |
| ZYX | yaw = 90°, (pitch, roll) = (20, 10), (15, 5), (10, 0) | 4,4e-8 dan 3,0e-8 | terkunci |
| ZYX | pitch = 90°, (yaw, roll) = (20, 10), (15, 5), (10, 0) | 0,0865 dan 0,174 | tidak terkunci |

**T4 terbukti.** Kubus Euler di demo starter mengisi `rotation = (pitch, 90°, roll)` dengan pitch - roll = 10° tetap, meniru `quaternion.py`. Tetapi dengan urutan bawaan Godot, sumbu tengahnya x, bukan y, jadi kubus itu tetap berputar sungguhan, dan tidak memperlihatkan gimbal lock sama sekali. Angka 0,0865 dan 0,174 sama dengan simulasi Python di Fase 3. Perbaikannya saya kerjakan sebagai commit terpisah.

Temuan kecil lain di script yang sama: komentarnya menyebut "two cubes driven by Euler angles ... while a third cube", padahal kodenya hanya membuat satu kubus Euler dan satu kubus quaternion. Ini cocok dengan pemeriksaan Fase 0 (`gimbal_children=2`).

## 4. Perbaikan demo gimbal lock (T4)

Ada dua cara memperbaikinya:

- **(a) Ganti urutan kubus ke ZYX** (`rotation_order = EULER_ORDER_ZYX`), supaya sama dengan `quaternion.py`. Untungnya, demo dan Python memakai angka yang persis sama (yaw = 90°, pitch - roll tetap). Ruginya, demo itu tidak lagi menunjukkan perilaku bawaan Godot. Orang yang memutar node di inspector Godot memakai YXZ, jadi mereka akan terkunci di pitch, bukan di yaw.
- **(b) Pertahankan urutan bawaan Godot (YXZ) dan pindahkan sudut yang dipatok ke sumbu tengahnya**, yaitu pitch = 90°, dengan yaw - roll tetap. Untungnya, demo ini memperlihatkan gimbal lock yang benar-benar akan dialami di Godot. Ruginya, angkanya berbeda dari contoh Python, jadi saat membandingkan saya harus selalu menyebut urutannya.

Saya memilih **(b)**, karena pelajaran utamanya justru bahwa sumbu yang terkunci bergantung pada urutan engine. Konstanta urutannya saya cek dari Godot, bukan ditebak: `rotation_order` bawaan bernilai 2 = `EULER_ORDER_YXZ` (baris `CEK` di atas).

Kubus merah sekarang memakai pitch = 90°, roll = 20° · sin t, dan yaw = roll + 10°. Angka yaw dan roll terus berubah, tapi karena di pitch = 90° hanya yaw - roll yang terlihat, kubus itu **diam total**. Label di bawahnya menampilkan ketiga sudut saat game jalan, supaya terlihat bahwa angkanya bergerak sementara kubusnya tidak. Kubus biru tetap melakukan slerp antara dua orientasi. Komentar starter yang menyebut tiga kubus saya ganti dengan penjelasan yang sesuai kode.

Bukti dari log headless, dibandingkan dengan Python oleh `godot_check.py`:

```
BASIS gimbal_demo order=2 deg=90.0000025044782,9.99999970909292,0.0 m=0.984807730,0.173648179,-0.000000008,...
BASIS gimbal_demo order=2 deg=90.0000025044782,29.949901397264,19.9498999806238 m=0.984807789,0.173648208,-0.000000022,...
GIMBAL euler_cube_max_change=0.000000060 quat_cube_max_change=0.997726381
[ok] Basis YXZ (90, 29.9499, 19.9499) vs euler_to_matrix: selisih 4.03e-08 (toleransi 1e-05)
[ok] kubus Euler diam (6.0e-08), kubus quaternion bergerak (0.998): selisih 0.00e+00 (toleransi 1e-05)
11 baris dibandingkan, 0 di atas toleransinya
```

Pitch terbaca 90,0000025°, bukan tepat 90°, karena sudut disimpan di `Vector3` 32-bit. Python menghitung matriksnya dari angka yang sama persis, jadi perbandingannya tetap adil.

Saya juga mengukur kubus yang sebenarnya saat game berjalan. Di salinan proyek, sebuah script pemeriksa membaca `Basis` kedua kubus dari frame 10 sampai frame 200:

```
f=10   label: Euler YXZ: pitch 90  yaw 12.2  roll 2.2 / yaw - roll = 10.0 -> kubus diam
f=200  label: Euler YXZ: pitch 90  yaw 29.7  roll 19.7 / yaw - roll = 10.0 -> kubus diam
frames 10..200: euler max change=0.000000119 quat max change=0.887561
```

Selama yaw naik dari 12,2° ke 29,7°, `Basis` kubus Euler hanya berubah 1,2e-7, sebesar pembulatan float 32-bit, sedangkan kubus quaternion berubah 0,89. Sebagai pembanding, demo starter dengan urutan yang sama berselisih sampai 0,174 (bagian 3). Bahwa di layar kubus merah memang terlihat diam dan kubus biru terlihat berputar, itu masih harus saya lihat sendiri di editor.

## 5. Scene saya: ruangan, jalur kamera, rig, dan aset (Lab 3 no 1 dan 2)

### Aset

- **Bangunan:** model ruangan patung kuda dari Modul 3, disalin tanpa diubah ke `godot_project/assets/ruangan/mymodel.obj` (SHA-256 sama dengan file di `Module3`). Texture atlas foto saya disimpan ulang sebagai PNG, karena Godot tidak bisa mengimpor PPM, dan isi pixelnya identik. `temple_blockout.gd` dari starter tidak lagi dipasang di scene, tapi file-nya tetap ada sebagai cadangan.
- **Karakter ter-rig:** KayKit Knight karya Kay Lousberg, lisensi CC0, diunduh 30 Oktober 2026 dari repo GitHub resminya. Sumber, commit, ukuran, SHA-256, dan teks lisensinya dicatat di `godot_project/assets/LICENSE.md` dan `assets/kaykit/LICENSE.txt`. Pilihan awal saya adalah Kenney, tapi unduhan Kenney harus lewat tombol di browser, jadi saya memakai KayKit, yang lisensinya sama (CC0) dan bisa diunduh langsung.
- Ukuran total aset sekitar 4 MB, di bawah batas 10 MB yang saya tetapkan (K5).

Editor Godot (mode tanpa jendela) mengimpor ketiga aset tanpa error, lalu membuat file `.import` di samping masing-masing file. File `.import` ikut di-commit karena berisi pengaturan impor. Godot juga mengeluarkan texture yang tertanam di `Knight.glb` menjadi `Knight_knight_texture.png`.

### Susunan scene

Scene `Main.tscn` sekarang terbagi menjadi dua bagian:

- **Ruangan saya di titik nol** (node `Ruangan`): model ruangan dengan lampu di langit-langit, rig lengan saya (`MyArm`), dan Knight yang diperkecil menjadi 0,16 kali (tingginya sekitar 0,4 m, kira-kira setinggi patung) dan memainkan animasi `Idle`. Pack KayKit memasang semua senjata dan perisai pada rig sekaligus, jadi `knight_actor.gd` hanya menampilkan bagian tubuhnya.
- **Area demo dosen** (node `Lab`, 7 m di samping ruangan): lengan FK/IK berukuran 3 dan 2 m, walker stick figure, dan kubus gimbal lock. Ukurannya berskala candi, jadi tidak muat di dalam ruangan 2 × 4 m. Area ini dilihat dengan kamera overview (tombol C).

### Kamera spline di jalur saya

`CameraPath` sekarang memakai `res://data/my_path.json` (salinan `Source/data/my_path.json`; `tests.py` memastikan kedua file sama persis) dan selalu melihat ke tengah patung (-0,2; 0,25; 0). Field of view-nya 55°, sama dengan kamera Modul 3. Jalur saya terbuka (300°), jadi kalau diputar terus, kamera akan meloncat dari P5 kembali ke P0 setiap putaran. Karena itu saya menambah pilihan `ping_pong`: kamera bergerak pergi lalu pulang, dengan `progress_ratio = 0,5 - 0,5 · cos(2π t)`, sehingga melambat dengan halus di kedua ujung. Satu putaran pergi-pulang 16 detik.

Kurva di Godot dibandingkan titik per titik dengan `spline.py`:

```
[ok] kurva my_path.json: 51 titik vs spline.py: selisih 2.72e-16 (toleransi 1e-05)
```

Selisihnya hampir nol karena dengan t = k/10 dan titik kontrol 2 desimal, setiap titik sampel tepat berupa angka desimal dengan paling banyak 5 angka di belakang koma, dan Godot mencetaknya dengan 6 desimal.

Satu hal tentang T8: `Curve3D.add_point` di `spline_camera.gd` tidak diberi handle, jadi kurva Godot berupa 50 garis lurus pendek di antara 51 sampel, bukan kurva Bezier. Dengan jarak antar sampel 3,7 sampai 7,2 cm, tekukan di setiap sambungan sangat kecil. `PathFollow3D.progress_ratio` bergerak menurut panjang busur, jadi kecepatan kamera rata walaupun jarak antar sampelnya tidak sama (grafik di catatan Fase 3).

### Rig lengan saya (Skeleton3D)

`my_arm_rig.gd` membaca `res://data/my_chain.json` dan membangun sebuah `Skeleton3D` dengan empat tulang: lengan atas, lengan bawah, tangan, dan satu tulang ujung jari. Rest setiap tulang adalah "maju sepanjang tulang induk di sumbu x induk", dan pose-nya adalah putaran terhadap sumbu z sebesar sudut lokal dari foto. Artinya posisi global yang dihitung `Skeleton3D` sendiri adalah forward kinematics. Kapsul berwarna dipasang dengan `BoneAttachment3D`. Hasil `get_bone_global_pose()` dicetak dan dibandingkan dengan `fk.py` (dalam meter):

```
[ok] rig lengan saya (Skeleton3D, 4 sendi) vs fk.py: selisih 5.31e-08 (toleransi 1e-05)
```

Jadi FK yang dihitung engine untuk lengan saya sama dengan FK yang saya hitung dengan tangan di Fase 2. Selisih 5e-8 m berasal dari penyimpanan `Vector3` 32-bit.

### Bukti

```
$ $GODOT --headless --editor --path godot_project --quit          # impor aset: kode 0, tanpa error
$ $GODOT --headless --path godot_project --quit-after 60 | .venv/bin/python godot_check.py
...
13 baris dibandingkan, 0 di atas toleransinya
```

Saya juga merender screenshot di salinan proyek (Godot dibuka dengan jendela sebentar, lalu gambar viewport disimpan) dari empat posisi kamera spline dan dari kamera overview. Ruangan bertexture, patung kuda, rig lengan saya, dan Knight terlihat dari jalur kamera, sedangkan area demo terlihat dari kamera overview. Screenshot untuk README saya buat di akhir fase. Kesan saat game dimainkan, yaitu gerak kamera yang halus dan animasi Knight, tetap harus saya lihat sendiri di editor.

## 6. Walker stick figure: posisi kaki yang sebenarnya (T11)

Di Python (Fase 4) celah foot-slide dihitung dari dua rumus jarak. Walker di Godot punya kaki sungguhan yang diayunkan oleh `_pose()`, jadi saya mengukur apakah kaki itu benar-benar diam saat menapak.

### Cara mengukur

`tools/cek_walker.gd` membuat walker sendirian, mematikan `_process` otomatisnya, lalu menjalankannya secara manual 60 langkah per detik selama 4 detik. Di setiap frame, posisi dunia kedua kaki (kotak kaki di ujung tulang kering) dicatat. Kaki dianggap **menapak** sesuai rancangan animasinya sendiri: `_pose()` hanya menekuk lutut saat kaki sedang mengayun (`max(0, cos(fase kaki)) > 0`), jadi kaki yang lututnya lurus adalah kaki yang menapak. Untuk setiap fase menapak dicatat:
- `slide`: geseran horizontal kaki dari awal sampai akhir menapak;
- `rise`: seberapa jauh kaki naik-turun selama menapak;
- `marker_off`: jarak antara posisi kaki sungguhan saat mulai menapak dan penanda footfall yang dihitung script dari rumus `stride_per_cycle × cycle_rate × t`.

Pembuatan node penanda dimatikan selama pengukuran, karena node itu ditambahkan secara tertunda dan meninggalkan peringatan "leaked" saat walker dihapus. Posisi penanda tetap dihitung dengan rumus yang sama.

Versi pertama alat ini memakai definisi "kaki dalam 2 mm dari titik terendahnya", dan hanya menangkap 2 sampai 3 frame per langkah. Dari situlah saya tahu kaki stick figure ternyata naik-turun selama menapak (lihat `rise` di bawah).

### Hasil

```
$ $GODOT --headless --path godot_project --script res://tools/cek_walker.gd
STANCE speed=1.000 foot=0 t0=2.2667 t1=2.7500 x0=2.7189 x1=2.4039 slide=-0.3150 rise=0.0919 marker_x=2.2667 marker_off=0.4522
STANCE speed=1.000 foot=1 t0=2.7667 t1=3.2500 x0=3.2189 x1=2.9039 slide=-0.3150 rise=0.0919 marker_x=2.7667 marker_off=0.4522
WALKER speed=1.000 stances=7 max_abs_slide=0.3296
WALKER speed=1.500 stances=7 max_abs_slide=0.0962
WALKER speed=1.601 stances=7 max_abs_slide=0.0491
```

| Kecepatan root | Asal angkanya | Geseran kaki per langkah (stabil) | Naik-turun kaki | Penanda vs kaki sungguhan |
|---|---|---|---|---|
| 1,0 m/s | "fixed" starter, `stride_per_cycle × cycle_rate` | **-31,5 cm** | 9,2 cm | penanda 45 cm di belakang kaki |
| 1,5 m/s | "buggy" starter | -7,3 cm | 9,2 cm | penanda 1,8 sampai 2,1 m di belakang |
| 1,601 m/s | geometri kaki: 2 langkah × 2 × 0,92 m × sin 0,45 | -2,5 cm | 9,2 cm | penanda 2,1 sampai 2,4 m di belakang |

Langkah pertama tiap kecepatan sedikit berbeda (misalnya -33,0 cm untuk 1,0 m/s), karena gerakan dimulai dari fase nol dan batas fase jatuh di antara dua frame. Tabel di atas memakai langkah yang sudah stabil.

### Yang terbukti

1. **T11 terbukti, dan lebih parah dari dugaan.** Dengan kecepatan yang dianggap "sudah benar" oleh starter (1,0 m/s = `stride_per_cycle × cycle_rate`), kaki yang menapak justru terseret ke belakang 31,5 cm setiap langkah. Itu lebih buruk daripada kecepatan "buggy" 1,5 m/s (7,3 cm). Penyebabnya, `stride_per_cycle = 1,0` hanyalah angka yang ditulis, tidak dihitung dari kaki. Kaki stick figure sepanjang 0,92 m (pinggul ke kotak kaki) yang berayun ±0,45 rad menempuh 2 × 0,92 × sin 0,45 = 0,80 m per langkah, atau 1,60 m per siklus. Perkiraan kasar saya di run awal adalah 1,57 m.
2. **Kecepatan konstan berapa pun tidak bisa membuat kaki diam.** Bahkan di 1,601 m/s kaki masih bergeser 2,5 cm per langkah. Posisi kaki relatif terhadap pinggul adalah 0,92 · sin(0,45 · sin φ), jadi kecepatannya naik-turun di dalam satu langkah, sedangkan root bergerak rata. Ini sama dengan temuan pitfall (c) di Fase 4.
3. **Kaki yang menapak juga tidak menempel di lantai: ia naik-turun 9,2 cm.** Kaki diayunkan dengan lutut lurus, jadi tingginya berubah 0,92 · (1 - cos 0,45) = 9,2 cm, sedangkan pinggul hanya naik-turun 3 cm. Cocok dengan angka terukur 0,0919 m.
4. **Penanda footfall tidak menunjukkan posisi kaki.** Penanda ditaruh di `stride_per_cycle × cycle_rate × t`, padahal kaki menapak di depan pinggul, sejauh 0,06 · cos 0,45 + 0,92 · sin 0,45 = 0,454 m (terukur 0,452). Akibatnya, bahkan di 1,0 m/s penanda berwarna hijau ("tidak sliding"), padahal kakinya terseret 31,5 cm setiap langkah. Warna penanda hanya membandingkan dua rumus, bukan kaki.

Perbaikannya saya buat sebagai commit terpisah: kecepatan root dan tinggi pinggul akan diturunkan dari kaki yang sedang menapak, dan penanda akan ditaruh di posisi kaki yang sebenarnya.

## 7. Perbaikan walker: root motion dari kaki yang menapak

Ada tiga cara memperbaiki temuan T11:
- **Ganti `stride_per_cycle` dengan 1,601 m** (stride dari geometri kaki). Perubahannya paling kecil, tapi menurut pengukuran di atas kaki masih bergeser 2,5 cm per langkah dan tetap naik-turun 9,2 cm.
- **Ubah animasinya** supaya kaki bergerak rata. Hasilnya tidak lagi mirip orang berjalan, dan stride tetap harus ditulis ulang setiap kali animasinya diubah.
- **Root motion:** setiap frame, badan dipindah sejauh kaki yang menapak bergerak mundur relatif terhadap badan di frame itu, lalu badan diangkat atau diturunkan supaya kaki itu tetap di lantai. Ini cara yang sama dengan pitfall (c) di Fase 4: kecepatan dibaca dari animasinya sendiri, bukan diketik.

Saya memilih **root motion**, karena hanya cara ini yang membuat geser dan naik-turun kaki menjadi nol. Cara ini juga tetap benar kalau sudut ayunan atau panjang kaki diubah.

### Yang diubah di `foot_slide_demo.gd`

- `_root_motion_step()`: menentukan kaki yang menapak (yang lututnya lurus di fase baru), menghitung posisi kaki itu di ruang badan sebelum dan sesudah pose diperbarui, lalu menggeser badan sebesar selisih x-nya. Tinggi badan diatur supaya kaki itu berada di ketinggian berdiri awal. Posisi kaki di ruang badan dihitung dengan menyusun transform lokal dari kaki ke atas sampai badan (`_foot_local()`), rantai FK yang sama dengan `fk.py`. Versi pertama saya memakai posisi global, dan itu keliru karena walker berada di dalam node `Lab` yang digeser 7 m.
- Penanda footfall diletakkan di **tempat kaki benar-benar mendarat**, dan berwarna merah kalau kaki itu kemudian bergeser lebih dari 5 cm sebelum terangkat.
- Label di atas walker menampilkan mode dan geser kaki langkah terakhir. Tombol **F** berpindah ke perilaku starter (kecepatan tetap `scripted_speed` dengan penanda dari rumus) dan kembali, supaya bug dan perbaikannya bisa dibandingkan saat dimainkan.
- `show_markers` untuk mematikan penanda saat diukur oleh `tools/cek_walker.gd`.

### Bukti

```
$ $GODOT --headless --path godot_project --script res://tools/cek_walker.gd | .venv/bin/python godot_check.py
[ok] walker kecepatan tetap 1.500 m/s: geser 0.096 m (pembanding, tidak dinilai)
[ok] walker kecepatan tetap 1.000 m/s: geser 0.330 m (pembanding, tidak dinilai)
[ok] walker kecepatan tetap 1.601 m/s: geser 0.049 m (pembanding, tidak dinilai)
[ok] walker root motion: kaki menapak geser 2.4e-07 m, naik-turun 1.8e-07 m
```

| Mode | Geser kaki per langkah (maks) | Naik-turun kaki (maks) |
|---|---|---|
| kecepatan tetap 1,0 m/s (starter "fixed") | 33,0 cm | 9,2 cm |
| kecepatan tetap 1,5 m/s (starter "buggy") | 9,6 cm | 9,2 cm |
| kecepatan tetap 1,601 m/s (stride geometri) | 4,9 cm | 9,2 cm |
| **root motion** | **2,4e-7 m** | **1,8e-7 m** |

Sisa 2e-7 m adalah pembulatan `Vector3` 32-bit pada posisi sejauh sekitar 6 m (jarak antar angka float 32-bit di sekitar 6 adalah 4,8e-7). Di mode root motion, posisi mendarat kaki kiri berurutan 2,3994, 4,0000, dan 5,6007 m, jadi satu siklus menempuh 1,6006 sampai 1,6007 m, sama dengan geometri kaki 4 × 0,92 × sin 0,45 = 1,6007 m. Kecepatan rata-ratanya kini muncul dari kaki sendiri, tidak ditulis di mana pun.

Saya juga menguji walker di scene utama dengan waktu frame yang sungguhan (tidak selalu tepat 1/60 detik), di salinan proyek: selama 400 frame geser terbesar yang tampil di label adalah 4,8e-7 m, dan keenam penanda berwarna hijau. Uji ini sempat menemukan bug di versi pertama saya: geser diukur sampai frame pertama setelah kaki terangkat, saat kaki sudah mulai mengayun, sehingga label menampilkan -1,2 cm. Sekarang geser diukur sampai frame terakhir kaki masih menapak, sama dengan alat ukurnya. Setelah tombol F ditekan, label menampilkan `scripted_speed 1.50 m/s` dan penanda dari rumus starter muncul kembali.

Catatan T14: dengan kecepatan tetap 1,5 m/s, kaki sudah bergeser 7 sampai 10 cm di langkah pertama, yang selesai sebelum 0,75 detik. Jadi bug ini terlihat sejak langkah pertama, jauh sebelum "dua detik" seperti tulisan PDF. Walker diulang setiap 8 detik, sedangkan kamera sekarang bolak-balik dalam 16 detik. Keduanya berjalan sendiri-sendiri, jadi panjang loop tidak memengaruhi hasil di atas.

## 8. Knight berjalan dengan root motion dari animasinya sendiri

Animasi `Walking_A` milik Knight adalah animasi di tempat: kakinya mengayun, tetapi tulang `root` tidak pernah bergerak (track posisi `root` hanya punya satu key). Kalau Knight digeser dengan kecepatan yang diketik, kakinya pasti tergelincir, sama seperti stick figure. Jadi saya memakai cara yang sama dengan bagian 7, kali ini dengan data animasi KayKit.

### Yang diubah di `knight_actor.gd`

- Dengan `walk = true`, AnimationPlayer diatur ke mode manual (`ANIMATION_CALLBACK_MODE_PROCESS_MANUAL`), sehingga animasi hanya maju saat script memanggil `advance(delta)`. Urutan per frame jadi pasti: baca posisi kaki, majukan animasi, baca lagi.
- Kaki yang menapak adalah kaki yang lebih rendah di ruang skeleton (`planted_foot()`). Setiap frame, Knight maju sejauh kaki itu bergerak mundur di sumbu z skeleton (+z adalah arah depan Knight). Perpindahan itu dikalikan `basis` Knight, yang membawa arah hadap dan skala 0,16-nya.
- Knight berjalan bolak-balik di samping patung, dari (0,15; 0; -0,6) ke (0,15; 0; 0,6). Di setiap ujung, Knight berbalik 180° terhadap sumbu y dalam 0,6 detik sambil tetap melangkah di tempat. Putarannya hanya terhadap satu sumbu, jadi tidak ada urutan Euler yang bisa terkunci.

### Bukti

`tools/cek_knight.gd` menjalankan Knight 60 langkah per detik selama 9 detik, di bagian lurus sebelum berbalik. Untuk setiap fase menapak dicatat geseran kaki di lantai (koordinat dunia), juga geseran yang akan terjadi kalau Knight didorong dengan kecepatan tetap sebesar kecepatan rata-ratanya:

```
$ $GODOT --headless --path godot_project --script res://tools/cek_knight.gd
KNIGHT clip=Walking_A length=1.066667 scale=0.16
STANCE foot=foot.r t0=2.6333 t1=3.1333 slide_root_motion=0.000000007 slide_constant_speed=-0.007470 rise=0.007303
STANCE foot=foot.l t0=3.1500 t1=3.6833 slide_root_motion=0.000000000 slide_constant_speed=-0.002498 rise=0.009074
...
KNIGHT_WALK stances=15 travelled=0.926874 avg_speed=0.102986 max_slide_root_motion=0.000000060 max_slide_constant=0.007470 max_rise=0.009074
[ok] Knight root motion: kaki menapak geser 6.0e-08 m (kecepatan tetap: 0.0075 m)
```

| | Root motion | Kecepatan tetap 0,103 m/s |
|---|---|---|
| Geser kaki menapak per langkah | 6e-8 m | 2,5 sampai 7,5 mm (setara 1,6 sampai 4,7 cm kalau Knight seukuran aslinya, karena skalanya 0,16) |

Ada tiga hal yang perlu dicatat:
- Kecepatan rata-ratanya (0,103 m/s, atau 0,110 m per siklus 1,0667 detik) tidak ditulis di mana pun. Angka itu muncul dari kaki di animasinya.
- Kaki yang menapak masih naik 7 sampai 9 mm. Yang diukur adalah tulang `foot` (pergelangan kaki), dan di animasi aslinya pergelangan memang naik saat telapak berguling dari tumit ke jari. Itu gerakan yang dibuat animatornya, bukan tergelincir, jadi tidak saya ubah. Perbaikan saya hanya untuk arah horizontal.
- Saat berbalik di ujung jalur, Knight berputar di tempat sambil melangkah, jadi selama 0,6 detik itu kakinya ikut berputar dan bergeser. Pengukuran di atas hanya untuk bagian jalan lurus.

Uji di scene utama dengan waktu frame sungguhan, di salinan proyek, selama 30 detik: Knight tetap di garis x = 0,15 (simpangan 0), bergerak antara z = -0,616 dan 0,600, dan berbalik tiga kali. Kelebihan 1,6 cm di ujung terjadi karena Knight baru berbalik setelah langkah yang melewati titik tujuan.

## 9. Pengukuran prediksi Euler vs quaternion, dan rekonsiliasinya (Lab 3 no 3)

Prediksinya di-commit lebih dulu (`docs/prediksi/prediksi-euler-rig.md`, commit `dfd6064`). Baru setelah itu saya menulis `tools/cek_euler_rig.gd`. Alat ini memutar bahu rig lengan saya (`bone_0` di `my_arm_rig.gd`) dengan dua cara: lewat `Node3D.rotation` (urutan bawaan Godot, YXZ), lalu `Basis`-nya diambil sebagai quaternion; dan lewat `Quaternion` / `slerp`. Sendi lain tetap memakai sudut dari foto.

```
$ $GODOT --headless --path godot_project --script res://tools/cek_euler_rig.gd
RIG_LOCK pitch=90 yaw_minus_roll_pairs_max_diff=0.000000030 yaw_plus_roll_pair_diff=0.171597 arm_dir_max_abs_y=0.000000060
RIG_B angle_deg=120.000000 get_angle_deg=240.000007
RIG_INTERP t=0.2500 euler_angle=31.716890 slerp_angle=30.000006 between=14.473744
RIG_INTERP t=0.5000 euler_angle=62.799424 slerp_angle=60.000004 between=19.471258
RIG_INTERP t=0.7500 euler_angle=92.527180 slerp_angle=90.000002 between=14.473744
RIG_INTERP t=1.0000 euler_angle=120.000000 slerp_angle=120.000000 between=0.000000
RIG_STEPS frames=120 euler_first_step_speed=127.307773 euler_min=1.058682 euler_max=1.061636 slerp_min=0.999354 slerp_max=1.002482
RIG_PATH euler_path_deg=127.251664 slerp_path_deg=120.089156 net_angle_deg=120.000000
RIG_LIFT dir_b=0.000000,0.000000,1.000000 dir_after=0.000000,-0.173648,0.984808
```

`godot_check.py` mencocokkan setiap baris dengan perhitungan Python yang dibuat terpisah: sudut Euler dihitung dari `euler_to_matrix(90t, 0, 90t, "YXZ")`, sudut slerp dari 120° · t, dan panjang jalur dari rumus 90 · √2. Kedelapan barisnya `[ok]`.

### Rekonsiliasi

| Prediksi | Hasil ukur | Tepat? |
|---|---|---|
| 1(a) di pitch 90°, arah lengan selalu mendatar (y = 0) | y terbesar 6,0e-8 dari enam pasangan (yaw, roll) | tepat |
| 1(b) pasangan yaw - roll tetap memberi posisi sama, yaw + roll tetap berbeda | 3,0e-8 m vs 0,172 m | tepat |
| 2 sudut B = 120° | 120,000000° | tepat |
| 2 slerp naik rata 120° · t, langkah per frame sama | 30,000, 60,000, 90,000, 120,000°; langkah 0,9994 sampai 1,0025° | tepat (lihat catatan float di bawah) |
| 2 Euler di t = 0,5 adalah 62,8° | 62,7994° | tepat |
| 2 Euler di awal 127,3° per durasi | 127,31° per durasi | tepat |
| 2 Euler pasti melambat di akhir, rasio langkah jauh di atas 1 | langkah 1,0587 sampai 1,0616°, hampir rata | **meleset** |
| 2 jalur Euler dan slerp berbeda di tengah (sudut antara keduanya > 0) | 19,47° di t = 0,5 | tepat |
| 3 dari B, putaran quaternion 10° mengubah y arah lengan sebesar ±0,174 | y = -0,173648 | tepat |

**Bagian yang meleset dan kenapa.** Saya menganggap total yang ditempuh Euler sama dengan sudut bersihnya, 120°. Karena gerakan awalnya lebih cepat dari slerp, saya menyimpulkan geraknya pasti melambat di akhir. Ternyata asumsi itu salah. Jalur Euler bukan jalur terpendek, jadi panjang jalurnya lebih dari sudut bersihnya. Kecepatan sudut `Rx(a) · Rz(a)` adalah besarnya `ex · ȧ + Rx(a) ez · ȧ`, yaitu |(1, 0, 0) + (0, -sin a, cos a)| · ȧ = √2 · ȧ, **konstan**. Artinya blend Euler ini bergerak rata di 127,3° per durasi, dan menempuh 90 · √2 = 127,28° untuk mencapai orientasi yang hanya berjarak 120°. Python mengonfirmasinya: dengan 100.000 langkah, panjang jalur Euler 127,2792°, dan Godot mengukur 127,25°. Jadi masalah blend Euler di sini bukan kecepatannya yang naik-turun, melainkan **jalurnya yang memutar 6% lebih jauh dan menyimpang sampai 19,5° dari jalur terpendek**. Prediksi saya tentang sudut di t = 0,5 dan kecepatan awal tetap tepat, karena keduanya diturunkan langsung dari rumus θ(t), bukan dari asumsi tadi.

**Catatan float.** Langkah slerp tidak tepat 1,0000° tetapi 0,9994 sampai 1,0025°, dan total jalurnya 120,09°, bukan 120°. Godot menyimpan quaternion dalam float 32-bit, dan sudut kecil dibaca kembali dengan `acos(w)` di dekat w = 1. Di daerah itu, galat pembulatan 6e-8 pada w menjadi sekitar 3e-4 rad (0,02°) pada sudut. Karena itu sudut tunggal dibandingkan dengan toleransi 0,01° dan jumlah 120 langkah dengan 0,2°. Sebagai pembanding, `slerp()` Python saya (float 64-bit) untuk A ke B yang sama memberi langkah 0,999999999997 sampai 1,000000000004° (selebar 7e-12°) dengan cara baca `acos` yang sama.

**Temuan kecil di Godot.** `Quaternion.get_angle()` untuk B mengembalikan 240°, bukan 120°. Fungsi itu menghitung 2 · acos(w) tanpa memilih jalan terpendek, padahal q dan -q adalah putaran yang sama. Saya memakai 2 · acos(|w|). Di Python, `slerp()` saya sudah membalik tanda quaternion untuk alasan yang sama.

### Keputusan representasi rotasi (LO8)

Untuk sendi rig yang berputar bebas, seperti bahu, saya memakai **quaternion**, dan angka di atas alasannya:
1. Dengan Euler YXZ, di pitch 90° satu arah putaran hilang. Lengan tidak bisa diangkat dengan yaw atau roll (y tetap 0 sampai 6e-8), padahal dengan quaternion lengan langsung terangkat 0,174 dari orientasi yang sama.
2. Interpolasi Euler menempuh jalur 6% lebih panjang dan menyimpang sampai 19,5° dari jalur terpendek, sedangkan slerp tepat di jalur terpendek dengan kecepatan sudut rata.

Euler tetap berguna sebagai angka yang mudah dibaca manusia di inspector, asalkan tidak dipakai untuk interpolasi atau untuk sendi yang bisa mencapai sumbu tengahnya.

## 10. Renderer Compatibility (K15)

Dokumentasi resmi Godot menulis "Godot 4 can only target WebGL 2.0 (using the Compatibility rendering method)", sedangkan starter memakai `rendering_method="mobile"` dengan fitur "Forward Plus" (T9). Jadi sebelum ekspor Web, `project.godot` saya ubah:

- `renderer/rendering_method="gl_compatibility"` (ditambah `rendering_method.mobile` dengan nilai yang sama), dan `config/features` menjadi `"4.7", "GL Compatibility"`;
- `config/name` dan `config/description` disesuaikan dengan isi proyek sekarang, yaitu ruangan patung kuda, bukan lagi candi Pusaka3D.

Bukti bahwa versi desktop tetap jalan:
- editor (mode tanpa jendela) membuka proyek dengan kode keluar 0 tanpa error, dan tidak menulis ulang `project.godot`;
- dijalankan dengan jendela di salinan proyek, Godot mencetak `OpenGL API 4.1 Metal - 91.7 - Compatibility - Using Device: Apple - Apple M5`, dan `RenderingServer` melaporkan `gl_compatibility` dengan driver `opengl3`;
- screenshot dari dua posisi kamera spline dan dari kamera overview menunjukkan ruangan bertexture, patung, rig lengan, Knight, dan area demo seperti sebelumnya. Penanda footfall root motion di area demo semuanya hijau;
- `godot_check.py` tetap `13 baris dibandingkan, 0 di atas toleransinya` untuk scene utama.

Rencana awal memisahkan perubahan renderer ke commit sendiri. Atas permintaan, perubahan ini digabung dengan pengukuran dan ekspor dalam satu commit, jadi buktinya saya tulis di sini.

## 11. Ekspor Web, ukuran, dan hosting (Lab 3 no 4)

### Export template

Export template resmi Godot 4.7.2 (`Godot_v4.7.2-stable_export_templates.tpz`, 1.281.349.702 byte) saya unduh dari halaman rilis GitHub `godotengine/godot`. SHA-256-nya, `f298490b8d44d934be425a5a65a51bf15f422428b229a06a6e11d9ffea248011`, sama dengan angka yang tercantum di rilis itu. Dari paket itu saya hanya memasang yang dibutuhkan untuk Web tanpa thread (`version.txt`, `web_nothreads_release.zip`, `web_nothreads_debug.zip`, masing-masing sekitar 10 MB) ke `~/Library/Application Support/Godot/export_templates/4.7.2.stable/`, di luar repo.

### Preset dan ekspor

`godot_project/export_presets.cfg` berisi satu preset **Web**:
- `variant/thread_support=false`, supaya build tidak butuh header `Cross-Origin-Opener-Policy` dan `Cross-Origin-Embedder-Policy` yang belum tentu dikirim GitHub Pages (K16);
- `include_filter="*.json"`, supaya `my_path.json`, `my_chain.json`, dan `camera_path.json` ikut terbawa. Godot tidak membawa file non-resource kecuali diminta;
- `exclude_filter="tools/*"`, supaya script pemeriksa saya tidak ikut ke build;
- tujuan `../../build/web/index.html`, yaitu `Module4/build/web/`.

```
$ $GODOT --headless --path godot_project --export-release "Web" ../../build/web/index.html     # kode keluar 0
```

| File | Ukuran |
|---|---|
| `index.wasm` (engine Godot) | 39.514.754 B |
| `index.pck` (scene, script, aset, JSON) | 1.566.920 B |
| `index.js` | 279.815 B |
| lainnya (html, ikon, audio worklet) | 54.816 B |
| **total** | **sekitar 40 MB** |

Isi game sendiri hanya 1,6 MB. Sisanya adalah engine, yang ukurannya sama untuk proyek Godot apa pun. Saya mengecek isi `index.pck`: ketiga file JSON ada, dan tidak ada satu pun file dari `tools/`. Ekspor kedua ke folder lain menghasilkan kesembilan file yang **identik byte per byte** dengan ekspor pertama. Catatan dari Fase 6: ini berlaku selama cache impor `.godot/` sama. Setelah impor dari nol (misalnya di clone), hasil impor `Knight.glb` dan `Main.scn` berbeda beberapa puluh byte, kemungkinan besar karena id acak sub-resource. `index.wasm` tetap identik, jadi build ulang paling banyak menambah sekitar 1,6 MB (`index.pck`).

### Uji di server lokal

```
.venv/bin/python -m http.server 8000 --bind 127.0.0.1 -d ../build/web
```

`lsof` menunjukkan `TCP 127.0.0.1:8000 (LISTEN)`, jadi server hanya bisa dibuka dari laptop ini. `curl` mendapat kode 200 untuk keempat file utama, dan `index.wasm` dikirim sebagai `application/wasm`.

Lalu build saya buka dengan Google Chrome 156 tanpa jendela, dikendalikan lewat Chrome DevTools Protocol dari sebuah script Node sementara di luar repo. Script itu menunggu 50 detik, mencatat semua pesan console, dan mengambil screenshot:
- WebGL: `WebGL 2.0 (OpenGL ES 3.0 Chromium)`, `ANGLE (Apple, ANGLE Metal Renderer: Apple M5)`;
- Godot mencetak `Compatibility - Using Device: WebKit - WebKit WebGL` dan `single-threaded, no GDExtension support`;
- tidak ada exception atau error di console;
- baris pengecekan yang dicetak game di console browser (`CURVE`, `ARM_*`, `BASIS`, `GIMBAL`, `MYARM`) saya alirkan ke `godot_check.py`, hasilnya `13 baris dibandingkan, 0 di atas toleransinya`. Jadi di browser pun angkanya sama dengan Python;
- screenshot setelah 50 detik memperlihatkan ruangan bertexture, patung kuda, rig lengan saya, dan Knight dari kamera spline.

Uji dengan browser yang saya buka sendiri dicatat terpisah, beserta nama dan versi browsernya.

### Hosting (K16)

Dari empat pilihan (GitHub Pages dari `main`, branch terpisah, itch.io, atau tanpa Web), saya memilih **GitHub Pages dari `main`**, sama dengan Modul 3 yang sudah memakai Pages di repo ini. Untungnya: paling sederhana, dan penilai cukup membuka satu link. Ruginya: repo bertambah sekitar 40 MB. Build ulang dengan cache impor yang sama menghasilkan file yang identik, dan `index.wasm` (39,5 MB) selalu identik, jadi build ulang paling banyak menambah sekitar 1,6 MB. Baris `Module4/build/` di `.gitignore` root saya buang supaya `Module4/build/web/` ikut ter-commit. Repo sudah punya `.nojekyll`, dan semua file build tidak diawali garis bawah, jadi Jekyll tidak akan membuang apa pun. Ukuran file terbesar (39,5 MB) masih di bawah batas 100 MB per file GitHub.

Link yang diharapkan setelah push: `https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module4/build/web/`. Link ini baru saya uji setelah di-push.

## 12. Refleksi: apa yang diambil alih engine, dan apa yang tetap harus saya pikirkan (Lab 3 no 6)

Godot mengambil alih banyak pekerjaan yang di Python saya tulis sendiri. `Skeleton3D` menyusun pose lokal setiap tulang menjadi pose global, jadi FK lengan saya cukup diisi panjang dan sudut, dan hasilnya sama dengan `fk.py` sampai 5e-8 m. `Basis` dan `Quaternion` menangani perkalian dan `slerp`. `Curve3D` dan `PathFollow3D` menyimpan jalur dan menggerakkan kamera menurut panjang busur. `AnimationPlayer` memutar 76 klip Knight, dan game loop memanggil semuanya setiap frame. Saya tidak perlu menulis perkalian matriks atau rumus slerp lagi.

Tapi setiap kesalahan yang saya temukan di Fase 5 bukan kesalahan engine. Semuanya kesalahan keputusan yang tetap harus dipikirkan manusia:

- **Urutan dan sumbu yang terkunci.** Demo gimbal starter menyalin angka Python (yaw 90°) ke Godot, padahal Godot memakai YXZ dengan sumbu tengah x. Engine menghitung `Basis` dengan benar, tapi kubusnya tidak terkunci sama sekali (selisih 0,174, T4). Sumbu mana yang terkunci harus diturunkan dari urutannya, bukan ditebak dari nama "yaw".
- **Representasi.** Godot menyediakan Euler di inspector dan quaternion di kode. Engine tidak memilihkan. Pengukuran di bagian 9 menunjukkan Euler kehilangan satu arah putaran di pitch 90°, dan jalur interpolasinya 6% lebih panjang. Keputusan memakai quaternion untuk sendi bebas tetap keputusan saya.
- **Sinkron langkah dan kecepatan.** Engine tidak tahu bahwa `stride_per_cycle = 1,0` adalah angka yang salah. Walker starter terseret 31,5 cm per langkah justru di kecepatan yang dianggap benar (T11), dan Knight akan tergelincir kalau didorong dengan kecepatan tetap. Root motion dari kaki yang menapak harus saya rancang dan ukur sendiri.
- **Konvensi lokal dan global, dan jenis angka.** Posisi kaki walker harus dihitung di ruang badan, bukan dari posisi global, karena walker berada di dalam node lain yang digeser. Engine juga menyimpan `Vector2`, `Vector3`, dan `Basis` dalam float 32-bit, jadi angka Godot berbeda dengan Python sampai 1e-7 kecuali hitungannya dibuat dengan float 64-bit. `Quaternion.get_angle()` pun mengembalikan 240° untuk putaran 120°.
- **Jalur kamera (T8).** `Curve3D` dari sampel tanpa handle hanyalah garis-garis lurus pendek, dan jalur saya terbuka, jadi saya sendiri yang harus memilih kamera bolak-balik supaya tidak meloncat.

Kesimpulan saya: engine menghemat pekerjaan menghitung, tetapi tidak menghemat pekerjaan memutuskan. Bagian yang paling sering salah justru bagian yang tampak "sudah diurus engine", dan satu-satunya cara saya menemukannya adalah mencetak angka dari Godot lalu membandingkannya dengan Python.
