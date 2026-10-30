# Prediksi: Euler vs quaternion pada rig lengan saya (ditulis sebelum pengukuran)

File ini saya tulis dan commit **sebelum** konfigurasinya dipaksakan dan diukur di Godot (Lab 3 no 3). Semua angka di sini berasal dari penurunan dengan tangan, bukan dari hasil run.

## Sendi yang dipilih

Saya memilih **bahu rig lengan saya** (`bone_0` di `my_arm_rig.gd`). Sendi ini berputar paling banyak, karena seluruh lengan (lengan atas, lengan bawah, tangan) ikut terbawa. Di rig sekarang bahu hanya berputar terhadap sumbu z, tetapi bahu sungguhan adalah sendi bola dengan tiga derajat kebebasan. Untuk prediksi ini bahu diputar penuh di 3D dengan dua cara:

- **Euler**, lewat properti `rotation` sebuah `Node3D` dengan urutan bawaan Godot, yaitu intrinsic YXZ: `Basis = Ry(yaw) · Rx(pitch) · Rz(roll)`;
- **quaternion**, lewat `Quaternion` dan `slerp`.

Di ruang lokal rig, tulang lengan atas mengarah ke +x. Jadi pitch (terhadap x) memuntir lengan terhadap sumbunya sendiri, roll (terhadap z) mengangkat lengan di bidang foto (gerakan yang sama dengan sudut lokal di `my_chain.json`), dan yaw (terhadap y) mengayunkan lengan ke kiri dan kanan.

## Prediksi 1: orientasi yang gagal dicapai Euler dengan bersih

Sumbu tengah urutan YXZ adalah x, jadi Euler terkunci saat **pitch = ±90°** (penurunan di catatan Fase 3, dan sudah dibuktikan untuk kubus di Fase 5). Di pitch = 90°:

```
Ry(yaw) · Rx(90°) · Rz(roll) = Ry(yaw - roll) · Rx(90°)
```

Arah lengan atas adalah bayangan sumbu +x:

```
Rz(roll) (1, 0, 0) = (cos roll, sin roll, 0)
Rx(90°) (cos roll, sin roll, 0) = (cos roll, 0, sin roll)
Ry(yaw) mengubah x dan z saja, jadi komponen y tetap 0
```

Prediksi saya:
- **(a)** Dengan pitch = 90°, untuk yaw dan roll berapa pun, komponen y arah lengan selalu 0. Lengan hanya bisa mengarah mendatar, jadi **mengangkat atau menurunkan lengan tidak mungkin** dengan hanya mengubah yaw dan roll.
- **(b)** Pasangan (yaw, roll) = (20°, 10°), (15°, 5°), dan (10°, 0°) memberi posisi siku dan ujung jari yang sama, sampai pembulatan float 32-bit (selisih di bawah 1e-6 m). Pasangan dengan yaw + roll tetap memberi posisi yang jelas berbeda.
- **(c)** Yang akan terlihat di layar: kalau pitch dipatok 90° lalu roll dinaikkan, lengan tidak terangkat, tetapi berputar mendatar, persis seperti kalau yaw diturunkan. Satu tombol putar seolah hilang.

## Prediksi 2: interpolasi menuju orientasi yang terkunci

Bahu digerakkan dari A = Euler (pitch, yaw, roll) = (0°, 0°, 0°), yaitu lengan lurus ke depan, ke B = (90°, 0°, 90°), yaitu orientasi yang berada tepat di lock.

**Sudut putaran B.** `B = Rx(90°) · Rz(90°)` (yaw 0). Trace dari `Rx(a) · Rz(a)` adalah `2 cos a + cos² a`, dan sudut putaran θ memenuhi `1 + 2 cos θ = trace`. Untuk a = 90°: trace = 0, jadi cos θ = -1/2 dan **θ = 120°**. Ini sesuai sifat yang sudah dikenal: dua putaran 90° terhadap sumbu yang saling tegak lurus menghasilkan satu putaran 120°.

**Slerp (quaternion):** sudut dari A naik rata, 120° · t. Langkah sudut per frame sama besar dari awal sampai akhir, jadi rasio langkah terbesar dibanding terkecil = 1 (sampai pembulatan).

**Blend linear Euler (pitch dan roll sama-sama 90° · t):** `M(t) = Rx(90° t) · Rz(90° t)`, jadi

```
cos θ(t) = (cos² a + 2 cos a - 1) / 2,   a = 90° · t
```

- di t = 0,5 (a = 45°): cos θ = (0,5 + 1,4142 - 1) / 2 = 0,4571, jadi **θ = 62,8°**, bukan 60° seperti slerp;
- di awal gerakan (a kecil): cos θ ≈ 1 - a², jadi θ ≈ √2 · a, artinya kecepatan sudutnya **√2 · 90° = 127,3° per durasi**, lebih cepat dari slerp yang 120° per durasi;
- karena total sudutnya sama-sama 120°, gerakan Euler pasti melambat di bagian akhir. Rasio langkah sudut terbesar dibanding terkecil **lebih dari 1**.

Selain kecepatannya, jalurnya juga berbeda. Di tengah jalan, orientasi hasil Euler tidak sama dengan orientasi hasil slerp, jadi **sudut di antara keduanya di t = 0,5 lebih dari 0°**. Besarnya tidak saya turunkan, jadi untuk angka ini saya hanya memprediksi tandanya.

## Kenapa versi quaternion tidak gagal

Quaternion menyimpan orientasi sebagai satu titik di bola satuan 4D. Tidak ada "sumbu tengah" yang bisa jatuh segaris dengan sumbu lain, jadi tidak ada orientasi di mana arah putaran tertentu hilang. Dari orientasi B pun, putaran kecil terhadap sumbu mana saja tetap berupa perubahan kecil pada quaternion. Contohnya, memutar 10° terhadap sumbu horizontal yang tegak lurus lengan akan mengangkat ujung lengan, sesuatu yang menurut prediksi 1(a) tidak bisa dilakukan Euler dengan pitch tetap 90°. Di B arah lengan adalah (cos 90°, 0, sin 90°) = (0, 0, 1), jadi sumbu itu adalah sumbu x. Prediksi 3: **dari B, putaran quaternion 10° terhadap sumbu x mengubah komponen y arah lengan dari 0 menjadi ±sin 10° = ±0,174** (untuk vektor arah satuan; tandanya bergantung pada arah putaran).

## Apa yang akan diukur sesudah file ini di-commit

1. Bahu rig diputar dengan `Node3D.rotation` (YXZ) pada pitch = 90° untuk beberapa pasangan (yaw, roll), lalu `Basis`, arah lengan, dan posisi siku serta ujung jari dicetak (prediksi 1).
2. Interpolasi A ke B dengan blend Euler dan dengan `Quaternion.slerp`, disampel per frame. Yang dicatat: sudut dari A, langkah sudut per frame, dan sudut antara kedua versi di t = 0,5 (prediksi 2).
3. Dari B, putaran quaternion 10° terhadap sumbu horizontal yang tegak lurus lengan, lalu komponen y arah lengan dicetak (prediksi 3).

Setelah itu hasilnya saya cocokkan dengan prediksi ini: mana yang tepat, mana yang meleset, dan kenapa.
