# Global SSIM vs windowed SSIM (Wang et al. 2004: 11x11 Gaussian, sigma 1.5)

- crop_dinding: median local standard deviation 0.51 codes (sqrt(C2) = 7.65)
- crop_surai: median local standard deviation 6.33 codes (sqrt(C2) = 7.65)

| crop | format | PSNR | SSIM global | SSIM windowed | worst local SSIM | texture kept |
|---|---|---|---|---|---|---|
| crop_dinding | JPG q92 | 52.1 dB | 0.9984 | 0.9946 | 0.9620 | 95% |
| crop_dinding | WebP q92 | 48.2 dB | 0.9963 | 0.9930 | 0.9519 | 71% |
| crop_dinding | JPG q75 | 50.0 dB | 0.9975 | 0.9933 | 0.9474 | 64% |
| crop_dinding | JPG q40 | 44.7 dB | 0.9913 | 0.9906 | 0.9343 | 12% |
| crop_dinding | AVIF q40 | 46.6 dB | 0.9942 | 0.9933 | 0.9178 | 49% |
| crop_surai | JPG q92 | 40.5 dB | 0.9979 | 0.9674 | 0.8188 | 100% |
| crop_surai | WebP q92 | 41.2 dB | 0.9982 | 0.9732 | 0.9021 | 99% |
| crop_surai | JPG q75 | 36.8 dB | 0.9950 | 0.9298 | 0.6702 | 99% |
| crop_surai | JPG q40 | 33.9 dB | 0.9901 | 0.8751 | 0.5483 | 96% |
| crop_surai | AVIF q40 | 33.8 dB | 0.9898 | 0.8605 | 0.3747 | 83% |
