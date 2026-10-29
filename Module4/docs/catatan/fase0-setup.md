# Fase 0: Setup repo, venv, toolchain, dan Godot

Tujuan fase ini: bahan dari dosen masuk git apa adanya, kode dosen dijalankan di Mac saya sebelum diubah sedikit pun, versi library terkunci, dan proyek Godot terbukti bisa dibuka dan dijalankan tanpa error.

## Toolchain (Lab 1 no 1)

Dicatat 30 Oktober 2026.

| Komponen | Versi |
|---|---|
| Komputer | Mac model Mac17,2, chip Apple M5 (arm64) |
| OS | macOS 27.0.1 (build 26A434) |
| Python | 3.11.8 (pyenv), di `.venv` milik `Module4/Source` |
| matplotlib | 3.11.2 (hanya untuk `figures.py`, bukan untuk hitungan) |
| Godot | 4.7.2 stable (`4.7.2.stable.official.ed1daf0bf`), dipasang lewat Homebrew, binary di `/Applications/Godot.app/Contents/MacOS/Godot` |
| Export template Godot | belum terpasang (baru dibutuhkan di Fase 5) |

Di catatan dan laporan, binary Godot itu saya sebut `$GODOT`.

## Langkah dan buktinya

1. **Folder Modul 4 dibuka di `.gitignore` root.** Baris `/Module4/` saya buang, sedangkan Modul 5 tetap tersembunyi. Saya juga menambahkan dua pola baru:
   - `.godot/`, yaitu cache editor Godot. Isinya hasil impor yang selalu bisa dibuat ulang, jadi tidak perlu disimpan;
   - `Module4/build/`, tempat hasil ekspor game nanti. Folder ini baru dibuka kalau saya memilih menaruh build di repo (Fase 5).
2. **Yang tidak boleh masuk git terbukti tidak masuk** (`git check-ignore -v`):
   - file panduan pribadi saya di `Module4/` tertangkap `.git/info/exclude`, yang tidak ikut ter-commit;
   - `Module4/Module4_ID.pdf` tertangkap `.gitignore` root (`Module*/*.pdf`);
   - `godot_project/.godot/` tertangkap pola `.godot/`;
   - `Module4/build/` tertangkap pola `Module4/build/`;
   - `Source/.venv/` tertangkap `.venv/`;
   - file `.gd.uid` **tidak** tertangkap, dan memang harus begitu. File kecil ini dipakai Godot 4.4 ke atas untuk mengenali script lewat nomor unik, jadi ia bagian dari proyek, bukan sampah.
3. **Commit pertama berisi starter apa adanya** (`8b7ff5d`). Semua pekerjaan saya nanti bisa dilihat dengan `git diff 8b7ff5d`.
4. **Kode dosen dijalankan sebelum diubah:**

   ```
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python fk.py
   .venv/bin/python ik.py
   .venv/bin/python spline.py
   .venv/bin/python quaternion.py
   .venv/bin/python foot_slide_bug.py
   .venv/bin/python tests.py          # 40 baris [ok], 0 FAIL, ALL CHECKS PASSED (40 ok)
   ```

   Semua keluar dengan kode 0. `.venv/bin/python -c "import sys; print(sys.prefix)"` menunjuk ke `Module4/Source/.venv`, jadi library tidak tercampur dengan Python laptop.

## Hasil kode dosen di Mac saya

| Script | Hasil di Mac | Di PDF |
|---|---|---|
| `fk.py` | siku (2.598, 1.500) sudut global 30.0, tangan (2.598, 3.500) sudut global 90.0 | sama |
| `ik.py` | theta1 -13.18, theta2 70.53, FK kembali ke (4.000, 1.000), error **4.44e-16** | sama |
| `spline.py` | q(0.5) = (3.000, 1.000), 5 titik kontrol jadi 41 sampel, (8, 3, 0) sampai (-8, 3, 0) | sama |
| `quaternion.py` | slerp (0.9511, 0.0000, 0.3090, 0.0000), sudut 36.00, selisih gimbal 1.11e-16 dan 1.06e-17 | sama |
| `foot_slide_bug.py` | celah setelah 5 detik: 2.50 m (buggy), 0.00 m (fixed) | sama |
| `tests.py` | ALL CHECKS PASSED (40 ok) | sama |

Satu hal kecil yang menarik: sebelum mulai, starter ini pernah dijalankan di komputer Linux dengan Python 3.13, dan di sana `ik.py` mencetak error `0.00e+00`. Di Mac saya hasilnya `4.44e-16`, sama dengan PDF. Angka `4.44e-16` itu dua kali epsilon float 64-bit (2 x 2.22e-16), jadi selisih sekecil ini hanyalah pembulatan float yang sedikit berbeda antar komputer. Dugaan saya penyebabnya implementasi `sin`, `cos`, dan `acos` di pustaka matematika tiap OS, tapi ini belum saya buktikan. Yang penting, keduanya jauh di bawah batas `1e-9` yang dipakai test.

## Mengunci versi library (K6)

Starter menulis `matplotlib>=3.7` dan `numpy>=1.24`, jadi `pip install` bisa memasang versi apa pun yang lebih baru. Starter juga menyebut keduanya hanya untuk `make_figures_m4.py`, padahal file itu tidak ada di zip. Saya menguncinya ke versi yang benar-benar terpasang di `.venv`, termasuk library yang ikut terpasang bersama matplotlib:

```
contourpy==1.3.3       cycler==0.12.1       fonttools==4.68.0
kiwisolver==1.5.1      matplotlib==3.11.2   numpy==2.4.6
packaging==26.3        pillow==13.0.0       pyparsing==3.3.3
python-dateutil==3.0.0 six==1.17.0          tzdata==2026.6
```

Saya buktikan file ini bisa dipasang ulang dari nol: di venv baru yang terpisah, `pip freeze` menghasilkan tepat 12 baris yang sama dengan isi `requirements.txt`. Lalu venv uji itu saya hapus.

matplotlib hanya akan dipakai `figures.py` untuk menggambar PNG di README. Kode hitungan (`fk.py`, `ik.py`, `spline.py`, `quaternion.py`, `foot_slide_bug.py`) tetap hanya memakai standard library Python, dan di Fase 3 aturan ini akan dicek otomatis oleh test.

## Godot headless

"Headless" artinya Godot dijalankan tanpa jendela. Cara ini cocok untuk membuktikan scene bisa dimuat dan dijalankan tanpa error, tapi **tidak** membuktikan tampilannya benar. Tampilan baru terbukti setelah saya membukanya sendiri di editor.

```
$GODOT --version
4.7.2.stable.official.ed1daf0bf

$GODOT --headless --path godot_project --quit-after 300
Godot Engine v4.7.2.stable.official.ed1daf0bf - https://godotengine.org
(kode keluar 0)
```

Log-nya hanya baris pembuka itu, tanpa error, tanpa warning, dan tanpa "missing script". Saya menjalankannya tiga kali (dua kali di salinan proyek, sekali di folder repo). Setelah run di folder repo, `git status` tidak menunjukkan file proyek yang berubah, dan Godot juga tidak membuat folder `.godot/`.

Log kosong saja belum membuktikan script benar-benar berjalan. Jadi di **salinan** proyek (bukan di repo) saya pasang script pemeriksa kecil sebagai autoload, yaitu script yang otomatis ikut dimuat setiap kali game jalan. Pada frame ke-299 script itu mencetak isi scene:

```
PROBE scene=Main nodes=62 camera=PathCamera curve_points=41 first=(8.0, 3.0, 0.0) last=(-8.0, 3.0, 0.0)
PROBE arm_children=3 walker_children=2 temple_children=5 gimbal_children=2
```

Artinya kelima script benar-benar menjalankan `_ready()` dan membangun objeknya (file `Main.tscn` hanya berisi 10 node, sisanya dibuat oleh script), kamera yang aktif adalah kamera spline, dan kurvanya berisi 41 titik dari (8, 3, 0) sampai (-8, 3, 0), sama dengan `spline.py`. Demo gimbal lock hanya punya 2 anak, padahal komentar script-nya menyebut tiga kubus. Ini dibahas di Fase 5 (T4).

## Yang belum

- Export template Godot belum dipasang. Baru dibutuhkan di Fase 5, dan saya sendiri yang mengunduhnya.
- Membuka proyek di editor Godot dengan mata saya sendiri, lalu mencatat apakah editor mengubah file, dilakukan di Fase 5 sebelum scene diubah.
- Folder `docs/` lain (`img/`, `rantai/`, `studi-pendahuluan/`, `prediksi/`, `laporan/`) baru muncul di git saat diisi, karena git tidak menyimpan folder kosong.
