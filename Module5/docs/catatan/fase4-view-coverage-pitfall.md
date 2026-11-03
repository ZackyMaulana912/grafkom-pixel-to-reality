# Fase 4: Diagnosis view coverage dan pitfall (Lab 2 no 3 dan 4)

Urutan fase ini dipatok supaya riwayat git membuktikan diagnosis ditulis sebelum hasilnya ada:

1. `nerf_bug.py --diagnose` hanya melatih model 2 view dan mencetak bukti latih;
2. prediksi ditulis di `docs/prediksi/diagnosis-view-coverage.md` dan di-commit;
3. baru setelah itu perbandingan dengan sudut baru dijalankan, lalu perbaikan pitfall.

## 1. Mode `--diagnose` (K14)

`nerf_bug.py --diagnose` melatih **hanya** grid 2 view (sudut 0 dan 20 derajat), lalu mencetak kurva MSE latih setiap 50 iterasi dan PSNR rata-rata di kedua view latihnya. Mode ini tidak menghitung PSNR sudut baru, tidak menjalankan model 8 view, dan tidak memberi kesimpulan. Pengaturan latihnya sama persis dengan mode lengkap (500 iterasi, lr 100, grid 12³, seed 0). Yang berubah hanya seberapa sering MSE dicatat, dan itu tidak memengaruhi latihannya: MSE akhir dan PSNR latih di kedua mode sama (`0.00836`, `21.13 dB`).

```
$ .venv/bin/python nerf_bug.py --diagnose
DIAGNOSE -- 2 views [0, 20] deg, 500 iterations, lr=100.0
  iter    0  train MSE = 0.14035
  iter   50  train MSE = 0.02087
  iter  100  train MSE = 0.01616
  iter  150  train MSE = 0.01405
  iter  200  train MSE = 0.01268
  iter  250  train MSE = 0.01157
  iter  300  train MSE = 0.01061
  iter  350  train MSE = 0.00984
  iter  400  train MSE = 0.00923
  iter  450  train MSE = 0.00875
  iter  499  train MSE = 0.00836
  mean training-view PSNR = 21.13 dB
(training evidence only: no novel view and no 8-view run in this mode)
```

## 2. Penjelasan dosen yang dipindah ke sini

Docstring `nerf_bug.py` dan bagian "Notes on fixes applied while verifying" di README starter sudah menjelaskan hasil tugas ini sebelum dikerjakan. Sesuai keputusan K14, keduanya saya pindahkan ke sini apa adanya, supaya file kode dan README tidak membocorkan jawabannya. Teksnya milik dosen dan tidak saya ubah.

**Docstring asli `nerf_bug.py`:**

```
"""Diagnose-and-fix: too few / too-clustered training views cause a NeRF to
memorise the views it saw and fail on angles it did not -- the toy-scale,
from-scratch analogue of real "floaters" / background-collapse when a
capture has too few poses or too narrow a baseline.

BUGGY:  2 views, 20 deg apart (0 deg, 20 deg) -- almost the same viewpoint.
FIXED:  8 views spread evenly around the full ring (0..315 deg, step 45).

Both are trained identically otherwise and evaluated on the *same* held-out
novel view, chosen to be far from the buggy pair's narrow baseline. The gap
in novel-view PSNR is the diagnostic evidence: it is not that the buggy grid
"looks wrong" in general -- it fits its own two training views about as well
as the fixed grid fits its eight -- it is that it has never seen, and cannot
predict, the rest of the object.
"""
```

**Bagian asli README starter**, termasuk satu poin dari "What `python tests.py` asserts" yang juga sudah menyebut hasilnya:

> ## Notes on fixes applied while verifying
>
> - **`sigma_raw` initialised at `-5.0` (an "empty" starting scene) silently
>   stalled training.** `softplus'(x) = sigmoid(x)`, and `sigmoid(-5) ~ 0.0067`
>   -- the density gradient was crushed by that factor from the very first
>   step, so 300 iterations barely moved the loss (`0.1107 -> 0.1100`).
>   Re-initialising at `sigma_raw = 0` (density `ln 2`, a neutral "half-there"
>   start) fixed it immediately (loss `0.137 -> 0.009` over 800 iterations).
>   Kept as a named pitfall in `Module5_EN.tex` -- exactly the kind of "the
>   gradient exists in principle but is numerically dead" bug this course's
>   diagnose-and-fix doctrine is meant to catch.
> - **The first view-coverage comparison used the same novel angle
>   (`22.5 deg`) for both the 2-view and 8-view models** and found the
>   *2-view* model generalised *better* -- the opposite of the intended
>   lesson. Root cause: `22.5 deg` is only `2.5 deg` from the 2-view cluster's
>   second view (`20 deg`) -- an easy near-interpolation for that model -- while
>   it is a harder `22.5 deg` from the nearest of the 8 spread views. Fixed by
>   evaluating both models on a novel angle (`190 deg`) chosen to be far from
>   the clustered pair; the intended effect (spread views generalise better)
>   then appears consistently across several tested novel angles.
> - The analytic backward pass (`backward_grid`) was derived by hand from the
>   compositing formula and got the **suffix-sum term** right on the first
>   full implementation, confirmed immediately by the finite-difference check
>   in `tests.py` (`max err ~3e-11`) -- included here as the honest exception
>   to "here is what broke," since MASTER Sec 9.6 asks for this section either
>   way.
>
>
> - **View-coverage diagnose-and-fix** -- training a voxel grid on 8 views
>   spread around the full ring beats training on 2 views clustered `20 deg`
>   apart by `> 1 dB` PSNR on the *same* held-out novel view (typically
>   `+2.7 dB`), even though the 2-view grid fits its own (fewer) training
>   views about as well.

## 3. Hasil di sudut baru, setelah prediksi di-commit

Prediksi di-commit di `319add1` (3 November 2026, 19.21). Baru setelah itu `nerf_bug.py --sweep` saya tambahkan dan jalankan. Mode ini melatih kedua grid persis seperti mode lengkap, lalu mengukurnya di sudut-sudut yang sudah ditulis di prediksi. Targetnya render pas dari scene analitik, bukan file 8 bit.

```
$ .venv/bin/python nerf_bug.py --sweep
training-view PSNR: 2 views 21.13 dB, 8 views 19.13 dB
 angle  nearest view 2v/8v   2 views   8 views    8v - 2v
  10.0    10.0 / 10.0    10.23     12.11     +1.88
  22.5     2.5 / 22.5    15.97     14.26     -1.71
  60.0    40.0 / 15.0    10.56     15.56     +5.00
 100.0    80.0 / 10.0     9.10     11.88     +2.78
 160.0   140.0 / 20.0     9.36     13.31     +3.95
 190.0   170.0 / 10.0     9.39     12.05     +2.66
 250.0   110.0 / 20.0     9.34     13.10     +3.76
 340.0    20.0 / 20.0    10.02     12.94     +2.92
 270.0    90.0 /  0.0     9.32     21.02    +11.70  <- training view of the 8-view grid, not held out
```

Dari 8 sudut held-out, model 8 view menang di 7 sudut dengan selisih +1.88 sampai +5.00 dB. Satu-satunya yang kalah adalah 22,5 derajat (-1.71 dB). Baris 270 derajat bukan held-out untuk model 8 view, jadi selisih +11.70 dB di sana tidak saya hitung sebagai bukti.

![PSNR kedua model di sekeliling lingkaran](../img/view_coverage.png)

Grafik di atas mengukur kedua model setiap 2,5 derajat di seluruh lingkaran (`figures.py --set readme`). Garis putus-putus adalah view latih.

![Sudut 60 derajat: target, kedua prediksi, dan selisihnya](../img/novel_60.png)

### Prediksi vs hasil

| No | Prediksi | Hasil | |
|---|---|---|---|
| 1 | di 60, 100, 160, 250 derajat model 8 view menang lebih dari 1 dB, selisih sekitar 2 sampai 6 dB; model 2 view 8,5 sampai 11 dB, model 8 view 11,5 sampai 16 dB | selisih +5.00, +2.78, +3.95, +3.76; model 2 view 9.10 sampai 10.56, model 8 view 11.88 sampai 15.56 | tepat |
| 2 | di 22,5 derajat model 2 view menang sekitar 1 sampai 2 dB | 2 view menang 1.71 dB | tepat |
| 3 | di 10 derajat model 2 view di bawah 12 dB dan kalah | 10.23 dB, kalah 1.88 dB | tepat |
| 4 | di 340 derajat model 2 view kalah lebih dari 1 dB | kalah 2.92 dB | tepat |
| 5 | model 8 view lebih rata (rentang sekitar 4 dB di sudut held-out), model 2 view hanya bagus di dekat 20 derajat | rentang model 8 view di sudut yang diuji 3.68 dB; model 2 view tinggi hanya di dekat 0 dan 20 derajat | tepat untuk sudut yang diuji, tetapi grafik menunjukkan model 8 view pun naik-turun tajam (lihat bawah) |
| 6 | di 270 derajat model 8 view sekitar 18 sampai 20 dB | 21.02 dB | **meleset**, 1 dB di atas rentang |
| 7 | bagian kuda di 60 sampai 160 derajat paling rusak di model 2 view | tidak terbukti (lihat bawah) | **meleset** |

Prediksi 2 dan 3 bersandar pada T7 (scene tanpa kuda), jadi ketepatannya tidak terlalu mengejutkan. Prediksi 1, 4, 5, 6, dan 7 adalah sudut dan hal yang belum pernah diukur.

**Kenapa prediksi 7 meleset.** Saya ukur kesalahan rata-rata khusus di pixel kuda (pixel yang berubah kalau kuda dihapus dari scene):

| Sudut | Pixel kuda | Kesalahan di kuda: 2 view / 8 view | Kesalahan di sisa gambar: 2 view / 8 view |
|---|---|---|---|
| 60 | 6 | 0,125 / 0,104 | 0,234 / 0,124 |
| 100 | 7 | 0,180 / 0,162 | 0,310 / 0,200 |
| 160 | 3 | 0,165 / 0,161 | 0,294 / 0,163 |
| 10 | 5 | 0,172 / 0,319 | 0,220 / 0,192 |
| 340 | 5 | 0,479 / 0,470 | 0,263 / 0,160 |

Di sisa gambar, model 2 view jelas lebih buruk. Tetapi di kuda, kedua model sama-sama buruk. Penyebabnya bukan sebaran sudut, melainkan ukuran: kuda hanya selebar satu sampai dua voxel grid 12³, jadi tidak ada model yang bisa menggambarnya, berapa pun jumlah view-nya. Jumlah pixelnya juga hanya 2 sampai 7 per sudut, jadi angka di tabel ini mudah berubah dan tidak bisa dipakai menarik kesimpulan kuat. Pelajarannya: menambah view hanya menolong kalau modelnya cukup halus untuk menyimpan detail itu.

**Yang tidak saya prediksi, terlihat di grafik:**
- **Model 8 view juga sangat bergantung pada jarak ke view latih.** PSNR-nya sekitar 17,5 sampai 21 dB tepat di view latih, lalu turun sampai sekitar 11,6 dB di sela dua view latih. Delapan view tidak membuat model "paham" bentuk candi. Model hanya punya lebih banyak titik pegangan di sekeliling lingkaran, jadi tidak ada sudut yang jauh dari pegangan.
- **Model 2 view punya lantai sekitar 9 sampai 11 dB.** Lebih dari sekitar 40 derajat dari view latihnya, kualitasnya tidak turun lagi, karena di sana ia sudah sama sekali tidak tahu apa-apa. Yang tersisa hanya warna rata-rata.
- **View latih diagonal model 8 view lebih rendah.** Di 45, 135, 225, dan 315 derajat PSNR-nya sekitar 17,5 dB, sedangkan di 90, 180, dan 270 derajat sekitar 20,5 sampai 21 dB. Dugaan saya, ini karena sumbu voxel grid sejajar dengan sumbu x dan z, jadi kamera diagonal melihat tepi voxel yang miring. Belum saya buktikan.
- **Soal T7.** Panduan mencatat PSNR 12,02 dB yang persis sama di 10, 100, dan 190 derajat untuk scene tanpa kuda, dan menduga penyebabnya simetri 4 arah. Dengan kuda, simetri itu rusak, dan angkanya tidak lagi sama (12.11, 11.88, 12.05). Ini mendukung dugaan simetri tersebut, walaupun belum membuktikannya.

### Kesimpulan diagnosis

PSNR latih model 2 view (21.13 dB) lebih tinggi dari model 8 view (19.13 dB), padahal di 7 dari 8 sudut baru ia kalah 1,9 sampai 5 dB. Ini persis pitfall 12.2: kualitas di view latih tidak bisa membedakan model yang paham bentuk 3D-nya dari model yang hanya menghafal dua gambar. Penyebabnya pitfall 12.3: dua foto yang hanya berbeda 20 derajat hampir tidak memberi informasi kedalaman. Hasil di 22,5 derajat menunjukkan bahwa satu sudut uji saja bisa menyesatkan: kalau hanya sudut itu yang diuji, kesimpulannya terbalik. Karena itu saya menguji 8 sudut, dan grafiknya mengukur 144 sudut.
