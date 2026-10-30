# Persiapan viva Modul 4

## Yang harus bisa saya lakukan langsung

1. **Menjalankan test.** `cd Module4/Source && source .venv/bin/activate && python tests.py`, hasilnya `ALL CHECKS PASSED (134 ok)`. Saya bisa menunjuk baris E1 sampai E4 (siku 2,598 / 1,500; IK -13,18° dan 70,53°; q(0,5) = (3, 1); slerp 36°) dan baris rantai saya (pergelangan 32,807 / 22,376 cm).
2. **Membuka scene Godot.** Buka `godot_project/project.godot` di Godot 4.7.2, tekan Play (F5), lalu:
   - **C**: pindah ke kamera overview supaya area demo terlihat;
   - **Space**: lengan berganti dari FK (30°/60°) ke IK target (4, 1), dan label menampilkan θ1 -13,18 dan θ2 70,53;
   - **U**: target pindah ke (5,5; 0), bola menjadi merah, dan label menulis "TARGET DI LUAR JANGKAUAN";
   - kubus merah (Euler, pitch 90°): labelnya menunjukkan yaw dan roll berubah, tapi kubusnya diam; kubus biru (quaternion) berputar;
   - **F**: walker berganti dari root motion (penanda hijau, geser 0,0 cm) ke perilaku starter (penanda dari rumus).
3. **Menjelaskan satu commit.** Pilihan saya: commit diagnosis foot-slide (`44ad407`) lalu perbaikannya (`2898aa9`). Diagnosis ditulis hanya dari angka `--diagnose`, dan riwayat git membuktikan diagnosis itu masuk lebih dulu.

## Pertanyaan yang mungkin muncul

**Kenapa sudut lokal, bukan global?**
Karena setiap sendi hanya tahu putarannya sendiri terhadap induknya. Kalau bahu saya berputar, siku dan tangan ikut terbawa tanpa ada angka yang perlu diubah, karena sudut globalnya selalu dihitung ulang sebagai jumlah sudut lokal dari root. Di rantai saya, kalau 83,4° di siku dipakai sebagai sudut global, pergelangan meleset 1,1 cm. `Skeleton3D` di Godot juga menyimpan pose lokal per tulang ("local to the bone with respect to the rotation of any parent bones").

**Apa yang berubah kalau rantai ini punya lima bone, bukan dua?**
FK tidak berubah: tetap perkalian matriks lokal dari root ke leaf, hanya lebih panjang (`fk.py` sudah menerima berapa pun bone, dan test-nya memakai 1 sampai 6 bone acak). IK yang berubah. Dua bone punya dua sudut dan dua persamaan (x, y), jadi aturan cosinus memberi paling banyak dua jawaban. Lima bone punya lima sudut tetapi tetap dua persamaan, jadi jawabannya tak hingga. Butuh solver iteratif seperti FABRIK atau CCD (dokumentasi `SkeletonIK3D` menyebut "uses FabrikInverseKinematic internally"), ditambah aturan untuk memilih satu jawaban: batas sendi, pole/magnet, atau pose paling dekat dengan pose sebelumnya.

**Sumbu mana yang terkunci di Godot, dan kenapa berbeda dengan Python?**
Yang terkunci selalu sumbu tengah urutan komposisinya. Python saya memakai `Rz · Ry · Rx`, sumbu tengahnya y, jadi terkunci di yaw 90°, dan hanya roll - pitch yang terlihat. Godot memakai intrinsic YXZ, yaitu `Ry · Rx · Rz`, sumbu tengahnya x, jadi terkunci di pitch 90°, dan hanya yaw - roll yang terlihat. Buktinya `Basis` dari Godot: di yaw 90° pasangan sudut berselisih 0,174 (tidak terkunci), di pitch 90° selisihnya 4,4e-8. Demo starter salah karena menyalin angka Python ke Godot.

**Kenapa gimbal lock tidak bisa diakali dengan "berputar sedikit lagi"?**
Di lock, sumbu cincin luar dan dalam segaris, jadi satu arah putaran memang tidak ada di antara ketiga sudut. Mendekati lock, sudutnya dihitung dengan membagi cos sudut tengah (Fjeld di ALSJ: "dividing by the cos of Z"), jadi perintahnya membesar tanpa batas. Collins memutari wilayah lock ("I am going around it"), dan Hoag (1963) menetapkan batas ±80° dengan lampu "GIMBAL LOCK".

**Kenapa foot-slide di Godot masih terjadi walaupun kecepatannya sudah "benar"?**
Karena `stride_per_cycle = 1,0` hanya angka yang ditulis. Kaki stick figure (0,92 m, ayunan ±0,45 rad) menempuh 4 · 0,92 · sin 0,45 = 1,60 m per siklus, jadi di 1,0 m/s kaki terseret 31,5 cm per langkah. Bahkan di 1,601 m/s masih 2,5 cm, karena kecepatan kaki tidak rata di dalam satu langkah. Solusinya root motion: badan digerakkan sejauh kaki yang menapak bergerak mundur, sehingga gesernya 2,4e-7 m.

**Kenapa celah sesudah perbaikan tepat 0, bukan cuma kecil?**
Kedua jarak dihitung dengan operasi float yang sama persis, `(stride × rate) × t`, jadi hasilnya identik sampai bit terakhir. Saya mengeceknya untuk 100.000 klip acak. Pada pitfall (c) celahnya 1,2e-14, bukan 0, karena root dijumlahkan dari 300 selisih per frame.

**Kenapa slerp, bukan blend linear?**
Slerp berjalan di busur bola satuan 4D dengan laju tetap, jadi sudut putaran bertambah rata dan selalu lewat jalur terpendek. Blend linear quaternion berjalan di tali busur, sehingga lebih lambat di ujung dan lebih cepat di tengah (34,48° di t = 0,25 untuk putaran 160°, bukan 40°). Blend matriks bahkan membuat model menyusut (sumbu x tinggal 0,174 di t = 0,5). Blend Euler di rig saya menempuh 127,3° untuk jarak 120° dan menyimpang 19,5° dari jalur terpendek.

**Kenapa prediksi Euler saya meleset, dan apa pelajarannya?**
Saya menganggap panjang jalur sama dengan sudut bersihnya. Ternyata kecepatan sudut `Rx(a) Rz(a)` konstan √2 · ȧ, jadi geraknya rata tapi memutar lebih jauh. Pelajarannya: "sudut dari titik awal" dan "panjang jalur yang ditempuh" adalah dua besaran yang berbeda.

**Kenapa angka Godot dan Python berbeda di 1e-7 atau 1e-8?**
`Vector2`, `Vector3`, `Basis`, dan `Quaternion` di Godot menyimpan float 32-bit (sekitar 7 digit), sedangkan Python dan `float` di GDScript 64-bit. Untuk lengan FK/IK saya menghitung dengan float 64-bit, jadi selisihnya 3e-13. Untuk `Basis` dan posisi node, toleransinya 1e-5, jauh di bawah perbedaan sungguhan (0,08 atau lebih).

**Asetnya dari mana dan boleh dipakai?**
Ruangan dan texture-nya karya saya dari Modul 3. Knight dari KayKit Adventurers karya Kay Lousberg, lisensi CC0 (LICENSE.txt ikut di repo), diunduh dari GitHub resmi pada 30 Oktober 2026. SHA-256 dan commit sumbernya dicatat di `assets/LICENSE.md`.

**Kenapa build Web 40 MB?**
39,5 MB adalah engine Godot (`index.wasm`), yang sama untuk proyek Godot apa pun. Isi game saya hanya 1,6 MB. Build-nya tanpa thread, jadi tidak butuh header cross-origin isolation, dan bisa jalan di GitHub Pages.
