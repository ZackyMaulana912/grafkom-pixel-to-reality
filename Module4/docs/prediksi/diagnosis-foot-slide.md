# Diagnosis foot-slide (ditulis sebelum perbaikan)

File ini saya tulis **hanya** dari angka yang dicetak `foot_slide_bug.py --diagnose`, sebelum kode perbaikan apa pun ditulis atau dijalankan. Saya meng-commit file ini lebih dulu, supaya riwayat git membuktikan bahwa diagnosisnya datang sebelum hasil perbaikan.

## Bukti yang dicetak

```
$ .venv/bin/python foot_slide_bug.py --diagnose
scripted_speed = 1.5 m/s (root node, set by game code)
animation clip: STRIDE_PER_CYCLE = 1.0 m per cycle, CYCLE_RATE = 1.0 cycles/s
 t (s)  cycles  root (m)  animation (m)  gap (m)
   0.0    0.00     0.000          0.000   +0.000
   0.5    0.50     0.750          0.500   +0.250
   1.0    1.00     1.500          1.000   +0.500
   1.5    1.50     2.250          1.500   +0.750
   2.0    2.00     3.000          2.000   +1.000
   2.5    2.50     3.750          2.500   +1.250
   3.0    3.00     4.500          3.000   +1.500
   3.5    3.50     5.250          3.500   +1.750
   4.0    4.00     6.000          4.000   +2.000
   4.5    4.50     6.750          4.500   +2.250
   5.0    5.00     7.500          5.000   +2.500
```

Kolom `root` adalah jarak yang ditempuh node root karakter, yaitu yang digerakkan kode game. Kolom `animation` adalah jarak yang benar-benar "dilangkahkan" kaki menurut klip animasinya. Kolom `gap` adalah selisih keduanya.

## Apa yang tidak cocok

**Celahnya tidak konstan, tapi tumbuh lurus terhadap waktu.** Setiap 0,5 detik celah bertambah tepat 0,250 m. Kalau masalahnya hanya posisi awal yang bergeser, celahnya akan tetap sama dari awal sampai akhir. Celah yang terus tumbuh berarti yang salah adalah **kecepatan**: root dan kaki bergerak dengan laju yang berbeda.

**Laju tumbuh celah**, dihitung dari dua sampel:

```
dari t = 1,0 dan t = 3,0:  (1,500 - 0,500) / (3,0 - 1,0) = 0,5 m/s
dari t = 0,0 dan t = 5,0:  (2,500 - 0,000) / (5,0 - 0,0) = 0,5 m/s
```

Hasilnya sama di mana pun diambil, jadi celahnya memang garis lurus: `gap(t) = 0,5 · t`.

**Dari mana 0,5 m/s itu.** Laju masing-masing kolom:

```
root:      (7,500 - 0,000) / 5,0 = 1,5 m/s   = scripted_speed
animation: (5,000 - 0,000) / 5,0 = 1,0 m/s
```

Kolom `animation` selalu sama dengan kolom `cycles` dikali 1,0 m, artinya kaki maju sepanjang STRIDE_PER_CYCLE untuk setiap siklus. Jumlah siklus sendiri bertambah CYCLE_RATE per detik (kolom `cycles` = 1,0 · t). Jadi laju yang benar-benar dihasilkan langkah kaki adalah

```
v_animasi = STRIDE_PER_CYCLE × CYCLE_RATE = 1,0 m × 1,0 /s = 1,0 m/s
```

dan celahnya adalah

```
gap(t) = (scripted_speed - STRIDE_PER_CYCLE × CYCLE_RATE) · t = (1,5 - 1,0) · t = 0,5 · t
```

Rumus ini cocok dengan setiap baris tabel. Contohnya t = 2,5: (1,5 - 1,0) · 2,5 = 1,250 m, sama dengan kolom `gap`.

Yang terjadi di layar: root karakter maju 1,5 m setiap detik, sedangkan langkah kakinya hanya menutup 1,0 m. Sisa 0,5 m per detik tidak dilangkahkan oleh kaki, jadi kaki yang seharusnya menempel di lantai ikut terseret maju. Itulah foot-sliding, seperti berjalan di atas es.

## Kecepatan yang benar, sebagai rumus

Celah nol di setiap waktu berarti laju root harus sama dengan laju langkah kaki:

```
scripted_speed = STRIDE_PER_CYCLE × CYCLE_RATE
```

Bukan "ganti 1,5 dengan 1,0". Angka 1,0 hanya kebetulan hasil rumus ini untuk klip ini. Kalau klipnya diganti dengan langkah 0,8 m dan diputar 1,25 siklus per detik, kecepatan yang benar tetap dari rumus yang sama (0,8 × 1,25 = 1,0 m/s), sedangkan angka yang ditulis mati akan langsung salah lagi begitu salah satu nilainya berubah.

Ada dua arah untuk menyamakannya, dan keduanya memenuhi rumus yang sama:

1. **Root mengikuti animasi:** kecepatan root dihitung dari data klip, `scripted_speed = STRIDE_PER_CYCLE × CYCLE_RATE`. Gerakan karakter terlihat sesuai langkahnya, tapi kecepatan gameplay ikut ditentukan oleh animator.
2. **Animasi mengikuti root:** klip diputar lebih cepat, `CYCLE_RATE = scripted_speed / STRIDE_PER_CYCLE` = 1,5 siklus per detik. Kecepatan gameplay tetap 1,5 m/s seperti yang diinginkan desainer, tapi langkah kakinya menjadi lebih cepat dari yang dibuat animator.

Saya memilih arah 1, karena itu yang diminta tugas (kecepatan yang benar dinyatakan dari `stride_per_cycle * cycle_rate`), dan karena dari situ perbaikan pitfall (c) berlanjut: kecepatan root dibaca dari kurva animasi.

## Kaitan dengan pitfall §12.5

Modul menulis bahwa kapan pun nilai yang menggerakkan gerakan (kecepatan yang di-script) ditetapkan terpisah dari nilai yang sudah dienkodekan animasinya sendiri (panjang stride, durasi siklus), keduanya akan tidak sepakat kecuali disinkronkan secara eksplisit. Kasus ini persis begitu: `scripted_speed` = 1,5 ditulis di kode game, sedangkan 1,0 m per siklus dan 1,0 siklus per detik tersimpan di klip. Tidak ada yang menghubungkan keduanya, jadi tidak ada yang memaksa keduanya sama.

## Prediksi untuk perbaikannya

Kalau `scripted_speed` dihitung dari `STRIDE_PER_CYCLE × CYCLE_RATE`, prediksi saya:

1. Celah **tepat 0,000 di setiap sampel**, bukan sekadar mengecil. Kedua jarak dihitung dengan perkalian yang sama terhadap t, jadi untuk angka-angka ini hasilnya identik sampai bit terakhir. Kalau ternyata ada sisa sekecil 1e-16, berarti urutan perkaliannya berbeda, dan itu harus dijelaskan, bukan diabaikan.
2. Kolom `root` akan sama persis dengan kolom `animation` (0,5 m per 0,5 detik).
3. Dengan kecepatan yang salah, celah sudah melewati batas yang mudah terlihat (misalnya 5 cm) setelah 0,05 / 0,5 = **0,1 detik**. Jadi bug ini seharusnya langsung kelihatan dalam beberapa frame pertama, bukan "setelah dua detik".

Catatan batas diagnosis ini: angka di atas hanya membandingkan dua rumus jarak di Python. Ia belum membuktikan bahwa kaki stick figure di Godot benar-benar diam saat menapak, karena posisi kaki di Godot dihitung dari geometri kaki, bukan dari `STRIDE_PER_CYCLE` (temuan T11). Itu diukur terpisah di Fase 5.
