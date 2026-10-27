# Downscale 2x: naive and Pillow BOX against the linear-correct result

| image | method | PSNR | SSIM | mean abs diff | max abs diff | darker by (mean) |
|---|---|---|---|---|---|---|
| IMG_8884.ppm | naive (sRGB codes) | 52.24 dB | 0.9999 | 0.18 | 27 | +0.18 |
| IMG_8884.ppm | Pillow Image.BOX | 51.42 dB | 0.9999 | 0.29 | 26 | -0.21 |
| IMG_8884.ppm | Pillow BOX vs naive | 52.24 dB | 1.0000 | 0.39 | 1 | -0.39 |
| IMG_8893.ppm | naive (sRGB codes) | 52.77 dB | 1.0000 | 0.20 | 24 | +0.20 |
| IMG_8893.ppm | Pillow Image.BOX | 51.45 dB | 1.0000 | 0.35 | 23 | -0.27 |
| IMG_8893.ppm | Pillow BOX vs naive | 51.45 dB | 1.0000 | 0.47 | 1 | -0.47 |
| relief.ppm | naive (sRGB codes) | 21.48 dB | 0.9623 | 20.25 | 42 | +20.25 |
| relief.ppm | Pillow Image.BOX | 21.68 dB | 0.9627 | 19.74 | 41 | +19.74 |
| relief.ppm | Pillow BOX vs naive | 51.11 dB | 0.9999 | 0.50 | 1 | -0.50 |
