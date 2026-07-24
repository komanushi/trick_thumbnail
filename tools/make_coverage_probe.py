#!/usr/bin/env python3
"""隠し市松の最適な被覆率を決める「カバレッジプローブ」PNGを生成する。

50%市松は縮小変種の2値化閾値(アルファ平均ちょうど0.5)の上に乗っており、
丸めの位相次第で全滅したり半分生き残ったりする(実測: 同じ3072px投稿でも
プローブは全滅、キャリブレーションは30〜60%生存)。確実に隠すには被覆率を
閾値より下げる必要がある。ただし下げるほど復元倍率 k=1/p が上がり、
明るい色のクリップ劣化が増える。この画像で「TLで消える最大の被覆率」を
実機で特定する。

帯は index.html の processTrick と同じ Bayer4x4 ディザで生成する
(p8=8/16=50% は対照、p7=43.75%, p6=37.5%, p5=31.25%, p4=25%)。
判定: 投稿してTLサムネで見えない帯のうち、最も被覆率が高いものを採用する。
"""
import sys
from PIL import Image, ImageDraw, ImageFont

BAYER4 = [0, 8, 2, 10,
          12, 4, 14, 6,
          3, 11, 1, 9,
          15, 7, 13, 5]
GRAY = 200
BANDS = [8, 7, 6, 5, 4]   # p/16

BAND_H = 180
LABEL_W = 300
HEADER_H = 60
WIDTH = 3072
HEIGHT = HEADER_H + BAND_H * len(BANDS) + 30

TRANSPARENT = 0
WHITE = 1
BLOCK = 2


def main(out_path: str) -> None:
    px = bytearray(WIDTH * HEIGHT)
    for b, n in enumerate(BANDS):
        p = n / 16
        top = HEADER_H + b * BAND_H
        for y in range(top + 10, top + BAND_H - 10):
            base = y * WIDTH
            by = (y & 3) * 4
            for x in range(LABEL_W, WIDTH - 20):
                thr = (BAYER4[by + (x & 3)] + 0.5) / 16
                if p > thr:
                    px[base + x] = BLOCK

    img = Image.frombytes("P", (WIDTH, HEIGHT), bytes(px))
    img.putpalette([0, 0, 0, 255, 255, 255, GRAY, GRAY, GRAY])

    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=44)
    draw.text((LABEL_W, 6), "COVERAGE PROBE: highest invisible band wins",
              fill=WHITE, font=font)
    for b, n in enumerate(BANDS):
        draw.text((12, HEADER_H + b * BAND_H + BAND_H // 2 - 22),
                  f"p{n} {n/16:.0%}", fill=WHITE, font=font)

    img.save(out_path, format="PNG", transparency=TRANSPARENT, optimize=True)
    print(f"wrote {out_path} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "coverage_probe.png")
