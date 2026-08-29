"""ワギャンランドのドット絵スプライトを生成し、PNG として書き出すツール。

ゲーム本体からは import されない。素材を作り直したいときに手動で実行する。

    python src/tools/generate_wagyan_sprites.py

低解像度のキャンバス（実寸の 1/SCALE）に pygame.draw のプリミティブでドット絵を
組み、最近傍拡大（ぼかしなし）で実寸に引き伸ばして保存する。低解像度で組むこと自体が
「ドット絵」の粒度を生み、実寸で直接プリミティブ描画するより粗く・くっきりした
レトロな見た目になる。

パレットは既存の `config.py` の WAGYAN_COLOR_* をそのまま使い、シーン側の色味
（空・地面・敵など）と統一する。
"""

import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from config import (
    WAGYAN_COLOR_GROUND, WAGYAN_COLOR_GROUND_DARK,
    WAGYAN_COLOR_PLATFORM, WAGYAN_COLOR_PLATFORM_DARK,
    WAGYAN_COLOR_BODY, WAGYAN_COLOR_BODY_DARK, WAGYAN_COLOR_BELLY,
    WAGYAN_COLOR_ENEMY, WAGYAN_COLOR_ENEMY_STUNNED,
    WAGYAN_COLOR_WAGYANIZER, WAGYAN_COLOR_GOAL, WAGYAN_COLOR_BOSS,
)

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "wagyan")
SCALE = 2

WHITE = (255, 255, 255)
DARK = (20, 20, 20)
ANTENNA_TIP = (240, 210, 60)
SKIN = (230, 200, 210)
RING = (90, 90, 100)


def _save(surf, name):
    os.makedirs(ASSET_DIR, exist_ok=True)
    scaled = pygame.transform.scale(surf, (surf.get_width() * SCALE, surf.get_height() * SCALE))
    pygame.image.save(scaled, os.path.join(ASSET_DIR, f"{name}.png"))


# --- ワギャン（プレイヤー） ---------------------------------------------

def _build_wagyan(swing):
    """w=15, h=16 の低解像度キャンバスにワギャンを描く。swing は脚の開き量。"""
    w, h = 15, 16
    s = pygame.Surface((w, h), pygame.SRCALPHA)

    pygame.draw.ellipse(s, WAGYAN_COLOR_BODY, (1, 3, w - 2, h - 6))
    pygame.draw.polygon(s, WAGYAN_COLOR_BODY_DARK, [(6, 1), (9, 2), (7, 5)])
    pygame.draw.ellipse(s, WAGYAN_COLOR_BELLY, (7, 8, 6, 6))
    pygame.draw.circle(s, WHITE, (11, 7), 2)
    pygame.draw.circle(s, DARK, (12, 7), 1)
    pygame.draw.line(s, WAGYAN_COLOR_BODY_DARK, (10, 3), (10, 0), 1)
    pygame.draw.circle(s, ANTENNA_TIP, (10, 0), 1)

    pygame.draw.rect(s, WAGYAN_COLOR_BODY_DARK, (max(0, 2 + swing), h - 3, 3, 3))
    pygame.draw.rect(s, WAGYAN_COLOR_BODY_DARK, (min(w - 3, w - 5 - swing), h - 3, 3, 3))
    return s


def build_wagyan_sprites():
    _save(_build_wagyan(0), "wagyan_stand")
    _save(_build_wagyan(1), "wagyan_walk1")
    _save(_build_wagyan(-1), "wagyan_walk2")
    _save(_build_wagyan(2), "wagyan_air")
    _save(_build_wagyan(4), "wagyan_dying")


# --- 敵 ------------------------------------------------------------------

def _build_enemy(stunned, eye_variant=0):
    """w=15, h=13。stunned なら目を回した表現、そうでなければ前を向く目。"""
    w, h = 15, 13
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    color = WAGYAN_COLOR_ENEMY_STUNNED if stunned else WAGYAN_COLOR_ENEMY
    pygame.draw.ellipse(s, color, (0, 0, w, h))
    pygame.draw.ellipse(s, DARK, (0, 0, w, h), 1)

    if stunned:
        offset = 1 if eye_variant == 0 else -1
        for ex in (5, 10):
            pygame.draw.circle(s, WHITE, (ex, 4), 2)
            pygame.draw.circle(s, DARK, (ex + offset, 4 + offset), 1)
    else:
        pygame.draw.circle(s, DARK, (11, 4), 1)
    return s


def build_enemy_sprites():
    _save(_build_enemy(stunned=False), "enemy_normal")
    _save(_build_enemy(stunned=True, eye_variant=0), "enemy_stunned1")
    _save(_build_enemy(stunned=True, eye_variant=1), "enemy_stunned2")


# --- 地形タイル ------------------------------------------------------------

def _build_terrain_tile(top_color, body_color):
    """w=20, h=20 の敷き詰め用タイル。上部を明るい帯、下部を濃い帯にする。"""
    w, h = 20, 20
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    top_h = 7
    pygame.draw.rect(s, top_color, (0, 0, w, top_h))
    pygame.draw.rect(s, body_color, (0, top_h, w, h - top_h))
    # 質感アクセント（テクスチャ用の小さな粒）
    for i, (px, py) in enumerate([(3, 2), (9, 4), (15, 1), (5, 12), (13, 15)]):
        shade = body_color if i % 2 == 0 else top_color
        s.set_at((px, py), shade)
    return s


def build_terrain_sprites():
    _save(_build_terrain_tile(WAGYAN_COLOR_GROUND, WAGYAN_COLOR_GROUND_DARK), "ground_tile")
    _save(_build_terrain_tile(WAGYAN_COLOR_PLATFORM, WAGYAN_COLOR_PLATFORM_DARK), "platform_tile")


# --- ワギャナイザー ---------------------------------------------------------

def build_wagyanizer_sprite():
    w, h = 14, 14
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(s, WAGYAN_COLOR_WAGYANIZER, [(1, 4), (13, 1), (13, 13), (1, 10)])
    pygame.draw.circle(s, RING, (1, 7), 4, 1)
    _save(s, "wagyanizer")


# --- ゴール ---------------------------------------------------------------

def build_goal_sprite():
    w, h = 25, 65
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (230, 230, 230), (10, 0, 3, h))
    pygame.draw.polygon(s, WAGYAN_COLOR_GOAL, [(12, 0), (22, 8), (12, 16)])
    _save(s, "goal")


# --- ボス戦 ---------------------------------------------------------------

def build_boss_sprites():
    w, h = 40, 45
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, WAGYAN_COLOR_BOSS, (0, 15, w, h - 15))
    pygame.draw.circle(s, SKIN, (w // 2, 10), 11)
    pygame.draw.polygon(s, DARK, [(10, 0), (30, 0), (w // 2, 15)])
    _save(s, "boss_dr_devil")

    fw, fh = 18, 21
    face = pygame.Surface((fw, fh), pygame.SRCALPHA)
    pygame.draw.ellipse(face, WAGYAN_COLOR_BODY, (0, 0, fw, fh))
    pygame.draw.circle(face, WHITE, (5, 6), 2)
    pygame.draw.circle(face, DARK, (4, 6), 1)
    _save(face, "boss_wagyan_faceoff")


def main():
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    build_wagyan_sprites()
    build_enemy_sprites()
    build_terrain_sprites()
    build_wagyanizer_sprite()
    build_goal_sprite()
    build_boss_sprites()
    print(f"generated sprites into {os.path.abspath(ASSET_DIR)}")


if __name__ == "__main__":
    main()
