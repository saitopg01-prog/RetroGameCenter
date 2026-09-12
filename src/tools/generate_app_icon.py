"""アプリ（ウィンドウ/タスクバー）アイコンを生成し、PNG として書き出すツール。

ゲーム本体からは import されない。アイコンを作り直したいときに手動で実行する。

    python src/tools/generate_app_icon.py

`src/tools/generate_wagyan_sprites.py` と同じ方針：低解像度キャンバスに
`pygame.draw` でドット絵を組み、最近傍拡大して PNG 保存する。
"""

import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

ASSET_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "app")
)
SCALE = 2

BODY = (40, 26, 16)          # 筐体本体（濃い焦げ茶シルエット）
BODY_EDGE = (70, 45, 25)
MARQUEE = (255, 170, 60)     # 上部マーキー（オレンジ・点灯）
SCREEN_FRAME = (20, 14, 10)
SCREEN_GLOW = (255, 205, 110)  # 画面の光
PANEL = (90, 58, 30)          # 操作パネル
BUTTON = (255, 170, 60)
STICK = (230, 225, 220)


def _build_icon():
    """w=32, h=32 のキャンバスにアーケード筐体のシルエットを描く。"""
    w, h = 32, 32
    s = pygame.Surface((w, h), pygame.SRCALPHA)

    # 筐体本体
    body = pygame.Rect(6, 6, 20, 24)
    pygame.draw.rect(s, BODY, body, border_radius=2)
    pygame.draw.rect(s, BODY_EDGE, body, 1, border_radius=2)

    # マーキー（上部の光る看板部分）
    pygame.draw.rect(s, MARQUEE, (8, 8, 16, 4), border_radius=1)

    # 画面
    screen = pygame.Rect(9, 14, 14, 8)
    pygame.draw.rect(s, SCREEN_FRAME, screen)
    pygame.draw.rect(s, SCREEN_GLOW, (screen.x + 2, screen.y + 2, screen.w - 4, screen.h - 4))

    # 操作パネル
    pygame.draw.rect(s, PANEL, (8, 24, 16, 4))
    pygame.draw.circle(s, STICK, (12, 24), 2)  # レバー
    pygame.draw.line(s, STICK, (12, 24), (12, 21), 1)
    pygame.draw.circle(s, BUTTON, (20, 26), 1)  # ボタン
    pygame.draw.circle(s, BUTTON, (23, 26), 1)

    return s


def main():
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(ASSET_DIR, exist_ok=True)
    icon = _build_icon()
    scaled = pygame.transform.scale(icon, (icon.get_width() * SCALE, icon.get_height() * SCALE))
    path = os.path.join(ASSET_DIR, "icon.png")
    pygame.image.save(scaled, path)
    print(f"generated icon into {path}")


if __name__ == "__main__":
    main()
