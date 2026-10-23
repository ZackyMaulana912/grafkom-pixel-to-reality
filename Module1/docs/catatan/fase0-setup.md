# Fase 0: Persiapan sebelum mengerjakan Modul 1

Sebelum mulai mengolah gambar, ada beberapa hal yang perlu dirapikan dulu. Tujuannya sederhana: supaya pekerjaan saya gampang dibedakan dari bahan dosen, supaya repo tidak penuh file yang tidak perlu, dan supaya hasilnya tetap sama kalau dijalankan ulang di laptop lain.

## Alat yang saya pakai

Saya mengerjakan modul ini di MacBook dengan macOS 27.0.1 (chip Apple Silicon). Bahasa yang dipakai Python versi 3.11.8, dengan dua library: NumPy 2.4.6 untuk semua hitungan gambar, dan Pillow 13.0.0 untuk membandingkan hasil dan menyimpan gambar ke format JPG, PNG, WebP, dan AVIF. Untuk menjalankan semuanya saya pakai `make` versi 3.81, yang sudah ada di macOS.

Saya juga sudah mengecek apakah Pillow di laptop ini bisa menyimpan gambar ke WebP dan AVIF, dan ternyata bisa. Ini penting karena di Lab 3 nanti saya membandingkan ukuran file dari keempat format itu. Kalau ada yang tidak bisa, lebih baik ketahuan sekarang daripada baru sadar di akhir.

## Apa saja yang saya siapkan

### Menyimpan bahan dosen apa adanya

Langkah pertama, saya menyimpan semua bahan awal dari dosen ke git tanpa mengubah isinya sedikit pun. Yang saya buang hanya file sampah yang dibuat otomatis oleh macOS dan sisa tes lama yang ukurannya cuma beberapa byte.

Simpanan ini saya beri penanda bernama `m1-starter`. Gunanya, nanti saya bisa menunjukkan dengan jelas bagian mana yang benar-benar saya kerjakan sendiri, cukup dengan membandingkan isi repo sekarang dengan penanda itu. Ini penting karena penilaian memberi nilai nol kalau pekerjaan saya tidak bisa dibedakan dari bahan dosen.

### Memilih file yang tidak ikut masuk repo

Tidak semua file perlu disimpan di GitHub. Ada lima jenis yang sengaja saya kecualikan:

- **File otomatis dari macOS dan Python.** Ini bukan hasil kerja, hanya catatan sementara dari sistem.
- **Folder library Python.** Isinya ratusan file yang bisa dipasang ulang kapan saja.
- **PDF materi dari dosen.** Ini bukan milik saya. Kalau sudah terlanjur tersimpan di git, menghapusnya dari riwayat itu susah, jadi lebih aman dikecualikan dari awal.
- **Folder `data`.** Isinya gambar contoh yang bisa dibuat ulang kapan saja dengan satu perintah. Nanti foto saya juga diubah ke sini dan ukurannya bisa puluhan MB, jadi tidak perlu ikut disimpan.
- **Modul 2 sampai 5.** Belum dikerjakan, jadi disembunyikan dulu supaya fokus ke Modul 1.

### Membuat ruang Python khusus untuk Modul 1

Saya membuat folder Python tersendiri untuk Modul 1, namanya `.venv`. Bayangkan seperti lemari khusus yang isinya hanya library untuk modul ini. Dengan begitu, versi library Modul 1 tidak akan bentrok dengan modul lain atau proyek lain di laptop saya.

Setelah itu saya mengatur supaya semua perintah `make` selalu memakai Python dari lemari khusus itu. Sebelumnya, `make` memakai Python mana saja yang pertama kali ditemukan di laptop, padahal belum tentu versi library-nya sama. Saya sudah mengecek bahwa perintahnya sekarang benar-benar memakai Python dari `.venv`.

Ada satu hal kecil yang sempat saya temukan saat mencoba: kalau keterangan ditulis di ujung baris pengaturan Python, ternyata ada spasi yang ikut terbawa. Jadi keterangannya saya pindah ke baris sendiri.

### Mengunci versi library

Di bahan dosen, versi library ditulis "minimal versi sekian", artinya versi yang lebih baru juga boleh. Masalahnya, versi baru bisa sedikit mengubah hasil. Misalnya kalau cara Pillow menyimpan JPG berubah, ukuran file di tabel perbandingan format saya juga bisa ikut berubah.

Karena modul ini meminta hasil yang bisa diulang, saya kunci versinya ke yang saya pakai sekarang, yaitu NumPy 2.4.6 dan Pillow 13.0.0. Untuk memastikan, saya coba memasang ulang dari nol di folder percobaan, dan versi yang terpasang memang persis sama. Folder percobaan itu lalu saya hapus.

## Hasil pengecekan awal

Setelah semua siap, saya menjalankan `make test`, yaitu kumpulan pengecekan bawaan dari dosen. Hasilnya, kesepuluh pengecekan lolos dan muncul tulisan `ALL CHECKS PASSED`.

Ini jadi titik awal saya. Kalau nanti ada pengecekan yang gagal, saya tahu penyebabnya pasti dari perubahan yang saya buat, bukan dari laptop atau versi library-nya.

Saya juga sudah menyiapkan folder untuk foto (`Source/photos/`) dan folder untuk tulisan (`docs/`). Folder yang masih kosong memang belum terlihat di GitHub sampai ada isinya.

## Pertanyaan yang mungkin muncul saat viva

**Kenapa versi library dikunci, tidak pakai yang terbaru saja?**
Supaya penilai yang menjalankan ulang di laptopnya mendapat angka yang sama persis dengan laporan saya.

**Kenapa folder `data` tidak disimpan, padahal ada di bahan dosen?**
Karena isinya bisa dibuat ulang dengan perintah `make data`, dan hasilnya selalu sama setiap kali dibuat. Git sebaiknya hanya menyimpan sumbernya, bukan hasil yang bisa dihitung ulang.

**Kenapa folder `report` tetap disimpan?**
Karena modul meminta laporan `report.html` bisa langsung dibuka penilai tanpa harus menjalankan apa pun dulu.
