# Prediksi: hotspot mana yang paling sulit disembunyikan dengan benar (Lab 3 no 2)

Ditulis 3 November 2026, **sebelum** pengujian occlusion dijalankan. File ini di-commit dulu, baru pengujiannya.

**Yang sudah saya ketahui sebelumnya:**
- posisi dan normal kelima hotspot (`assets/hotspots_kuda.json`);
- satu screenshot dari sudut kamera default (`0deg 80deg`), di mana kelima hotspot terlihat;
- isi `style.css` dan dokumentasi `<model-viewer>` yang saya baca di Studi Pendahuluan.

Saya belum pernah memutar kamera ke sudut lain sambil melihat hotspot.

## 1. Dugaan cara kerja `<model-viewer>`

Dokumentasi yang saya baca menyebut hotspot diletakkan dengan `data-position` dan `data-normal`, dan ada variabel CSS `--min-hotspot-opacity` (default 0,25) untuk "hotspot yang tersembunyi". Dokumentasi itu tidak menjelaskan **bagaimana** `<model-viewer>` memutuskan sebuah hotspot tersembunyi. Dugaan saya:

- **D1.** Keputusannya hanya dari normal. Hotspot dianggap terlihat kalau normalnya menghadap kamera, tanpa mengecek apakah ada bagian model lain di antara hotspot dan kamera.
- **D2.** Hotspot yang "tersembunyi" tidak hilang, hanya diredupkan ke opacity sekitar 0,25. `style.css` starter punya aturan `.hotspot.hidden { display: none; }`, tetapi yang saya baca di dokumentasi tidak pernah menyebut class `hidden`. Jadi aturan itu kemungkinan tidak pernah aktif.

## 2. Prediksi

Normal kelima hotspot semuanya menghadap ke depan model (komponen z antara 0,81 dan 1,00), karena ray penempatnya ditembakkan dari depan. Dari situ:

1. **Dari kamera default (`0deg 80deg`), kelima hotspot terlihat, dan memang benar terlihat.** Ini sudah terlihat di screenshot.
2. **Dari belakang (sekitar `180deg 75deg`), kelima hotspot dianggap tersembunyi**, karena semua normalnya membelakangi kamera. Itu benar secara geometri. Akibatnya, dari belakang tidak ada hotspot yang jelas terlihat dan bisa diketuk.
3. **Yang paling sulit: hotspot surai (`surai`).** Titiknya di surai, `z = -0,010`, sekitar 6 cm di belakang bidang depan kepala dan leher (hotspot kepala ada di `z = 0,055`). Kalau kamera berputar ke sisi kepala (azimuth positif, ke arah +x), leher dan kepala akan berada di antara titik surai dan kamera. Normal surai `(-0,18; 0,22; 0,96)` baru membelakangi kamera kalau azimuth di atas sekitar 79 derajat. Perkiraan kasar saya: leher mulai menutupi titik itu sekitar azimuth 55 derajat. Lebar dan tebal leher ini saya kira-kira dari gambar, tidak saya ukur. Jadi saya prediksi **ada rentang sekitar 55 sampai 79 derajat** (contoh: `65deg 75deg`) di mana hotspot surai tetap tampak penuh dan bisa diketuk, padahal titiknya tertutup leher. Hotspotnya akan terlihat "melayang" di depan leher.
4. **Hotspot kaki, alas, kepala, dan ekor hampir selalu benar.** Keempatnya berada di bagian paling depan atau paling ujung model, jadi hampir tidak ada bagian lain yang bisa berada di depannya saat normalnya masih menghadap kamera. Kalau ada kesalahan, paling-paling hanya beberapa derajat di sekitar sudut tempat normalnya mulai membelakangi kamera.
5. **Dari atas (polar kecil, misalnya `0deg 25deg`)**, hotspot kaki (normalnya agak ke bawah, `y = -0,36`) dianggap tersembunyi. Itu benar, karena kaki menutupi sisi bawahnya sendiri.
6. **Kalau D2 benar,** hotspot yang tersembunyi masih terlihat samar (sekitar 25%) dan mungkin masih bisa diketuk.

## 3. Cara menguji (setelah file ini di-commit)

- **Yang dikatakan `<model-viewer>`:** Playwright memutar `camera-orbit` setiap 5 derajat di sekeliling model (polar 75 derajat), ditambah beberapa sudut dari atas. Di setiap sudut, dicatat atribut yang dipasang `<model-viewer>` pada tiap hotspot, beserta opacity yang benar-benar dipakai browser.
- **Kebenaran geometri:** dari setiap hotspot, ditembakkan ray ke posisi kamera dan dicek apakah ray itu menabrak mesh `kuda.glb` lebih dulu. Ray yang sama dengan Fase 2 dan 3, kali ini untuk mengecek terlihat atau tidak.
- **Rekonsiliasi:** dibandingkan sudut per sudut, mana yang cocok, mana yang tampil padahal tertutup, dan mana yang disembunyikan padahal terlihat. Lalu dibandingkan dengan prediksi di atas: mana yang tepat, mana yang meleset, dan kenapa.
