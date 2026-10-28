# Fase 0: Setup repo, npm, dan toolchain

Tujuan fase ini: bahan dari dosen masuk git apa adanya, versi library terkunci, test starter hijau, dan server lokal hanya bisa dibuka dari laptop saya sendiri.

## Toolchain (Lab 1 no 1)

Dicatat 28 Oktober 2026.

| Komponen | Versi |
|---|---|
| Komputer | Mac model Mac17,2, chip Apple M5 |
| OS | macOS 27.0.1 (build 26A434) |
| Node | v22.23.4, dipasang lewat nvm. Versinya dikunci di `Source/.nvmrc` |
| npm | 10.9.9 |
| Three.js | 0.160.0 (sama dengan importmap di `web/index.html`) |
| serve | 14.2.6 |
| Browser untuk uji otomatis | Google Chrome 156.0.8078.48, mode tanpa layar (headless), WebGL lewat ANGLE Metal di GPU Apple M5 |
| Browser yang saya buka sendiri | _diisi setelah saya membuka halaman GitHub Pages_ |

Kenapa Node 22: di Mac saya sebelumnya hanya ada Node v20.20.2, sedangkan dosen memverifikasi starter di Node v22.19.0. Node 20 juga sudah habis masa dukungannya (April 2026). Node 22 saya pasang lewat nvm tanpa mengubah default nvm, jadi proyek lain yang memakai Node 20 tidak terganggu. Di folder `Module2/Source`, perintah `nvm use` otomatis memilih versi dari `.nvmrc`.

## Langkah dan buktinya

1. **Folder Modul 2 dibuka di `.gitignore` root.** Selama Modul 1, `/Module2/` sampai `/Module5/` sengaja disembunyikan. Baris `/Module2/` saya buang, sedangkan Modul 3 sampai 5 tetap tersembunyi.
2. **Yang tidak boleh masuk git terbukti tidak masuk** (`git check-ignore -v`):
   - file panduan pribadi saya di folder `Module2/` tertangkap `.git/info/exclude`, yang hanya berlaku di laptop saya dan tidak ikut ter-commit,
   - `Module2/Module2_ID.pdf` tertangkap `.gitignore` root (`Module*/*.pdf`),
   - `Module2/Source/out/...` tertangkap `Module2/Source/.gitignore` bawaan starter (`out/`),
   - `node_modules/` dan `plan_three.ppm` juga tertangkap `.gitignore` starter.
3. **Commit pertama berisi starter apa adanya**, yaitu `123b344`. Semua pekerjaan saya bisa dilihat dengan `git diff 123b344`.
4. **Test starter hijau di Mac saya:** `ALL CHECKS PASSED (10 ok, 0 fail)`. Contoh terpandu juga sama dengan PDF: tanpa aturan ada 6 pixel dobel, dengan `> 0` ada 6 celah, dan dengan aturan 36/0/0, cocok 144/144 dengan `ref/square_fill_ref.ppm`.

## Mengunci versi library

Starter menulis `"three": ">=0.160.0"` dan `"serve": ">=14.0.0"`. Artinya `npm install` bisa memasang versi apa pun yang lebih baru, padahal halaman web memuat Three.js **0.160.0** dari CDN. Saya mengubahnya menjadi versi pasti:

```
npm install --save-dev --save-exact three@0.160.0 serve
```

`package-lock.json` ikut di-commit, karena tanpa file itu `npm ci` di clone baru tidak bisa jalan.

**Celah keamanan di `serve`.** `npm audit` melaporkan 2 temuan "high" pada `compression` 1.8.1, library yang dipakai `serve` (DoS lewat kebocoran memori). Saran otomatis npm adalah menurunkan `serve` ke versi 10, padahal itu perubahan besar. Saya memilih jalan yang lebih kecil: `"overrides": { "compression": "1.8.2" }`, yaitu versi perbaikan dari library yang sama. Hasil `npm audit` setelahnya: `found 0 vulnerabilities`. Risiko aslinya memang kecil, karena server ini hanya hidup di laptop saya, tapi tidak ada alasan membiarkannya.

## Server lokal (temuan T5 dan dua temuan baru)

Script starter `"serve": "npx --yes serve web"` punya tiga masalah:

1. **Halaman tidak bisa memuat denah (T5).** Yang dilayani hanya folder `web/`, padahal viewer mengambil `../pusaka_plan.json` dari folder induknya. Solusinya: layani folder `Source/` (`.`) dan buka `/web/`.
2. **Terbuka ke seluruh jaringan.** Menurut `serve --help`, default-nya mendengarkan di `0.0.0.0:3000`, jadi laptop lain di WiFi yang sama bisa membukanya. Solusinya: `-l tcp://127.0.0.1:...`.
3. **`--yes` boleh mengunduh package tanpa bertanya.** Sekarang `serve` dipasang lokal dan versinya terkunci.

Saat menguji di Mac saya, ada dua hal lagi:

- **Port 3000 sudah dipakai program lain** di laptop saya (`gowa`). Program itu bukan bagian proyek ini, jadi tidak saya sentuh.
- **`serve` diam-diam pindah ke port acak** (`http://localhost:58924`) kalau port yang diminta sedang dipakai, dan menyalin alamatnya ke clipboard. Akibatnya tidak ada error sama sekali, dan alamat yang ditulis di README menjadi salah tanpa ketahuan.

Script akhirnya:

```
"serve": "serve -l tcp://127.0.0.1:4173 --no-port-switching --no-clipboard ."
```

Bukti dari run: `curl` ke `/web/`, `/web/viewer.mjs`, dan `/pusaka_plan.json` memberi 200 (dengan content type `text/html`, `application/javascript`, dan `application/json`). `lsof` menunjukkan server hanya mendengarkan di `127.0.0.1:4173`. Server dimatikan setelah uji.

Halaman dibuka di **http://127.0.0.1:4173/web/**.
