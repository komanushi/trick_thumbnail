#!/usr/bin/env python3
"""分数アルファ(PNG-32)による変種生存差プローブを生成する。

スケールプローブの結果、AndroidのTL≈medium(縮小率2.56)・拡大≈large(1.5)で、
Xの新リサンプラは箱平均+アルファ0.5閾値の2値化に近いと判明した。
箱モデルでは 2×2ブロックをアルファαで置くと:
  - large:  縮小窓(1.5px角)がブロック内に収まる → 平均α → α>0.5なら生存
  - medium: 窓(2.56px角)が周期全体を均す → 平均≈0.61α → α<0.82なら全滅
つまり 0.5 < α < 0.8 の2×2ブロックは「拡大でだけ見える」はず。これが成立
すればモバイル向けトリックを再建できる。

帯構成(すべてグレー200のブロック):
  A: 2×2 周期3 α=1.00 — 対照(TLでも拡大でも見えるはず)
  B: 2×2 周期3 α=0.70 — 本命
  C: 2×2 周期3 α=0.60 — 本命
  D: 2×2 周期3 α=0.55 — 本命(閾値ぎりぎり)
  E: 2×2 周期4 α=0.70 — 低被覆版
  F: 2×2 周期4 α=0.60 — 低被覆版
  G: 全面 α=0.50      — 対照(全変種で消えるはず。origのアルファ保持確認用)

判定: TLで消えて拡大でだけ B〜F が見えれば成立。全帯がTLでも見える場合は
PNG-32のアルファがアップロード時に2値化されている(方式不成立)。
"""
import sys
from PIL import Image, ImageDraw, ImageFont

GRAY = 200
BANDS = [
    ("A k2 p3 a100", 2, 3, 255),
    ("B k2 p3 a70",  2, 3, 179),
    ("C k2 p3 a60",  2, 3, 153),
    ("D k2 p3 a55",  2, 3, 140),
    ("E k2 p4 a70",  2, 4, 179),
    ("F k2 p4 a60",  2, 4, 153),
    ("G flat a50",   0, 1, 127),
]

BAND_H = 160
LABEL_W = 340
HEADER_H = 60
WIDTH = 3072
HEIGHT = HEADER_H + BAND_H * len(BANDS) + 30


def main(out_path: str) -> None:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    px = img.load()

    for b, (_, k, p, alpha) in enumerate(BANDS):
        top = HEADER_H + b * BAND_H
        for y in range(top + 10, top + BAND_H - 10):
            if k == 0:  # 全面均一アルファ
                for x in range(LABEL_W, WIDTH - 20):
                    px[x, y] = (GRAY, GRAY, GRAY, alpha)
            elif (y - top - 10) % p < k:
                for x0 in range(LABEL_W, WIDTH - 20 - p, p):
                    for dx in range(k):
                        px[x0 + dx, y] = (GRAY, GRAY, GRAY, alpha)

    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=44)
    draw.text((LABEL_W, 6), "ALPHA PROBE: bands visible only when zoomed?",
              fill=(255, 255, 255, 255), font=font)
    for b, (label, *_rest) in enumerate(BANDS):
        draw.text((12, HEADER_H + b * BAND_H + BAND_H // 2 - 22),
                  label, fill=(255, 255, 255, 255), font=font)

    img.save(out_path, format="PNG", optimize=True)
    print(f"wrote {out_path} ({WIDTH}x{HEIGHT}, RGBA)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "alpha_probe.png")
