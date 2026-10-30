# Laporan Modul 4: Animasi, Kinematika & Game Engine

Zacky Maulana (NIM 20241337034), S1 Informatika UMSurabaya
Praktikum Grafika Komputer

Subjek saya sama dengan Modul 1 sampai 3, yaitu patung kuda milik saya. Bangunannya adalah ruangan tempat patung itu berdiri, dari model Modul 3. Semua angka di laporan ini adalah keluaran program yang benar-benar saya jalankan. Perintah dan transkrip lengkapnya ada di `docs/catatan/`.

**Toolchain (Lab 1 no 1).** Mac17,2 (Apple M5), macOS 27.0.1 (26A434), Python 3.11.8 di `Module4/Source/.venv`, matplotlib 3.11.2 (hanya untuk gambar), Godot 4.7.2 stable (`4.7.2.stable.official.ed1daf0bf`), renderer Compatibility. Dicatat 30 Oktober 2026. Di repo ini, folder `code/Module4/` dari modul adalah `Module4/Source/`.

---

## 1. Rantai saya dan FK dengan tangan (A1)

Rantainya adalah lengan saya: bahu, siku, pergelangan, dan ujung jari tengah. Panjangnya 29, 24, dan 20 cm. Sudut lokal satu pose saya baca dari foto samping IMG_9035 dengan `atan2` dari koordinat pixel titik sendi: **-2,6°, 83,4°, dan 26,5°**. Ketelitiannya sekitar ±4°, karena tangan di foto 8,3% lebih pendek dari ukuran aslinya, tanda bahwa tangan agak miring terhadap kamera. Data dan titik pixelnya ada di `Source/data/my_chain.json`. Foto yang masuk repo hanya potongan lengan tanpa wajah dan tanpa EXIF, karena foto aslinya menyimpan lokasi GPS.

FK dengan tangan untuk satu sendi, yaitu pergelangan (sudut global 80,8° = -2,6° + 83,4°):

```
siku        = (29 · cos(-2,6°) ; 29 · sin(-2,6°)) = (28,970 ; -1,316)
pergelangan = siku + (24 · cos 80,8° ; 24 · sin 80,8°) = (28,970 + 3,837 ; -1,316 + 23,691) = (32,807 ; 22,376)
ujung jari  = pergelangan + (20 · cos 107,3° ; 20 · sin 107,3°) = (26,860 ; 41,471)
```

| Sendi | Tangan (cm) | `fk.py` lewat `my_chain.py` (cm) |
|---|---|---|
| siku | (28,970; -1,316) | (28.970, -1.316) |
| pergelangan | (32,807; 22,376) | (32.807, 22.376) |
| ujung jari tengah | (26,860; 41,471) | (26.860, 41.471) |

Semuanya cocok sampai 3 desimal. `tests.py` menguji ketiganya, dan saya membuktikan test itu bisa gagal: dengan sudut siku 83,5° test langsung `FAIL`.

## 2. Primitif from-scratch dan cross-check (A2)

`fk.py`, `ik.py`, `spline.py`, dan `quaternion.py` saya tulis ulang: FK sebagai perkalian matriks lokal, Catmull-Rom sebagai bobot basis, dan quaternion dengan perkalian, normalisasi, serta Euler dengan urutan sebagai parameter. Pada 2000 input acak per fungsi, hasilnya sama dengan kode starter sampai 1,2e-13. Keempatnya hanya memakai standard library, dan `test_stdlib_only` membuktikannya dengan membaca import tiap file lewat modul `ast` (test itu terbukti gagal kalau `import numpy` disisipkan).

**Contoh E1 sampai E4, angkanya:**

| Contoh | Hasil `tests.py` |
|---|---|
| E1 FK | siku (2,598; 1,500) sudut global 30°, tangan (2,598; 3,500) sudut global 90° |
| E2 IK | θ1 = -13,18°, θ2 = 70,53°, error verifikasi FK 4,44e-16 (di bawah 1e-9) |
| E3 Catmull-Rom | q(0,5) = (3,0; 1,0); `camera_path.json` 5 titik menjadi 41 sampel |
| E4 slerp | (0,9511; 0; 0,3090; 0), sudut 36,00° |

Test tambahan: batas jangkauan dalam dan luar sama-sama melempar `UnreachableTarget`, dan error IK lalu FK di bawah 1e-9 untuk 20.000 target acak, termasuk yang mepet batas. Test acak ini sempat menemukan kesalahan di versi pertama saya. Sudut bahu yang dihitung dengan aturan cosinus juga meleset sampai 1,4e-7 saat lengan hampir lurus. Setelah sudut bahu dihitung dari θ2 yang sebenarnya dipakai (bentuk atan2), errornya turun ke 1,4e-12. Total test sekarang `ALL CHECKS PASSED (134 ok)`.

**Rantai 3-bone saya** adalah tabel di bagian 1, dan IK lengan saya mengembalikan tepat sudut foto. Dengan target pergelangan (32,807; 22,376) cm, `solve_two_bone_ik(29, 24, ...)` memberi θ1 = -2,60° dan θ2 = 83,40°, dengan error FK 7,1e-15 cm.

**Jalur kamera saya:** 6 titik di lingkaran 0,6 m di sekitar patung pada tinggi 1,15 m, menjadi 51 sampel. Setiap sampel ke-10 tepat di titik kontrol, dan jarak terdekat ke dinding atau lemari 0,215 m. Jarak antar sampel 3,7 sampai 7,2 cm, jadi langkah t yang sama besar tidak berarti jarak tempuh yang sama (T8).

**Urutan Euler alternatif.** Untuk `Rx · Rz · Ry` saya menurunkan dengan tangan, sebelum cek numerik, bahwa yang terkunci adalah roll (sumbu tengah): `Rz(90°)` mengirim sumbu y ke -x, sehingga `M(roll = 90°) = Rx(pitch - yaw) · Rz(90°)`.

| Urutan | Pasangan | Selisih matriks maks |
|---|---|---|
| Rx Rz Ry, roll = 90°, pitch - yaw tetap | (20, 10), (15, 5), (10, 0) | 1,11e-16 dan 1,06e-17: **terkunci** |
| Rx Rz Ry, yaw = 90°, pitch - roll tetap | sama | 0,0865 dan 0,174: **yaw tidak terkunci** |
| Rz Ry Rx (urutan awal), yaw = 90°, pitch - roll tetap | sama | 1,11e-16 dan 1,06e-17: terkunci di yaw |

Jadi sumbu yang terkunci selalu sumbu tengah urutan yang dipakai, bukan yaw.

## 3. Diagnosis dan perbaikan foot-slide (A3)

**Diagnosis (di-commit sebelum perbaikan, `docs/prediksi/diagnosis-foot-slide.md`).** Dari `foot_slide_bug.py --diagnose` saja: celahnya bertambah 0,250 m setiap 0,5 detik, jadi tumbuh lurus 0,5 m/s. Berarti yang salah adalah kecepatan, bukan posisi awal. Root maju 1,5 m/s (`scripted_speed`), sedangkan langkah kaki menutup `STRIDE_PER_CYCLE × CYCLE_RATE` = 1,0 m/s. Rumusnya:

```
gap(t) = (scripted_speed - STRIDE_PER_CYCLE × CYCLE_RATE) · t        kecepatan benar: scripted_speed = STRIDE_PER_CYCLE × CYCLE_RATE
```

Ini pitfall §12.5: nilai yang menggerakkan gerakan ditetapkan terpisah dari nilai yang sudah tersimpan di animasi, dan tidak ada yang memaksa keduanya sama.

**Satu perubahan:** `scripted_speed` diganti `matched_speed() = stride × rate`.

| t (s) | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| celah sebelum (m) | 0,000 | 0,500 | 1,000 | 1,500 | 2,000 | 2,500 |
| celah sesudah (m) | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |

Celah sesudahnya **tepat 0,0** (dicek dengan `== 0.0`) di 11, 51, dan 301 sampel, dan juga untuk 1000 klip acak, karena kedua jarak dihitung dengan perkalian float yang sama persis. Test foot-slide sekarang menghitung kecepatan benar dari konstanta, bukan dari angka 1,0 yang ditulis mati (T6).

**Perbaikan pitfall (c):** kecepatan dibaca dari kurva root motion yang di-bake (dibayangkan: kaki lambat saat menapak, cepat di tengah langkah, 30 keyframe per siklus). Saat panjang langkah turun dari 1,0 m ke 0,8 m di t = 2,5 s, kecepatan tetap 1,0 m/s menghasilkan celah 50 cm di detik ke-5, sedangkan kurva menjaga celah di 1,2e-14 m, sisa pembulatan dari menjumlahkan 300 frame. Temuan tambahan: kecepatan tetap yang "benar" pun membuat kaki maju-mundur 4,75 cm di dalam setiap langkah. Tabel per 0,5 detik menyembunyikannya, karena sampelnya jatuh tepat di tengah dan akhir siklus.

## 4. Scene Godot dan keputusan Euler vs quaternion (A4)

### Scene

- **Bangunan:** ruangan patung kuda dari Modul 3 (`mymodel.obj` disalin tanpa diubah; texture foto saya sebagai PNG).
- **Kamera spline:** jalur saya, selalu melihat ke patung, bolak-balik dengan perlambatan cosinus karena jalurnya terbuka. Kurva Godot sama dengan `spline.py` sampai 3e-16.
- **Rig:** lengan saya sebagai `Skeleton3D` dari `my_chain.json`, yang pose globalnya sama dengan `fk.py` sampai 5e-8 m; dan **KayKit Knight** (Kay Lousberg, CC0, diunduh 30 Oktober 2026 dari GitHub resminya; sumber, commit, ukuran, dan SHA-256 di `assets/LICENSE.md`) yang berjalan bolak-balik di samping patung.
- **Demo dosen:** lengan FK/IK, walker, dan kubus gimbal, dipindah 7 m ke samping ruangan.

`godot_project/` diimpor dan dijalankan tanpa error atau missing-script, dan tidak ada file starter yang ditulis ulang editor. **Toggle FK/IK** (Space, U) mereproduksi angka Python: siku (2,598076211353; 1,500000000000), θ1 = -13,178679239300°, θ2 = 70,528779365509°, selisih 3e-13 dari `fk.py`/`ik.py`. Target (5,5; 0) ditandai merah "di luar jangkauan" dan tidak di-clamp diam-diam (T5). Selisih awal 6,3e-6° sempat muncul karena `Vector2` di Godot 32-bit, lalu hilang setelah hitungannya dibuat dengan float 64-bit.

**Demo gimbal lock.** Godot memakai intrinsic YXZ (`rotation_order` bawaan = 2 = `EULER_ORDER_YXZ`). `Basis` yang dicetak Godot cocok dengan `euler_to_matrix(..., "YXZ")` sampai 7,6e-8. Demo starter mematok yaw 90° dan ternyata tidak terkunci (selisih 0,0865 dan 0,174, T4). Setelah diperbaiki dengan pitch 90° dan yaw - roll tetap, kubus Euler hanya bergerak 1,2e-7 dari frame 10 sampai 200, padahal yaw naik dari 12° ke 30°, sedangkan kubus quaternion bergerak 0,89.

**Walker (T11).** Diukur di Godot, walker starter terseret **31,5 cm per langkah** justru di kecepatan "benar" 1,0 m/s, karena kakinya menempuh 1,60 m per siklus, bukan 1,0. Kaki yang menapak naik-turun 9,2 cm, dan penanda footfall jatuh 45 cm di belakang kaki yang sebenarnya, tapi tetap hijau. Dengan root motion dari kaki yang menapak, gesernya 2,4e-7 m dan naik-turunnya 1,8e-7 m. Knight memakai cara yang sama dari animasi `Walking_A` miliknya: geser 6e-8 m, sedangkan kecepatan tetap akan tergelincir sampai 7,5 mm per langkah.

### Prediksi, pengukuran, rekonsiliasi

Prediksi (di-commit sebelum diukur, `docs/prediksi/prediksi-euler-rig.md`) untuk bahu rig lengan saya dengan Euler YXZ Godot:
1. di pitch 90° lengan hanya bisa mengarah mendatar, karena `Ry(yaw) Rx(90°) Rz(roll) = Ry(yaw - roll) Rx(90°)`;
2. dari A = (0, 0, 0) ke B = (90°, 0, 90°), yaitu putaran 120°, slerp naik rata, sedangkan blend Euler mencapai 62,8° di t = 0,5, kecepatan awalnya 127,3° per durasi, lalu melambat di akhir;
3. dari B, quaternion bisa mengangkat lengan sebesar ±0,174.

| Prediksi | Terukur di Godot | |
|---|---|---|
| y arah lengan di pitch 90° = 0 | 6,0e-8 (6 pasangan yaw, roll) | tepat |
| pasangan yaw - roll tetap memberi posisi sama | 3,0e-8 m (yaw + roll: 0,172 m) | tepat |
| Euler 62,8° di t = 0,5, kecepatan awal 127,3 | 62,7994°, 127,31 | tepat |
| slerp 60° di t = 0,5, langkah rata | 60,000°, langkah 0,9994 sampai 1,0025° (float 32-bit) | tepat |
| Euler melambat di akhir | langkah 1,0587 sampai 1,0616°, hampir rata | **meleset** |
| quaternion mengangkat lengan ±0,174 | y = -0,173648 | tepat |

**Kenapa meleset:** saya menganggap panjang jalur Euler sama dengan sudut bersihnya (120°). Ternyata kecepatan sudut `Rx(a) Rz(a)` adalah |(1, 0, 0) + (0, -sin a, cos a)| · ȧ = √2 · ȧ, konstan. Jadi blend Euler bergerak rata tetapi menempuh 90√2 = 127,28°, 6% lebih jauh, dan menyimpang sampai 19,5° dari jalur terpendek di t = 0,5. **Keputusan:** sendi bebas seperti bahu memakai quaternion, karena Euler kehilangan satu arah putaran di pitch 90° dan interpolasinya tidak menempuh jalur terpendek. Euler hanya untuk angka di inspector.

### Keterbatasan

- Kalau rantainya 5 bone, misalnya lengan sampai ruas jari, IK aturan cosinus tidak lagi cukup. Rig ini perlu solver iteratif seperti FABRIK di `SkeletonIK3D`/`SkeletonModifier3D`, dengan pole (magnet) untuk memilih arah tekukan.
- Kalau kamera harus berakselerasi mulus (misalnya untuk rekaman sinematik), Catmull-Rom hanya menjamin C1. Percepatannya melompat di titik kontrol, jadi butuh spline C2 seperti B-spline kubik.
- Jalur saya terbuka (300°). Untuk satu putaran penuh tanpa bolak-balik dibutuhkan Catmull-Rom tertutup.
- Sudut pose dibaca dari satu foto 2D (±4°). Rig 3D yang akurat butuh dua sudut pandang atau motion capture.
- Saat Knight berbalik di ujung jalur, kakinya ikut berputar dan bergeser. Root motion saya hanya untuk berjalan lurus.

## 5. Reproducibility (A5)

**Build:** https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module4/build/web/ (Web, Godot 4.7.2, renderer Compatibility, tanpa thread, 40 MB, di mana 39,5 MB adalah engine). Di server lokal `127.0.0.1:8000` dan di link Pages, Chrome 156 tanpa jendela tidak mencatat error, dan 13 baris angka dari console browser cocok dengan Python. File yang disajikan Pages identik dengan file di repo. Saya juga membukanya sendiri di Safari 27.0.1.

**Clone bersih** dari GitHub (commit `418d846`), di Mac yang sama:

```
pip install -r requirements.txt        # pip freeze sama persis dengan requirements.txt
python tests.py                        # ALL CHECKS PASSED (134 ok)
$GODOT --headless --editor --path godot_project --quit         # impor: kode 0, 0 error
$GODOT --headless --path godot_project --quit-after 300        # kode 0, 0 error / missing script
  | python godot_check.py              # 13 baris dibandingkan, 0 di atas toleransinya
git status --short                     # kosong
```

Versi Godot: 4.7.2 stable. Satu temuan dari uji ini: ekspor Web dari impor baru tidak identik byte per byte dengan build yang di-commit. Hasil impor `Knight.glb` dan `Main.scn` berbeda beberapa puluh byte, kemungkinan karena id acak sub-resource, sedangkan perilakunya sama. Transkrip lengkapnya ada di `docs/catatan/fase6-reproduksi.md`.

**Persiapan viva:** `docs/catatan/persiapan-viva.md`.
