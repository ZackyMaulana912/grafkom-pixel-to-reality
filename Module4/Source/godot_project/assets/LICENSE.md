# Sumber dan lisensi aset

Semua aset di folder ini boleh disebarkan ulang. Ukuran totalnya sekitar 4 MB.

## `ruangan/`: model ruangan patung kuda (milik saya)

| File | Asal | Lisensi |
|---|---|---|
| `mymodel.obj` | Disalin tanpa diubah dari `Module3/Source/data/mymodel.obj` (dibuat oleh `Module3/Source/make_mymodel.py` dari ukuran ruangan saya). SHA-256 sama: `dda3a167e8c841a995838d2a6f8c656013c07abfb658fb1fffc2f6f79271e31c` | karya saya sendiri |
| `mymodel_tex.png` | `Module3/Source/data/mymodel_tex.ppm` disimpan ulang sebagai PNG (Godot tidak bisa mengimpor PPM). Isi pixel identik, 512 × 512, dicek dengan Pillow | foto saya sendiri |

## `kaykit/`: karakter Knight

| | |
|---|---|
| Nama | KayKit : Adventurers Character Pack (1.0), karakter Knight |
| Pembuat | Kay Lousberg (www.kaylousberg.com) |
| Sumber | https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0, file `addons/kaykit_character_pack_adventures/Characters/gltf/Knight.glb`, commit `672074b73ba276876a19e8816ecdc5241817ab47` (16 September 2023) |
| Lisensi | Creative Commons Zero (CC0). Teks lengkapnya ada di `kaykit/LICENSE.txt`, yang saya unduh dari repo yang sama. Isinya: "This content is free to use in personal, educational and commercial projects", dan kredit tidak wajib |
| Tanggal unduh | 30 Oktober 2026 |
| Ukuran | `Knight.glb` 3.659.532 byte, SHA-256 `60428e3abc09ba83e595d256e3af8c5c976b46cdae599f0802fc82b4a3445168` |
| Isi | 1 skeleton dengan 41 tulang, 76 animasi (termasuk `Idle` dan `Walking_A`), texture tertanam |

`Knight_knight_texture.png` bukan unduhan terpisah. File itu dikeluarkan Godot sendiri dari texture yang tertanam di `Knight.glb` saat impor, dan ikut di-commit supaya proyek yang baru di-clone tidak perlu membuatnya ulang.
