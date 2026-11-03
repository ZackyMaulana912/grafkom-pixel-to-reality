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
