#!/usr/bin/env python3
"""どの縮小変種が表示されているかを特定する「スケールプローブ」PNGを生成する。

2026-07 の変種パイプライン変更後、透明PNGの縮小変種はアルファ2値化の際に
不透明ブロックが「大きさ次第で」生き残る。ブロック1辺 k px のパターンは
縮小率 f に対して k ≳ f なら残り、k < f ならほぼ消える。

長辺3072pxで投稿すると変種は small(f≈4.5) / medium(f≈2.56) / large(f≈1.5) /
orig(f=1) になるため、どの帯(K2/K3/K5...)が見えるかで表示中の変種が分かる:

  - K2以上が見える  → large (f1.5)
  - K3以上のみ見える → medium (f2.56)
  - K5以上のみ見える → small (f4.5)
  - K1(市松)まで完全に見える → orig

使い方: 生成したPNGをXに投稿し、TLサムネとタップ後の拡大ビューをスクショ。
それぞれでどの帯が見えるかを読み取る。
"""
import sys
from PIL import Image, ImageDraw, ImageFont

# (ブロック1辺k, 周期p) — 被覆率(k/p)^2は0.5未満に抑え、平均アルファでは残らない
BANDS = [(1, 2), (2, 3), (3, 5), (4, 6), (5, 8), (7, 10)]
GRAY = 200          # ブロック色(黒背景で明るく見える)

BAND_H = 180
LABEL_W = 220
HEADER_H = 60
WIDTH = 3072
HEIGHT = HEADER_H + BAND_H * len(BANDS) + 40

TRANSPARENT = 0
WHITE = 1


def main(out_path: str) -> None:
    palette = [(0, 0, 0), (255, 255, 255), (GRAY, GRAY, GRAY)]
    BLOCK = 2
    px = bytearray(WIDTH * HEIGHT)

    for b, (k, p) in enumerate(BANDS):
        # k=1は市松(従来方式の対照)、それ以外はk×kブロックを周期pで敷き詰め
        top = HEADER_H + b * BAND_H
        for y in range(top + 10, top + BAND_H - 10):
            base = y * WIDTH
            if k == 1:
                start = LABEL_W + ((LABEL_W + y) % 2)
                n = len(range(start, WIDTH - 20, 2))
                px[base + start:base + WIDTH - 20:2] = bytes([BLOCK]) * n
            elif (y - top - 10) % p < k:
                for x0 in range(LABEL_W, WIDTH - 20 - p, p):
                    px[base + x0:base + x0 + k] = bytes([BLOCK]) * k

    img = Image.frombytes("P", (WIDTH, HEIGHT), bytes(px))
    img.putpalette([v for rgb in palette for v in rgb])

    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=48)
    draw.text((LABEL_W, 8), "SCALE PROBE: which bands are visible?", fill=WHITE, font=font)
    for b, (k, p) in enumerate(BANDS):
        draw.text((16, HEADER_H + b * BAND_H + BAND_H // 2 - 24),
                  f"K{k}", fill=WHITE, font=font)

    img.save(out_path, format="PNG", transparency=TRANSPARENT, optimize=True)
    print(f"wrote {out_path} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "scale_probe.png")
