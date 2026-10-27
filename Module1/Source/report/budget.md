# Modul 1 -- budget.md

Dibuat ulang oleh `python report.py` (bagian dari `make report`).
MB = 10^6 byte, GB = 10^9 byte; MiB = 2^20 byte, GiB = 2^30 byte.

## Set foto saya (resolusi asli dari kamera)

| Item | Nilai |
|---|---|
| Resolusi asli | 4536 x 8064 px, 24 foto dipakai |
| Byte per foto (RGB888) | 4536 x 8064 x 3 = 109,734,912 B = 109.7349 MB = 104.6514 MiB |
| Working set seluruh set | 109,734,912 x 24 = 2,633,637,888 B = 2511.63 MiB = 2.4528 GiB |
| Flythrough 10 s @ 30 fps | 109,734,912 x 300 = 32,920,473,600 B = 32.9205 GB = 30.6596 GiB |
| Bandwidth | 3,292,047,360 B/s = 3292.05 MB/s = 26,336.38 Mbit/s |
| Total di disk (JPG kamera) | 163,004,791 B = 163.00 MB = 155.45 MiB |
| Rasio kompresi kamera | rata-rata 16.16x; IMG_8884.jpg 18.38x (file terkecil), IMG_8897.jpg 14.93x (file terbesar) |

## Contoh E6/E7, refresh rate, dan isi data/

```
== Example E6: one 1920x1080 RGB888 frame, then 10 s @ 30 fps ==
  pixels            : 2,073,600
  bytes / frame     : 6,220,800 B  =  6.221 MB  =  5.933 MiB  =  0.0058 GiB
  10 s @ 30 fps     : 1,866,240,000 B  =  1866.240 MB  =  1779.785 MiB  =  1.7381 GiB
  bandwidth         : 178.0 MiB/s  =  1.49 Gbit/s
  (H.264 ~8 Mbit/s -> ~187x smaller than uncompressed)

== Example E7: 4096x4096 RGBA8 texture atlas ==
  no mips           : 64.0 MiB
  full mip chain    : 85.3 MiB
  fit in 8 GiB VRAM : ~96 atlases (before geometry/buffers/targets)
  200 atlases       : 16.7 GiB (> 2x an 8 GiB card -> compression + streaming)

== Refresh rate -> per-frame time budget ==
   24 Hz :  41.7 ms/frame
   60 Hz :  16.7 ms/frame
  120 Hz :   8.3 ms/frame
  144 Hz :   6.9 ms/frame

file                            WxH    decoded B    on-disk B   ratio
IMG_8878.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8879.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8882.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8883.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8884.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8886.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8887.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8889.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8890.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8892.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8893.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8894.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8895.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8896.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8897.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8899.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8900.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8901.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8902.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8903.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8904.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8905.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8906.ppm               907x1612    4,386,252    4,386,268   1.00x
IMG_8907.ppm               907x1612    4,386,252    4,386,268   1.00x
checker.pgm                 256x256       65,536       65,551   1.00x
crop_dinding.ppm            256x256      196,608      196,623   1.00x
crop_hifreq.ppm             128x128       49,152       49,167   1.00x
crop_smooth.ppm             118x118       41,772       41,787   1.00x
crop_surai.ppm              256x256      196,608      196,623   1.00x
gradient.ppm                 512x64       98,304       98,318   1.00x
gradient5.pgm                512x64       32,768       32,782   1.00x
patch8.pgm                      8x8           64           75   0.85x
photo_00.ppm                256x256      196,608      196,623   1.00x
photo_01.ppm                256x256      196,608      196,623   1.00x
photo_02.ppm                256x256      196,608      196,623   1.00x
photo_03.ppm                256x256      196,608      196,623   1.00x
photo_04.ppm                256x256      196,608      196,623   1.00x
photo_05.ppm                256x256      196,608      196,623   1.00x
photo_06.ppm                256x256      196,608      196,623   1.00x
photo_07.ppm                256x256      196,608      196,623   1.00x
photo_08.ppm                256x256      196,608      196,623   1.00x
photo_09.ppm                256x256      196,608      196,623   1.00x
relief.ppm                  256x256      196,608      196,623   1.00x
relief_rot90.ppm            256x256      196,608      196,623   1.00x
silhouette.pgm              256x256       65,536       65,551   1.00x
silhouette_flip.pgm         256x256       65,536       65,551   1.00x
thumb_buggy.ppm             128x128       49,152       49,167   1.00x
--------------------------------------------------------------------
SET TOTAL                            108,490,380  108,491,103   1.00x
decoded working set: 103.46 MiB   (at 4000x3000 RGB each: 1614 MiB)

```
