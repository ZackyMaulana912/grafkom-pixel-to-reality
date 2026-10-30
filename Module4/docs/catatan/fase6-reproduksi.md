# Fase 6: Reproduksi dari clone bersih dan uji GitHub Pages (Lab 3 no 5, A5)

Diuji 30 Oktober 2026 di Mac yang sama (Apple M5, macOS 27.0.1), dari GitHub, bukan dari folder kerja saya.

## Clone bersih

```
$ git clone https://github.com/ZackyMaulana912/grafkom-pixel-to-reality.git <folder sementara>
$ git log --oneline -1
418d846 "Ukur prediksi Euler vs quaternion di rig lengan saya ...
$ cd Module4/Source
$ python3 -m venv .venv
$ .venv/bin/python -m pip install -r requirements.txt
$ .venv/bin/python -m pip freeze          # sama persis dengan isi requirements.txt (12 paket)
$ .venv/bin/python tests.py
ALL CHECKS PASSED (134 ok)
$ $GODOT --headless --editor --path godot_project --quit            # impor semua aset: kode 0, 0 error/warning
$ $GODOT --headless --path godot_project --quit-after 300           # kode 0, 0 error/warning/missing script
$ $GODOT --headless --path godot_project --quit-after 300 | .venv/bin/python godot_check.py
13 baris dibandingkan, 0 di atas toleransinya
$ git status --short                                                # kosong
```

Artinya:
- dari clone baru dengan `.venv` baru, test hijau;
- proyek Godot terbuka di Godot 4.7.2 tanpa error missing-script, dan scene berjalan 300 frame;
- angka yang dicetak scene (FK/IK lengan, kurva kamera, kubus gimbal, rig lengan saya) sama dengan Python;
- editor tidak mengubah satu pun file yang dilacak git.

File panduan pribadi saya (yang di-ignore lewat `.git/info/exclude`) memang tidak ikut ter-clone, dan tidak saya salin ke folder uji. Folder uji dihapus setelah transkrip ini dicatat.

## Build Web di GitHub Pages

URL: https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module4/build/web/

| File | Status | MIME | Sama dengan file di repo |
|---|---|---|---|
| `index.html` | 200 | `text/html` | ya (SHA-256) |
| `index.js` | 200 | `application/javascript` | ya |
| `index.wasm` | 200 | `application/wasm` | ya |
| `index.pck` | 200 | `application/octet-stream` | ya |

Dibuka dengan Google Chrome 156 tanpa jendela (lewat Chrome DevTools Protocol, ditunggu 50 detik):
- WebGL 2.0 lewat ANGLE Metal di Apple M5;
- Godot mencetak `Compatibility - Using Device: WebKit - WebKit WebGL`;
- 0 exception dan 0 error di console;
- baris pengecekan dari console browser lewat `godot_check.py`: `13 baris dibandingkan, 0 di atas toleransinya`;
- screenshot memperlihatkan ruangan, patung, rig lengan saya, dan Knight.

Build yang sama juga saya buka sendiri di **Safari 27.0.1** (dari server lokal `127.0.0.1:8000`), dan berjalan dengan baik.

## Temuan: ekspor dari impor baru tidak identik byte per byte

Saya juga mengekspor ulang build Web dari clone, lalu membandingkannya dengan build yang di-commit. `index.wasm` dan `index.js` identik, tetapi `index.pck` dan `index.html` (yang menyimpan ukuran pck) berbeda. Daftar isi pck saya baca langsung dari formatnya (versi format 4, Godot 4.7.2, 32 file). Dari 32 file, hanya dua yang berbeda:

- hasil impor `Knight.glb` (`.godot/imported/Knight.glb-....scn`);
- `Main.scn` yang diekspor.

Untuk memastikan penyebabnya bukan perbedaan isi repo, saya mengambil isi commit yang sama ke dua folder bersih, mengimpor dari nol, dan mengekspor masing-masing. Kedua hasilnya **juga** berbeda satu sama lain, di dua file yang sama. Hasil impor Knight hanya berbeda 89 byte dari 1,3 MB, dan `Main.scn` 56 byte. Semuanya di bagian akhir file, dan ada string pendek acak (misalnya `Dmc3/`) yang hanya muncul di salah satunya. Dugaan kuat saya, Godot memberi id acak pada sub-resource setiap kali menyimpan hasil impor. Ini belum saya pastikan dari kode sumber Godot.

Jadi klaim saya di Fase 5 perlu dipersempit: **ekspor ulang identik byte per byte selama cache impor (`.godot/`) sama**, seperti dua ekspor di laptop saya. Setelah impor dari nol, dua resource itu berbeda di beberapa byte. Perilakunya tetap sama: angka yang dicetak build dari clone cocok dengan Python sama seperti build yang di-commit. Untuk hosting, akibatnya kecil. `index.wasm` (39,5 MB) adalah template engine dan selalu identik, jadi yang berubah saat build ulang hanya `index.pck` (1,6 MB).

## Belum diuji

- Komputer lain, Windows, Linux, dan GPU selain Apple M5.
- Membuka `godot_project/` di jendela editor Godot dengan mata saya sendiri dari clone ini. Impornya sudah dicek tanpa jendela.
