# Sumber denah: ruangan tempat patung kuda

Subjek saya sejak Modul 1 adalah patung kuda berdiri milik saya sendiri. Patung tidak punya denah (tidak ada dinding, ruang, atau pintu), jadi untuk Modul 2 saya menelusuri denah **ruangan tempat patung itu berdiri** di rumah saya. Patungnya tetap ada di denah sebagai salah satu kategori.

## Ukuran

Diukur dan diceritakan oleh saya sendiri pada 28 Oktober 2026.

| Elemen | Ukuran | Asal angka |
|---|---|---|
| Ruangan | 2 m × 4 m, persegi panjang | ukuran saya |
| Lemari penyimpanan | menempel di dinding kanan sepanjang 4 m, dalam 0,4 m, 8 pintu (masing-masing 0,5 m) | ukuran saya |
| Sisi masuk | dinding pendek 2 m. Seperempatnya jalan masuk di pojok kiri (sekitar 0,5 m), tiga perempatnya sekat berlubang tempat menaruh vas (sekitar 1,5 m) | **perbandingan** 1/4 dan 3/4, belum diukur dengan meteran |
| Alas patung | 8 cm × 30 cm, sisi 30 cm sejajar dinding 4 m | ukuran saya |
| Letak patung | pusat alas 0,8 m dari dinding kiri dan 2,0 m dari sisi masuk | **perkiraan**: "di tengah-tengah lemari". Patung tidak di atas lemari, karena di Modul 1 saya memotretnya sambil mengelilinginya |

```
            2 m
     ┌──────────────┐
     │           ▐▐▐│
     │           ▐▐▐│
     │     ▮     ▐▐▐│  4 m   ▮ = patung 8 × 30 cm
     │           ▐▐▐│        lemari 4 m × 0,4 m, 8 pintu
     │           ▐▐▐│
     └ ─ ─ ┬░░░░░░░░┘
      masuk  sekat berlubang
     50 cm      1,5 m
```

## Dari ukuran ke `myplan.json`

- Satuan meter, titik asal di pojok kiri sisi masuk, y ke atas (sama dengan `pusaka_plan.json`).
- `scale_px_per_m` = 130, `origin_m` = [2,0; 0,3], sehingga ruangan menempati pixel x 260 sampai 520 dan y 40 sampai 560 di canvas 800 × 600. Panah jalan masuk ada di bawah ruangan, di area yang gelap.
- Dinding luar adalah polyline terbuka berbentuk U (kiri, belakang, kanan), karena sisi depan adalah sekat dan jalan masuk.
- Lemari digambar sebagai garis depan lemari ditambah 7 garis pembatas antar pintu.
- Lantai (siluet) adalah persegi panjang 2 × 4 m. Bentuknya cembung, jadi fan-triangulation di `renderPlan()` sudah benar.
- Hasilnya 14 polyline dan 20 segmen.

## Yang masih kurang

- **Tidak ada foto sketsa.** Ukuran ruangan saya ukur sendiri secara manual, lalu angkanya langsung saya tulis ke `myplan.json`.
- Lebar jalan masuk dan letak patung belum diukur dengan meteran. Kalau nanti diukur, cukup ubah angka di `myplan.json`. Semua test dan gambar dibuat ulang otomatis.
