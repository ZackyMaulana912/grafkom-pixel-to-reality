# Fase 4: Perbaikan foot-slide dan pitfall (c) (Lab 2 no 2 dan 4)

Diagnosis saya sudah di-commit lebih dulu (`docs/prediksi/diagnosis-foot-slide.md`, commit `44ad407`), sebelum kode perbaikan di catatan ini ditulis. Isinya: celah root dan kaki tumbuh 0,5 m/s, dan kecepatan yang benar adalah `scripted_speed = STRIDE_PER_CYCLE × CYCLE_RATE`.

## Yang saya ubah di `foot_slide_bug.py` sebelum diagnosis

Starter sudah membocorkan jawabannya (T6): docstring-nya menjelaskan akar masalah ("If SCRIPTED_SPEED != STRIDE_PER_CYCLE * CYCLE_RATE ... the feet slip against the floor"), dan bagian utama programnya mencetak versi "fixed" lengkap dengan rumusnya. Untuk commit diagnosis, docstring itu saya ganti dengan deskripsi netral, lalu saya tambah mode `--diagnose` yang hanya mencetak jarak root, jarak langkah kaki, dan celahnya untuk kecepatan yang dilaporkan (1,5 m/s), tanpa bagian perbaikan dan tanpa assert.

## Perbaikan: satu perubahan

Perubahannya: kecepatan root tidak lagi berupa angka yang diketik di kode game, melainkan dihitung dari data klip.

```python
def matched_speed(stride=STRIDE_PER_CYCLE, rate=CYCLE_RATE):
    return stride * rate
```

Hasilnya (`.venv/bin/python foot_slide_bug.py`):

```
-- before: scripted_speed = 1.5 m/s (typed in game code) --
-- after:  scripted_speed = matched_speed() = STRIDE_PER_CYCLE x CYCLE_RATE = 1.0 m/s --
 t (s)  gap before (m)  gap after (m)
   0.0          +0.000            0.0
   0.5          +0.250            0.0
   1.0          +0.500            0.0
   ...
   4.5          +2.250            0.0
   5.0          +2.500            0.0
gap after the fix is exactly 0.0 at every sample: True
```

Kolom "gap after" sengaja dicetak dengan `repr`, bukan dibulatkan ke 3 desimal. Jadi `0.0` di sana benar-benar nol, bukan angka kecil yang tampak nol karena dibulatkan.

| t (s) | Celah sebelum (m) | Celah sesudah (m) |
|---|---|---|
| 0,0 | +0,000 | 0,0 |
| 1,0 | +0,500 | 0,0 |
| 2,0 | +1,000 | 0,0 |
| 3,0 | +1,500 | 0,0 |
| 4,0 | +2,000 | 0,0 |
| 5,0 | +2,500 | 0,0 |

![Celah sebelum dan sesudah perbaikan, dan pitfall (c)](../img/foot_slide_before_after.png)

### Mencocokkan dengan prediksi di diagnosis

1. **"Celah tepat 0,000 di setiap sampel."** Tepat. Test mengeceknya dengan `== 0.0`, bukan dengan toleransi, untuk 11 sampel (setiap 0,5 detik), 51 sampel (setiap 0,1 detik), dan 301 sampel (setiap frame pada 60 fps). Nolnya tepat karena kedua jarak dihitung dengan operasi float yang sama persis, `(stride × rate) × t`: root memakai `matched_speed() * t`, dan jarak kaki memakai `stride * rate * t`, yang di Python juga dihitung dari kiri ke kanan. Jadi hasilnya tepat nol untuk klip berapa pun, tidak hanya untuk 1,0 dan 1,0. Saya mengeceknya pada 100.000 klip acak (langkah dan laju 0,1 sampai 3, t sampai 100 detik), dan tidak ada satu pun yang celahnya bukan nol. Test baru mengulang cek ini untuk 1000 klip acak.
2. **"Kolom root sama dengan kolom animation."** Tepat, karena celahnya nol.
3. **"Dengan kecepatan yang salah, celah melewati 5 cm setelah 0,1 detik."** Dari rumus celah `0,5 · t`, celah 5 cm tercapai di t = 0,1 s. Di Godot ini berarti sekitar 6 frame pada 60 fps. Jadi bug ini seharusnya langsung terlihat, bukan "dalam dua detik" seperti yang ditulis PDF (T14). Ini baru dari rumus; pengamatan di Godot ada di Fase 5.

### Test diperbaiki (T6)

Test starter memakai angka mati: `foot_slide_at(5.0, 1.5)` harus 2,5 dan `foot_slide_at(5.0, 1.0)` harus 0. Kalau klipnya berubah, test itu tetap hijau walaupun kecepatan "fixed" sudah salah. Test baru:
- kecepatan benar diambil dari `matched_speed()`, dan dicek sama dengan `STRIDE_PER_CYCLE * CYCLE_RATE`;
- celah buggy harus sama dengan `(REPORTED_SPEED - matched_speed()) · t` di setiap sampel (selisih di bawah 1e-12) dan harus terus tumbuh;
- celah sesudah perbaikan harus tepat `0.0` di 11, 51, dan 301 sampel, dan juga untuk 1000 klip acak.

## Pitfall (c): kecepatan dibaca dari kurva animasi

Perbaikan di atas masih menyimpan satu asumsi: kaki maju dengan kecepatan konstan di sepanjang langkah, dan panjang langkahnya tidak pernah berubah. Klip jalan sungguhan tidak begitu. Untuk Lab 2 no 4 saya memilih perbaikan (c): `scripted_speed` yang konstan diganti dengan kecepatan yang dibaca dari kurva animasi yang di-bake.

### Klip yang saya bayangkan

Modul mengizinkan kurva ini "dibayangkan", jadi bentuknya saya pilih sendiri dan saya tulis terang-terangan di kode:

- Dalam satu siklus dengan langkah 1 m, jarak maju kaki adalah `d(φ) = φ - 0,3 · sin(2πφ) / (2π)`, dengan φ fase dari 0 sampai 1. Kecepatannya `1 - 0,3 · cos(2πφ)`: lebih lambat saat kaki baru menapak, lebih cepat di tengah langkah, tapi rata-ratanya tetap 1 m per siklus. Angka 0,3 (`SWAY`) adalah pilihan saya, bukan hasil ukur.
- Kurva itu di-bake menjadi 31 keyframe (30 interval) per siklus, lalu dibaca dengan interpolasi linear, seperti klip di engine.
- Di t = 2,5 detik langkahnya berubah dari 1,0 m menjadi 0,8 m per siklus (misalnya karakter mulai berjalan dengan langkah pendek), sedangkan laju siklus tetap 1 per detik.

Ada dua pengendali root yang saya bandingkan, keduanya disimulasikan per frame pada 60 fps:
- **kecepatan konstan** 1,0 m/s, yaitu perbaikan pertama di atas;
- **root motion dari kurva:** setiap frame, root dimajukan sejauh selisih kurva antara awal dan akhir frame itu, yaitu jarak yang menurut klip benar-benar ditempuh kaki selama frame tersebut.

### Hasil

```
-- pitfall (c): stride drops from 1.0 m to 0.8 m per cycle at t = 2.5 s, 60 fps --
 t (s)         constant 1.0 m/s  baked root-motion curve
   0.0                  +0.0000                  +0.0000
   0.5                  -0.0000                  -0.0000
   ...
   2.5                  -0.0000                  -0.0000
   3.0                  +0.1000                  -0.0000
   4.0                  +0.3000                  -0.0000
   5.0                  +0.5000                  -0.0000
constant 1.0 m/s: max |gap| up to 2.5 s = 4.75e-02 m, after = 5.00e-01 m, at 5 s = +0.5000 m
baked root-motion curve: max |gap| up to 2.5 s = 4.44e-15 m, after = 1.15e-14 m, at 5 s = -0.0000 m
```

| Pengendali | Celah maks sampai 2,5 s | Celah maks sesudah 2,5 s | Celah di 5 s |
|---|---|---|---|
| kecepatan konstan 1,0 m/s | 4,75 cm | 50,0 cm | +50,0 cm |
| root motion dari kurva | 4,4e-15 m | 1,2e-14 m | 0 (pembulatan) |

Ada tiga hal yang saya pelajari dari sini:

1. **Kecepatan konstan yang "sudah benar" tetap membuat kaki tergelincir di dalam setiap langkah.** Celahnya naik turun sampai 4,75 cm (grafik kanan, sebelum garis putus-putus), karena root maju rata sedangkan kaki maju cepat-lambat. Tabel per 0,5 detik tidak memperlihatkannya sama sekali, karena 0,5 dan 1,0 detik jatuh tepat di tengah dan akhir siklus, saat `sin(2πφ) = 0`. Artinya cara mengambil sampel bisa menyembunyikan bug, jadi pengecekan foot-slide harus dilakukan per frame, bukan per detik. Besarnya cocok dengan rumus: amplitudo `0,3 / (2π) = 4,77 cm`, dan yang terukur 4,75 cm, sedikit lebih kecil karena kurva dibaca dari 30 keyframe linear dan sampelnya per frame.
2. **Begitu panjang langkah berubah, kecepatan konstan langsung salah lagi.** Setelah 2,5 detik celah tumbuh `(1,0 - 0,8) × 1 = 0,2 m/s`, sampai 50 cm di detik ke-5. Ini persis kasus §12.5: angka di kode game tidak ikut berubah saat klipnya berubah.
3. **Root motion dari kurva menjaga celah tetap nol, sampai batas pembulatan float.** Nilainya 1,2e-14 m dan bukan tepat 0, karena root adalah jumlah 300 selisih kecil per frame, sedangkan posisi kaki dihitung langsung dari kurva. Setiap penjumlahan menyumbang galat sekitar 1e-16, jadi 300 langkah memberi sekitar 1e-14. Ini sekitar 87 miliar kali lebih kecil dari 1 mm, jadi bukan foot-slide. Test memakai batas 1e-12 dan menjelaskan alasannya di komentar.

Test `test_pitfall_c_root_motion` juga mencoba jadwal yang lebih sulit: laju siklus berubah dari 1,0 ke 1,25 di t = 1,7 s, lalu langkah dan laju berubah lagi ke 0,9 m dan 0,8 siklus per detik di t = 3,3 s. Keduanya berubah di tengah siklus. Celah maksimumnya 1,2e-14 m.

Untung ruginya: cara ini paling banyak menambah kode dibanding pilihan (a) dan (b), dan butuh data kurva root motion di setiap klip. Sebagai gantinya, gameplay tidak bisa lagi tidak sinkron dengan animasi, karena hanya ada satu sumber kebenaran, yaitu klipnya. Cara yang sama akan saya pakai untuk walker di Godot, karena di sana penanda footfall juga masih ditaruh dari rumus, bukan dari posisi kaki yang sebenarnya (T11).

## Jumlah test

`tests.py` sekarang `ALL CHECKS PASSED (118 ok)`, dari 109 setelah Fase 3.
