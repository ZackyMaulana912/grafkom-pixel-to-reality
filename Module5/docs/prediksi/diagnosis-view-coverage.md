# Diagnosis dan prediksi: 2 view vs 8 view (Lab 2 no 3)

Ditulis 3 November 2026, **sebelum** perbandingan di banyak sudut baru dijalankan pada scene saya (candi + patung kuda mini). Hasil latih yang saya pakai sebagai bukti hanyalah output `nerf_bug.py --diagnose` (model 2 view saja). File ini di-commit dulu, baru pengukurannya dijalankan.

**Yang sudah saya ketahui sebelumnya, supaya jelas prediksi ini tidak buta:**
- angka modul di scene tanpa kuda: 2 view 9.30 dB dan 8 view 12.02 dB di 190 derajat;
- tabel T7 di panduan saya: hasil run awal di scene tanpa kuda untuk enam sudut, termasuk bahwa di 22,5 derajat model 2 view justru menang;
- **satu angka dari scene saya sendiri sudah terlanjur terlihat:** saat menambah kuda di Fase 3, `nerf_bug.py` dan `tests.py` tetap harus dijalankan, dan keduanya mencetak hasil di 190 derajat, yaitu 2 view 9.39 dB dan 8 view 12.05 dB (+2.66 dB). Jadi sudut 190 derajat di bawah bukan prediksi, melainkan angka yang sudah diketahui. Tujuh sudut lainnya belum pernah dijalankan.

Scene saya sekarang berbeda (ada kuda, data latih dari file 8 bit), jadi angka itu tidak bisa disalin. Saya memakainya sebagai pegangan, dan menandai prediksi mana yang bersandar padanya.

## 1. Bukti latih model 2 view

```
2 views [0, 20] deg, 500 iterations, lr=100.0
iter 0: 0.14035   50: 0.02087   100: 0.01616   200: 0.01268   300: 0.01061   400: 0.00923   499: 0.00836
mean training-view PSNR = 21.13 dB
```

Kurvanya turun mulus tanpa lonjakan, paling cepat di 50 iterasi pertama, dan masih pelan-pelan turun di akhir (`0.00875` ke `0.00836` dalam 50 iterasi terakhir). PSNR di kedua view latihnya 21,13 dB. Sebagai pembanding, model 8 view di `fit_nerf_toy.py` (800 iterasi, Fase 3) hanya mencapai 20,32 dB di view latihnya.

## 2. Apakah saya akan curiga kalau hanya melihat angka ini?

**Tidak, kalau hanya dari angka latihnya.** Kurva yang turun mulus dan PSNR latih yang bahkan lebih tinggi dari model 8 view terlihat seperti latihan yang sehat. Tidak ada satu pun angka di atas yang memberi tanda bahaya. Kalau curiga, alasannya datang dari luar angka latih, yaitu dari cara capture-nya dibuat:

- **Jumlah yang harus ditebak jauh lebih banyak daripada yang dilihat.** Grid 12³ punya 1728 voxel × 4 angka (density + 3 warna) = 6912 parameter. Dua gambar 20 × 16 hanya memberi 2 × 20 × 16 × 3 = 1920 angka. Ada banyak sekali scene 3D berbeda yang menghasilkan dua gambar itu dengan sama baiknya. Grid tinggal memilih salah satu, dan tidak ada yang memaksanya memilih scene yang benar. Delapan gambar memberi 7680 angka, lebih banyak dari jumlah parameternya.
- **Masalahnya bukan voxel yang tidak terlihat, melainkan arah pandang yang hampir sama.** Saya hitung dari geometri kamera saja, tanpa melatih apa pun: ray dari 2 view itu menembus 1714 dari 1728 voxel, hampir semuanya. Tetapi semua ray itu datang dari arah yang hanya berbeda 20 derajat. Satu ray hanya tahu warna akhirnya, tidak tahu di kedalaman mana warna itu berada. Untuk memastikan kedalaman, satu titik harus dilihat dari dua arah yang cukup berbeda, dan beda 20 derajat itu tipis sekali. Grid bisa menaruh warna yang benar di kedalaman yang salah, dan kedua view latih tetap terlihat benar.
- **PSNR latih yang tinggi justru wajar untuk kasus ini.** Menjelaskan 2 gambar lebih gampang daripada 8, jadi model 2 view punya lebih banyak kebebasan per gambar. PSNR latih mengukur seberapa baik model menghafal yang ia lihat, bukan seberapa benar bentuk 3D-nya.

Jadi PSNR view latih bukan bukti yang cukup (pitfall 12.2): ia hanya bisa membuktikan model gagal, tidak bisa membuktikan model benar. Satu-satunya cara menguji bentuk 3D-nya adalah melihatnya dari sudut yang tidak pernah dipakai melatih. Pitfall 12.3 menjelaskan sumber masalahnya: yang penting adalah sebaran sudut, bukan jumlah foto. Dua foto berjarak 20 derajat hampir tidak memberi informasi 3D lebih banyak daripada satu foto.

## 3. Prediksi saya

Sudut yang akan diuji, dengan model 2 view dilatih di 0 dan 20 derajat, dan model 8 view di 0, 45, 90, ..., 315 derajat:

| Sudut | Jarak ke view latih terdekat: 2 view / 8 view | Status |
|---|---|---|
| 10 | 10° / 10° | held-out untuk keduanya, di antara dua view latih model 2 view |
| 22,5 | 2,5° / 22,5° | held-out untuk keduanya, sangat dekat dengan view 20 |
| 60 | 40° / 15° | held-out untuk keduanya |
| 100 | 80° / 10° | held-out untuk keduanya |
| 160 | 140° / 20° | held-out untuk keduanya |
| 190 | 170° / 10° | held-out untuk keduanya, sudut modul; **hasilnya sudah diketahui** (9.39 / 12.05 dB) |
| 250 | 110° / 20° | held-out untuk keduanya |
| 340 | 20° / 20° | held-out untuk keduanya, di sisi lain view 0 |
| 270 | 90° / **0°** | **view latih model 8 view**, hanya sebagai pembanding, bukan held-out |

Prediksi yang bisa dibuktikan salah:

1. **Di sudut yang jauh dari 0 dan 20 derajat (60, 100, 160, 250; 190 sudah diketahui), model 8 view menang lebih dari 1 dB di setiap sudut**, dengan selisih sekitar 2 sampai 6 dB. Model 2 view di sudut-sudut ini sekitar 8,5 sampai 11 dB, model 8 view sekitar 11,5 sampai 16 dB.
2. **Di 22,5 derajat hasilnya terbalik: model 2 view menang**, sekitar 1 sampai 2 dB. Sudut ini hanya 2,5 derajat dari view latihnya, jadi gambar yang ia hafal masih hampir berlaku. Bagi model 8 view, sudut ini berjarak 22,5 derajat dari view terdekat. Prediksi ini bersandar pada T7.
3. **Di 10 derajat, walaupun berada di antara dua view latihnya sendiri, model 2 view tetap buruk, di bawah 12 dB, dan kalah dari model 8 view.** Ini bagian yang paling tidak intuitif. Alasan saya: warna yang ditaruh di kedalaman yang salah hanya tetap benar tepat di sudut latih. Bergeser 10 derajat saja sudah cukup membuat letak yang salah itu kelihatan. Prediksi ini juga bersandar pada T7.
4. **Di 340 derajat**, yang berjarak 20 derajat dari view 0 tetapi di sisi yang tidak pernah dilihat model 2 view, model 2 view kalah lebih dari 1 dB.
5. **Model 8 view lebih rata**: semua sudut held-out-nya berada dalam rentang sekitar 4 dB. Model 2 view naik-turun lebih tajam: bagus hanya di dekat 20 derajat.
6. **Di 270 derajat** (view latih model 8 view), model 8 view sekitar 18 sampai 20 dB, jauh di atas sudut held-out-nya. Selisih besar di sudut ini tidak boleh dihitung sebagai bukti, karena model 8 view memang pernah melihatnya.
7. **Patung kuda:** sisi depan kuda (+z) paling jelas terlihat di sekitar 90 derajat. Model 2 view tidak pernah melihat sisi itu, jadi bagian kuda di sudut 60 sampai 160 derajat akan paling rusak di model 2 view.

Kalau prediksi nomor 1 meleset (model 8 view tidak menang di sudut jauh), berarti diagnosis saya salah: masalahnya bukan sebaran sudut, dan harus dicari di tempat lain, misalnya resolusi grid atau jumlah iterasi.
