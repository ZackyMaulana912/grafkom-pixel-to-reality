# Prediksi forward vs backward (Lab 1 no 4, Lab 3 no 3)

Ditulis **sebelum** `bench.mjs` dijalankan pada denah saya. File ini di-commit lebih dulu daripada hasil pengukurannya, supaya riwayat git membuktikan urutannya.

## Yang dibandingkan

`bench.mjs` menggambar denah `myplan.json` di framebuffer 800 × 600 dengan dua cara, pada zoom 1× dan 10× (zoom di sekitar pusat canvas):

- **Forward (rasterise):** untuk setiap segmen, jalankan Bresenham dari ujung ke ujung.
- **Backward (per pixel):** untuk setiap pixel layar, hitung jaraknya ke setiap segmen. Pixel dinyalakan kalau jaraknya paling jauh 0,75 pixel. Begitu satu segmen kena, segmen lain tidak diuji lagi.

## Model biaya, dengan angka dari denah saya

Angka ini saya hitung dari geometri denah saja, tanpa mengukur waktu:

| Zoom | Segmen | Langkah Bresenham (forward) | Uji jarak pixel × segmen (backward) |
|---|---|---|---|
| 1× | 20 | 2.621 | 800 × 600 × 20 = 9.600.000 |
| 10× | 20 | 26.030 | 9.600.000 |

- **Forward** sebanding dengan total panjang segmen dalam pixel. Zoom 10× membuat semua segmen 10 kali lebih panjang, jadi langkahnya naik dari 2.621 ke 26.030. Bresenham tetap berjalan sepanjang segmen walaupun sebagian besar sudah keluar layar, karena `fb.set` hanya menolak pixel di luar layar, tidak memotong garisnya lebih dulu.
- **Backward** sebanding dengan jumlah pixel × jumlah segmen, dan **tidak bergantung pada zoom**. Pixel yang kena garis kurang dari 1% dari layar (sekitar 2.600 langkah garis dibanding 480.000 pixel), jadi keluar lebih awal dari loop hampir tidak menghemat apa-apa.

Satu hal lagi dari membaca kodenya: `bench.mjs` membuat `new Framebuffer(800, 600)` **di dalam** bagian yang diukur, untuk kedua cara. Itu 1.440.000 byte yang harus dialokasikan dan dinolkan setiap kali. Untuk forward yang langkahnya cuma ribuan, saya menduga alokasi ini justru lebih mahal daripada menggambar garisnya.

## Prediksi

| | Zoom 1× | Zoom 10× |
|---|---|---|
| Forward | sekitar 0,2 sampai 1 ms, didominasi alokasi framebuffer | sedikit lebih lambat dari 1×, paling banyak 3 kali lipat, karena langkahnya 10 kali lebih banyak tapi alokasinya sama |
| Backward | sekitar 50 sampai 300 ms (9,6 juta uji jarak, perkiraan saya 5 sampai 30 ns per uji) | **hampir sama** dengan 1×, selisihnya di bawah 30% |
| Yang lebih cepat | **forward**, sekitar 100 sampai 1000 kali | **forward**, sekitar 50 sampai 500 kali |

Rasio di zoom 10× saya perkirakan lebih kecil daripada di 1×, karena forward bertambah berat sementara backward tetap.

## Bagian yang paling tidak saya yakini

1. **Waktu absolut.** Saya belum pernah mengukur kecepatan V8 di Mac ini untuk loop seperti ini, jadi rentangnya lebar.
2. **Backward di zoom 10×.** PDF modul sudah menuliskan contoh angka dari mesin penulisnya untuk `pusaka_plan.json` (37 segmen): forward sekitar 1 ms dan 3 ms, backward sekitar 520 ms dan 380 ms. Artinya di mesin itu backward malah **lebih cepat** di zoom 10×. Model biaya saya tidak menjelaskan kenapa bisa begitu, jadi prediksi saya tetap "hampir sama". Kalau hasil saya juga lebih cepat di 10×, berarti ada efek yang belum saya masukkan ke model, dan itu harus saya cari penyebabnya.
3. **Seberapa besar porsi alokasi framebuffer** di waktu forward.

## Pilihan yang saya duga akan saya ambil

Untuk viewer denah yang bisa di-pan dan di-zoom: **forward**. Biayanya mengikuti jumlah garis yang digambar, bukan jumlah pixel layar, dan denah hanya punya puluhan segmen. Backward baru masuk akal kalau setiap pixel memang perlu dihitung sendiri, misalnya untuk efek per pixel.
