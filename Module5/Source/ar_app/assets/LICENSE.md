# Asal-usul dan lisensi aset AR app

Setiap aset punya satu baris provenance dengan format yang sama. `tests.py` gagal kalau file ini hilang atau ada kolom yang kosong.

```
Aset: kuda.glb | sumber: scan photogrammetry dari 28 foto saya sendiri (Source/data/my_capture/, iPhone 17 Pro, 27 Oktober 2026) dengan Apple Object Capture, diubah ke glTF oleh tools/scan_to_glb.py | pembuat: Zacky Maulana (foto, scan, ukuran); patung aslinya milik saya, pembuat patungnya tidak diketahui | lisensi: CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/) untuk foto, scan, dan model ini | dibuat: 3 November 2026 | dibuat dengan AI: tidak (photogrammetry, bukan AI generatif) | diubah: diluruskan 1,59 derajat, diskalakan ke panjang alas 46 cm, tekstur 8192 px diperkecil ke 4096 px JPEG, peta roughness diganti satu nilai
Aset: hotspots_kuda.json | sumber: posisi dihitung tools/scan_to_glb.py dari mesh kuda.glb; teks dari tools/kuda_hotspot_text.json | pembuat: Zacky Maulana | lisensi: CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/) | dibuat: 3 November 2026 | dibuat dengan AI: tidak | diubah: tidak
Aset: kuda_ukuran.json | sumber: diukur dengan tangan pada patung asli | pembuat: Zacky Maulana | lisensi: CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/) | dibuat: 3 November 2026 | dibuat dengan AI: tidak | diubah: tidak
Aset: pusaka_temple.glb dan hotspots.json | sumber: dibuat ar_app/make_temple_glb.py dari bahan Modul 5 dosen (commit a522d3c), tanpa unduhan luar | pembuat: dosen pengampu | lisensi: belum ditetapkan dengan lisensi baku (halaman starter hanya menyebut "CC0-equivalent: authored for this course") | dibuat: 6 September 2026 (README starter) | dibuat dengan AI: tidak diketahui | diubah: tidak
```

## Catatan tentang patung kuda

- **Yang pasti milik saya:** patungnya sendiri (benda fisik di rumah saya), ke-28 foto, ukurannya, hasil scan, dan semua pengolahan sesudahnya. Lisensi CC BY-NC 4.0 berlaku untuk bagian-bagian itu: siapa pun boleh memakai dan mengubahnya dengan menyebut nama saya, tetapi tidak untuk tujuan komersial.
- **Yang belum pasti:** desain patung itu karya pemahat yang tidak saya ketahui namanya. Apakah desainnya masih dilindungi hak cipta, dan apakah salinan 3D-nya boleh disebarkan, belum bisa saya pastikan (This needs verification). Inilah persoalan yang sama dengan kasus scan Nefertiti di Studi Pendahuluan Q4: memindai benda fisik tidak otomatis memberi hak atas desainnya. Saya memilih lisensi nonkomersial supaya tidak ada pihak yang mendapat keuntungan dari desain yang bukan milik saya.
- **Yang tidak di-commit:** foto asli (checksum ada di `Source/data/my_capture/sha256sums.txt`) dan scan mentah (`ar_app/scan/`, 233 MB, di-ignore). Checksum scan mentah yang dipakai: `kuda_full.usdz` sha256 `7b185243cebe9390b1b0628712227d42f2fd9ab83334943fde46138e07ac1aa9`.
