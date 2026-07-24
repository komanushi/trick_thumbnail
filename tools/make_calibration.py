#!/usr/bin/env python3
"""Xモバイルアプリ再キャリブレーション用のパッチ表PNGを生成する。

2026-07 のカルーセル化で拡大ビューのレンダリングが変わった可能性があるため、
「どの倍率なら市松パッチが中央の基準色と同じ明るさに見えるか」を実機で
測るための画像。使い方:

  1. python3 tools/make_calibration.py 出力先.png
  2. 出力PNGをXに投稿する(長辺3072pxなのでサーバーが表示用変種を生成する)
  3. モバイルアプリで (a)TLサムネ (b)タップ後の拡大ビュー をスクショ
  4. 各セルの市松部分が中央の四角と同じ明るさに見える列の倍率が正解

各セル: 基準グレー G の行 × 倍率 m の列。市松の不透明ピクセルは
clip(G*m)、中央の四角は不透明の G。PNG-8 (パレット + tRNS、アルファ2値)
で出力し、Xが無条件でPNGのまま保持する形式に合わせる。
"""
import sys
from PIL import Image, ImageDraw, ImageFont

GRAYS = [32, 64, 96, 128, 160, 192]
MULTS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.5, 3.0, 4.0]

CELL = 200          # セル1辺
GAP = 4             # セル境界の透過ギャップ
REF = 80            # 中央の不透明基準四角の1辺
LABEL_W = 152       # 左の行ラベル帯
HEADER_H = 80       # 上の列ラベル帯
FOOTER_H = 120      # 下の不透明グレー帯(スクショ露出の基準)
WIDTH = 3072        # 長辺2048px超が必須(サーバー変種を確実に発生させる)
HEIGHT = HEADER_H + CELL * len(GRAYS) + FOOTER_H

TRANSPARENT = 0     # index 0 = 透過黒
WHITE = 1


def main(out_path: str) -> None:
    grid_w = LABEL_W + CELL * len(MULTS)
    assert grid_w <= WIDTH, grid_w

    # パレット構築: 0=透過黒, 1=白, 以降 基準グレーと倍率適用色
    palette = [(0, 0, 0), (255, 255, 255)]
    index_of = {}

    def idx(v: int) -> int:
        if v not in index_of:
            index_of[v] = len(palette)
            palette.append((v, v, v))
        return index_of[v]

    px = bytearray(WIDTH * HEIGHT)  # 全面 index0(透過)

    def fill_rect(x0, y0, w, h, index):
        for y in range(y0, y0 + h):
            base = y * WIDTH + x0
            px[base:base + w] = bytes([index]) * w

    def fill_checker(x0, y0, w, h, index):
        # (x+y) が偶数のピクセルだけ index、残りは透過のまま(被覆率50%固定)
        for y in range(y0, y0 + h):
            start = x0 + ((x0 + y) % 2)
            base = y * WIDTH
            n = len(range(start, x0 + w, 2))
            px[base + start:base + x0 + w:2] = bytes([index]) * n

    for r, g in enumerate(GRAYS):
        top = HEADER_H + r * CELL
        for c, m in enumerate(MULTS):
            left = LABEL_W + c * CELL
            stored = min(255, round(g * m))
            fill_checker(left + GAP, top + GAP,
                         CELL - 2 * GAP, CELL - 2 * GAP, idx(stored))
            # 中央の不透明基準四角(この明るさに市松が一致する列が正解倍率)
            cy, cx = top + CELL // 2, left + CELL // 2
            fill_rect(cx - REF // 2, cy - REF // 2, REF, REF, idx(g))

    # 最下段: 不透明のグレー帯(基準色がスクショでどう写るかの物差し)
    band_top = HEADER_H + CELL * len(GRAYS) + 20
    seg = grid_w // len(GRAYS)
    for r, g in enumerate(GRAYS):
        fill_rect(r * seg, band_top, seg, 80, idx(g))

    img = Image.frombytes("P", (WIDTH, HEIGHT), bytes(px))
    img.putpalette([v for rgb in palette for v in rgb])

    # ラベルは不透明白(サムネでも拡大でも読める)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=44)
    small = ImageFont.load_default(size=36)
    for c, m in enumerate(MULTS):
        draw.text((LABEL_W + c * CELL + 40, 16), f"x{m:g}", fill=WHITE, font=font)
    for r, g in enumerate(GRAYS):
        draw.text((16, HEADER_H + r * CELL + CELL // 2 - 22), f"G{g}", fill=WHITE, font=font)
    draw.text((16, band_top - 60), "opaque ref:", fill=WHITE, font=small)

    img.save(out_path, format="PNG", transparency=TRANSPARENT, optimize=True)
    print(f"wrote {out_path} ({WIDTH}x{HEIGHT}, {len(palette)} colors)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "calibration.png")
