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

## Uji ulang 31 Oktober 2026, setelah tujuh commit tambahan

Setelah commit hari ini di-push (spline tertutup, kamera memutari patung penuh, FABRIK, dan asal matriks buta warna di Modul 1 dan 2), saya mengulang uji dari clone GitHub yang baru, kali ini untuk keempat modul (commit `3f30c76`):

| Modul | Perintah | Hasil |
|---|---|---|
| 1 | `pip install -r requirements.txt`, `make data`, `make test`, `make report` | numpy 2.4.6 dan pillow 13.0.0, ALL CHECKS PASSED (17/17), `git status` bersih: semua file `data/` dan `report/` yang dibuat ulang identik dengan yang di-commit |
| 2 | `nvm use`, `npm ci`, `npm test`, `npm run plan` | Node 22.23.4, 23 ok, `git status` bersih |
| 3 | `pip install`, `make_model.py`, `tests.py` | 17 ok, `git status` bersih |
| 4 | `pip install`, `tests.py`, impor dan run Godot 300 frame, `godot_check.py`, `fabrik.py` | `pip freeze` sama dengan `requirements.txt`, 171 ok, Godot kode 0 tanpa error atau missing script, 13 baris cocok (kurva tertutup 61 titik), `git status` bersih |

Ini pertama kalinya Modul 1 diuji dari clone GitHub. Sebelumnya README Modul 1 masih mencatatnya sebagai "not yet verified".

GitHub Pages: deploy commit `3f30c76` sukses. Keempat file build Web identik dengan repo. Di Chrome tanpa jendela tidak ada error console, dan kurva tertutup yang dicetak di browser cocok dengan Python. Halaman Modul 2 dan 3 tetap memberi status 200.

**Temuan baru: `npm audit` di Modul 2.** Tanggal 28 Oktober `npm ci` melaporkan 0 kerentanan. Sekarang ada 3 laporan tingkat moderate dari satu advisory, GHSA-g3hv-75wg-m249 (minimatch di bawah 11.0.1, kemungkinan denial of service), yang baru terbit 30 Oktober 2026 pukul 23:09 UTC. Paket itu masuk lewat `serve-handler` di dependensi `serve`, yang hanya dipakai untuk `npm run serve`, yaitu server lokal di `127.0.0.1`. Halaman Pages tidak memakai Node sama sekali. Perbaikan yang disarankan npm (`npm audit fix --force`) justru menurunkan `serve` ke versi 6.5.8, sebuah breaking change. Jadi dependensinya tidak saya ubah, dan temuan ini saya catat di baris Verified Modul 2.

Folder clone uji dihapus setelah transkrip ini dicatat.

## Uji ulang 1 November 2026, dari clone lokal

Perubahan hari ini:
- Modul 2: paket `serve` diganti `serve.mjs` tanpa dependensi;
- Modul 4: batas sendi di FABRIK, dan Knight berbalik bertumpu pada kaki yang menapak.

Saat uji ini, commit terakhir (`cf0ad24`) dan dua commit berikutnya belum di-push. Jadi saya meng-clone repo lokal ke folder sementara, lalu menerapkan perubahan yang belum di-commit dengan `git apply`. Yang diuji adalah isi file yang akan masuk ke repo, tanpa `.venv`, `node_modules`, Module5, atau file pribadi. **Ini belum uji dari GitHub dan GitHub Pages.** Uji itu baru bisa dilakukan setelah push.

| Modul | Perintah | Hasil |
|---|---|---|
| 1 | `.venv` baru, `pip install -r requirements.txt`, `make data`, `make test`, `make report` | 17 baris OK, ALL CHECKS PASSED |
| 2 | `nvm use`, `npm ci`, `npm test`, `npm run plan`, `npm audit` | Node 22.23.4, `npm ci` hanya memasang 1 paket (`three`), **0 vulnerabilities**, 25 ok |
| 3 | `.venv` baru, `pip install`, `make_model.py`, `tests.py` | 17 ok |
| 4 | `.venv` baru, `pip install`, `tests.py`, impor dan run Godot 300 frame, `godot_check.py`, `cek_knight.gd`, `fabrik.py` | `pip freeze` sama dengan `requirements.txt`, 177 ok, impor dan run kode 0 tanpa error atau warning, 13 baris cocok, `KNIGHT_WALK` dan `KNIGHT_TURN` lolos (8,9e-8 m per putaran), `fabrik.py` menunjukkan jebakan dan perbaikannya |

Setelah semua perintah itu, `git status` di clone tidak menunjukkan perubahan apa pun selain perubahan yang diterapkan. Artinya semua file yang dibuat ulang (data dan laporan Modul 1, model Modul 3, cache impor Godot) identik dengan isi repo, atau memang di-ignore.

Temuan `npm audit` dari 31 Oktober sudah selesai: dengan `serve` dihapus, Modul 2 hanya punya satu paket dan tidak ada kerentanan yang dilaporkan.

Folder clone uji dihapus setelah transkrip ini dicatat.
