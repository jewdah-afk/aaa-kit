# vfxbench results

Fastest of 3 runs per mode. Luau CLI 0.740, -O2 unless noted. ms per call.
x = speed-up vs the first row of the group in the same mode. Output: checksum (or mean, ≈) matches the first row.

| Group | Variant | interp-O2 ms | x | native-O2 ms | x | interp-O1 ms | x | native gain | output |
|---|---|---|---|---|---|---|---|---|---|
| 01 clear 480x270 to a colour | writeu32 per pixel | 1.295 | 1.0 | 0.283 | 1.0 | 1.298 | 1.0 | 4.6 | reference |
|  | doubling buffer.copy (log2 N copies) | 0.009 | 143.9 | 0.009 | 31.4 | 0.009 | 144.2 | 1.0 | same |
|  | copy from a prebuilt clear buffer | 0.009 | 143.9 | 0.009 | 31.4 | 0.009 | 144.2 | 1.0 | same |
| 02 clear 480x270 to transparent black | writeu32 per pixel | 1.369 | 1.0 | 0.273 | 1.0 | 1.379 | 1.0 | 5.0 | reference |
|  | buffer.fill(b, 0, 0) | 0.008 | 171.1 | 0.008 | 34.1 | 0.008 | 172.4 | 1.0 | same |
| 03 write a gradient pixel (pack) | 4x writeu8 | 5.033 | 1.0 | 0.516 | 1.0 | 5.397 | 1.0 | 9.8 | reference |
|  | 1x writeu32, arithmetic pack | 2.657 | 1.9 | 0.436 | 1.2 | 2.688 | 2.0 | 6.1 | same |
|  | 1x writeu32, bit32 pack | 4.314 | 1.2 | 0.359 | 1.4 | 4.490 | 1.2 | 12.0 | same |
| 04 additive blend 256x256 (saturating) | per channel: readu8 + math.min | 6.010 | 1.0 | 0.834 | 1.0 | 6.953 | 1.0 | 7.2 | reference |
|  | per channel: saturation LUT | 7.708 | 0.8 | 1.452 | 0.6 | 7.242 | 1.0 | 5.3 | same |
|  | SWAR: 2 channels per add (bit32) | 5.558 | 1.1 | 0.265 | 3.1 | 6.151 | 1.1 | 21.0 | same |
|  | SWAR, skip where glow is 0 (sparse) | 5.630 | 1.1 | 0.398 | 2.1 | 6.059 | 1.1 | 14.1 | same |
| 05 alpha blend 256x256 (layer opacity) | per channel: readu8 x2, writeu8 | 8.498 | 1.0 | 0.884 | 1.0 | 8.346 | 1.0 | 9.6 | reference |
|  | SWAR: 2 channels per multiply | 5.049 | 1.7 | 0.268 | 3.3 | 4.200 | 2.0 | 18.8 | same |
| 06 index->RGBA resolve 480x270 | compute colour per pixel | 3.921 | 1.0 | 0.512 | 1.0 | 3.865 | 1.0 | 7.7 | reference |
|  | palette in a Luau table | 2.711 | 1.4 | 0.625 | 0.8 | 2.924 | 1.3 | 4.3 | same |
|  | palette in a buffer (readu32) | 2.710 | 1.4 | 0.484 | 1.1 | 3.154 | 1.2 | 5.6 | same |
|  | 4 indices per readu32 | 2.317 | 1.7 | 0.336 | 1.5 | 2.404 | 1.6 | 6.9 | same |
| 07 box blur 256x256 u8, radius 8 | naive 2D (289 taps/px) | 485.889 | 1.0 | 274.065 | 1.0 | 588.344 | 1.0 | 1.8 | reference |
|  | separable naive (34 taps/px) | 47.994 | 10.1 | 35.781 | 7.7 | 68.436 | 8.6 | 1.3 | same |
|  | separable running sum (O(1)/px) | 6.975 | 69.7 | 3.116 | 88.0 | 6.088 | 96.6 | 2.2 | same |
| 08 400 soft splats r=6 into 256x256 u8 | exp() per covered pixel | 3.304 | 1.0 | 0.589 | 1.0 | 2.859 | 1.0 | 5.6 | reference |
|  | precomputed stamp table | 2.102 | 1.6 | 0.436 | 1.4 | 2.021 | 1.4 | 4.8 | same |
| 09 tunnel 256x256 (texture lookup) | atan2 + sqrt per pixel | 6.417 | 1.0 | 1.408 | 1.0 | 5.644 | 1.0 | 4.6 | reference |
|  | precomputed (u,v) table | 3.382 | 1.9 | 0.323 | 4.4 | 2.510 | 2.2 | 10.5 | same |
|  | table, one readu16 for (u,v) | 2.439 | 2.6 | 0.296 | 4.8 | 2.319 | 2.4 | 8.2 | same |
| 10 plasma 256x256 | 3x math.sin per pixel | 5.463 | 1.0 | 1.716 | 1.0 | 8.222 | 1.0 | 3.2 | reference |
|  | row/col tables (sin once per row/col) | 2.322 | 2.4 | 0.396 | 4.3 | 2.078 | 4.0 | 5.9 | same |
| 11 rotozoom feedback 256x256 (nearest) | rotate each pixel (mul per pixel) | 3.020 | 1.0 | 0.525 | 1.0 | 3.736 | 1.0 | 5.8 | reference |
|  | incremental (u,v) step along the row | 2.381 | 1.3 | 0.510 | 1.0 | 2.464 | 1.5 | 4.7 | ≈same |
| 12 swirl warp 256x256: per-pixel vs 8px grid | exp+cos+sin+sqrt per pixel | 5.824 | 1.0 | 1.946 | 1.0 | 8.164 | 1.0 | 3.0 | reference |
|  | warp at grid nodes, bilinear in between | 2.940 | 2.0 | 0.544 | 3.6 | 2.972 | 2.7 | 5.4 | ≈same |
| 13 shade() call per pixel vs inline | local function per pixel | 1.968 | 1.0 | 0.212 | 1.0 | 2.632 | 1.0 | 9.3 | reference |
|  | indirect call (stored function) | 1.680 | 1.2 | 0.210 | 1.0 | 3.149 | 0.8 | 8.0 | same |
|  | inline maths | 1.579 | 1.2 | 0.218 | 1.0 | 1.517 | 1.7 | 7.2 | same |
| 14 unpack RGBA, sum channels 256x256 | 4x readu8 | 2.370 | 1.0 | 0.224 | 1.0 | 1.880 | 1.0 | 10.6 | reference |
|  | readu32 + bit32 band/rshift | 2.196 | 1.1 | 0.221 | 1.0 | 2.195 | 0.9 | 9.9 | same |
|  | readu32 + // and % | 1.852 | 1.3 | 0.439 | 0.5 | 1.858 | 1.0 | 4.2 | same |
| 15 update 20k particles | array of {x,y,vx,vy} tables | 0.838 | 1.0 | 0.495 | 1.0 | 0.860 | 1.0 | 1.7 | n/a |
|  | 4 parallel arrays (SoA) | 1.177 | 0.7 | 0.385 | 1.3 | 1.014 | 0.8 | 3.1 | n/a |
|  | one f32 buffer (interleaved) | 1.835 | 0.5 | 0.205 | 2.4 | 1.746 | 0.5 | 9.0 | n/a |
|  | vector type (p += v*dt in one op) | 0.941 | 0.9 | 0.782 | 0.6 | 0.781 | 1.1 | 1.2 | n/a |
| 16 pack a 96x96 dirty rect from 480x270 | per pixel readu32/writeu32 | 0.215 | 1.0 | 0.037 | 1.0 | 0.160 | 1.0 | 5.8 | reference |
|  | one buffer.copy per row | 0.004 | 53.8 | 0.003 | 12.3 | 0.004 | 40.0 | 1.3 | same |
| 17 2x nearest upscale 240x135 -> 480x270 | per output pixel | 2.733 | 1.0 | 0.516 | 1.0 | 3.044 | 1.0 | 5.3 | reference |
|  | write each row once, buffer.copy the twin row | 0.857 | 3.2 | 0.152 | 3.4 | 0.992 | 3.1 | 5.6 | same |
| 18 warped fBm field: resolution & temporal levers | full res, every pixel every frame | 70.421 | 1.0 | 18.366 | 1.0 | 69.486 | 1.0 | 3.8 | reference |
|  | checkerboard (half the pixels per frame) | 32.938 | 2.1 | 9.258 | 2.0 | 34.718 | 2.0 | 3.6 | ≈same |
|  | interlaced 1 row in 4 per frame | 20.355 | 3.5 | 4.222 | 4.4 | 17.465 | 4.0 | 4.8 | ≈same |
|  | half res 128x128 (GPU bilinear does the upscale) | 20.152 | 3.5 | 4.904 | 3.7 | 17.127 | 4.1 | 4.1 | ≈same |
|  | quarter res 64x64 | 5.059 | 13.9 | 0.936 | 19.6 | 4.446 | 15.6 | 5.4 | ≈same |
| 19 same kernel, typed vs untyped params | untyped params | 2.414 | 1.0 | 0.233 | 1.0 | 1.979 | 1.0 | 10.4 | reference |
|  | params annotated buffer/number | 2.329 | 1.0 | 0.136 | 1.7 | 1.938 | 1.0 | 17.1 | same |
| 20 sparse glow composite 480x270 (30 blobs) | blend every pixel | 12.864 | 1.0 | 1.284 | 1.0 | 12.454 | 1.0 | 10.0 | reference |
|  | skip pixels where glow == 0 | 2.596 | 5.0 | 0.460 | 2.8 | 2.583 | 4.8 | 5.6 | same |
|  | only 16x16 tiles marked lit | 3.563 | 3.6 | 0.390 | 3.3 | 3.661 | 3.4 | 9.1 | same |
| 21 50% overlay 256x256: blend vs dither | SWAR alpha blend (read both, write) | 5.071 | 1.0 | 0.270 | 1.0 | 4.813 | 1.0 | 18.8 | reference |
|  | checker dither: copy every other pixel | 0.602 | 8.4 | 0.105 | 2.6 | 0.466 | 10.3 | 5.7 | ≈same |
| 22 blit 300 sprites 24x24 (60% opaque) | per pixel: read, test alpha, write | 3.547 | 1.0 | 0.738 | 1.0 | 3.072 | 1.0 | 4.8 | reference |
|  | opaque runs: one buffer.copy per run | 0.312 | 11.4 | 0.170 | 4.3 | 0.304 | 10.1 | 1.8 | same |
| 23 fill 200 discs r=10 on 480x270 | bounding box, test dx²+dy² per pixel | 1.397 | 1.0 | 0.291 | 1.0 | 1.424 | 1.0 | 4.8 | reference |
|  | row spans: one buffer.copy per row | 0.187 | 7.5 | 0.109 | 2.7 | 0.186 | 7.7 | 1.7 | same |
| 24 resample 128x128 -> 256x256 | bilinear (4 taps) in Luau | 4.217 | 1.0 | 0.407 | 1.0 | 4.096 | 1.0 | 10.4 | reference |
|  | nearest in Luau | 1.269 | 3.3 | 0.211 | 1.9 | 1.152 | 3.6 | 6.0 | ≈same |
