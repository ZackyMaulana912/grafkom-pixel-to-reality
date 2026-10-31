# Extension Lab: FABRIK, IK iteratif untuk rantai lebih dari dua bone

Modul menawarkan Extension Lab (tidak dinilai): "Baca cara kerja sebuah solver IK iteratif untuk sebuah rantai > 2 bone; implementasikan sebuah versi minimal dan bandingkan konvergensinya dengan kasus 2-bone analitik." Saya mengerjakannya karena berkaitan langsung dengan pertanyaan viva "apa yang berubah kalau rantai ini punya lima bone?" dan dengan keterbatasan pertama di laporan saya. Dikerjakan 31 Oktober 2026.

## Cara kerja

`Source/fabrik.py` (standard library saja, ikut dicek `test_stdlib_only`) bekerja dengan **posisi sendi**, bukan sudut. Satu iterasi terdiri dari dua langkah:

1. **Mundur:** ujung rantai diletakkan tepat di target. Lalu dari ujung ke pangkal, setiap sendi ditarik ke arah sendi berikutnya sampai jaraknya kembali sama dengan panjang tulangnya.
2. **Maju:** pangkal dikembalikan ke bahu. Lalu dari pangkal ke ujung dilakukan hal yang sama.

Kedua langkah diulang sampai jarak ujung ke target di bawah 1e-9. Setelah itu sudut lokal dibaca dari posisi sendi dengan `atan2`, dengan konvensi yang sama seperti `fk.py`, sehingga hasilnya bisa langsung dicek ulang lewat FK. Target yang lebih jauh dari panjang total rantai **tidak dipaksa diam-diam**: rantai diluruskan ke arah target dan hasilnya ditandai `reached = False`, sama prinsipnya dengan `UnreachableTarget` di `ik.py`.

Nama dan gagasan FABRIK saya ambil dari dokumentasi Godot 4.7 `SkeletonIK3D` ("uses FabrikInverseKinematic internally"). Makalah aslinya belum saya baca. Implementasi di atas saya tulis dari penjelasan dua langkah tersebut.

## Hasil

```
$ .venv/bin/python fabrik.py
modul arm (3, 2) -> (4, 1), start straight: theta -13.1787 / 70.5288 deg, 10 iterations, error 7.24e-10
  analytic solutions: (-13.1787, 70.5288) and (41.2512, -70.5288)
my arm -> fingertip (26.860, 41.471) cm from straight: 3.83, 65.72, 51.99 deg, 8 iterations, FK error 7.61e-10 cm
my arm -> fingertip (26.860, 41.471) cm from photo pose: -2.60, 83.40, 26.50 deg, 0 iterations, FK error 3.55e-15 cm
my arm -> fingertip (26.860, 41.471) cm from elbow bent the other way: -2.45, 82.88, 27.34 deg, 6 iterations, FK error 7.72e-11 cm
my arm -> (80, 0) cm, beyond 73 cm reach: reached=False, stretched at 0.0 deg, short by 7.0 cm
```

![Konvergensi FABRIK dan dua pose lengan saya](../img/fabrik.png)

### Dibanding IK analitik (2 bone)

Untuk lengan modul (3 dan 2) ke target (4, 1), FABRIK yang dimulai dari lengan lurus mendarat di solusi analitik θ2 ≥ 0: θ1 = -13,178679° dan θ2 = 70,528779°, berselisih 1,5e-8° dan 2,2e-8° dari `ik.py`, setelah **10 iterasi**. IK analitik hanya butuh satu kali hitung, dengan error 4,4e-16. Errornya turun sekitar 9 kali setiap iterasi (rasio 0,111 setelah iterasi ke-4). Ini konvergensi **linear**: setiap tambahan satu digit ketelitian butuh sekitar satu iterasi lagi.

### Lengan 3-bone saya: banyak jawaban

Target yang sama, yaitu ujung jari tengah saya di (26,860; 41,471) cm, dicapai dengan tiga pose berbeda, tergantung pose awalnya:
- dari lengan lurus: (3,8°; 65,7°; 52,0°), 8 iterasi;
- dari pose foto: tetap pose foto (-2,6°; 83,4°; 26,5°), 0 iterasi;
- dari siku yang ditekuk ke arah sebaliknya: (-2,45°; 82,88°; 27,34°), 6 iterasi.

Ketiganya menyentuh titik yang sama (error FK di bawah 1e-9 cm). Ini yang dimaksud jawaban di persiapan viva: dengan tiga sudut tetapi hanya dua persamaan (x, y), jumlah pose yang benar tak hingga, dan solver iteratif memilih pose yang paling dekat dengan pose awalnya. Di game, pose awal itu biasanya pose frame sebelumnya, jadi gerakannya tidak meloncat dari satu jawaban ke jawaban lain.

### 10.000 target acak

Saya mengacak 10.000 target di dalam jangkauan lengan saya (sampai 99,9% dari 73 cm), masing-masing dengan pose awal acak, dan batas 1000 iterasi:

| | Hasil |
|---|---|
| median iterasi | 13 |
| persentil ke-95 | 128 |
| target di atas 95% jangkauan (947 buah), median iterasi | 98 |
| belum mencapai 1e-9 dalam 1000 iterasi | 39 (0,39%) |
| error terbesar di antara 39 itu | 0,03 cm (0,3 mm) |

Dari 39 target yang belum selesai:
- **31 berada di atas 98% jangkauan.** Di dekat lengan lurus penuh, setiap iterasi hanya mengurangi error sedikit. Rasionya 0,48 di 90% jangkauan, 0,94 di 99%, dan 0,994 di 99,9%. Target di 99% jangkauan butuh 332 iterasi (garis oranye di gambar).
- **8 berada sekitar 15 cm dari bahu.** Di sana FABRIK berakhir dengan siku terlipat hampir 180° (misalnya 174° dan 178°). Konvergensinya lambat, dan **pose itu mustahil untuk siku manusia**.

## Yang saya pelajari, dan keterbatasannya

- **Untuk 2 bone, rumus analitik lebih baik:** satu kali hitung, tepat sampai 1e-16, dan langsung memberi kedua solusinya. FABRIK baru berguna saat bone-nya lebih dari dua, atau saat rumus tertutupnya tidak ada.
- **FABRIK sederhana dan selalu menjaga panjang tulang**, tapi kecepatannya bergantung pada letak target. Engine membatasi jumlah iterasi dan menerima jarak "cukup dekat", seperti `max_iterations = 10` dan `min_distance = 0,01` di `SkeletonIK3D`.
- **Versi saya tidak punya batas sendi.** Siku manusia hanya menekuk ke satu arah, kira-kira sampai 150° (perkiraan umum, tidak saya ukur), tapi FABRIK di atas bebas menghasilkan siku terlipat 178° atau menekuk ke belakang. Rig sungguhan butuh batas sudut di setiap sendi dan sebuah pole (seperti `magnet` di `SkeletonIK3D`) untuk memilih arah tekukan.

## Test

`test_fabrik` di `tests.py` mengecek:
- FABRIK ke (4, 1) sama dengan solusi analitik sampai 1e-6°, dalam 10 iterasi;
- errornya turun dengan rasio 0,10 sampai 0,12 per iterasi setelah stabil;
- lengan saya mencapai ujung jari dari posisi lurus dengan pose yang berbeda dari foto;
- dari pose foto selesai dalam 0 iterasi;
- target 80 cm ditolak dan lengan diluruskan dengan kekurangan tepat 7 cm.

Saya juga membuktikan test itu bisa gagal: kalau langkah tarik di FABRIK dibuat meleset 0,1% dari panjang tulang, test langsung gagal di sudut bahu. `tests.py` sekarang `ALL CHECKS PASSED (171 ok)`.
