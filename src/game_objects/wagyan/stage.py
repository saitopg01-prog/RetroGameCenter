"""ワギャンランド 1 ステージの地形モデルと描画。

DK81・アイスクライマーと同じく「自己完結モジュール」方針。

このゲームは縦スクロールなし・横スクロールのみなので、地形は
ワールド x 座標に対する固定 y（WAGYAN_GROUND_Y）の矩形群として持つ。

構成:
  - 地面（ground）: 隙間（gaps）を除いた区間に敷かれる、落下しない土台。
  - 中州（stepping island）: 隙間の中に置かれた小さな足場。歩行する敵が
    常駐しており、しびれさせないと乗れば即ミスになる（ジャンプで渡る
    唯一のルート）。
  - 浮遊足場（platform）: 地面から直接ジャンプしても届かない高さにあり、
    敵の背中（しびれさせて足場化）に乗ってからでないと届かない。
  - ワギャナイザー: 取ると音波レベルが上がるアイテム。

solid_rects() が「その時点で乗れる地形」を返す。しびれ中の敵はここに
含まれないので、乗れる敵の矩形は scene 側で毎フレーム追加する。
"""

import pygame

from config import (
    WAGYAN_WORLD_WIDTH, WAGYAN_GROUND_Y, WAGYAN_GOAL_X,
    SCREEN_HEIGHT, SCREEN_WIDTH,
)
from utils.sprite_loader import load_wagyan_sprite

GROUND_BOTTOM = SCREEN_HEIGHT  # 地面の下面（画面外まで塗ればよい）

# 隙間（穴）: (start_x, end_x)。この区間には地面がない。
GAPS = [(760, 980), (1650, 1880)]

# 中州（隙間の中の小足場）。幅は片側ジャンプで渡れる距離に調整済み。
ISLANDS = [
    pygame.Rect(830, WAGYAN_GROUND_Y, 70, GROUND_BOTTOM - WAGYAN_GROUND_Y),
    pygame.Rect(1750, WAGYAN_GROUND_Y, 70, GROUND_BOTTOM - WAGYAN_GROUND_Y),
]

# 浮遊足場（地面からは届かず、しびれた敵の背中経由でのみ届く高さ）
PLATFORMS = [
    pygame.Rect(2200, 415, 140, GROUND_BOTTOM - 415),
]

# ワギャナイザー配置（中心 x, 中心 y）: 取得順に音波レベルが上がる。
# y は歩いているだけで触れる高さ（ジャンプ必須にしない）。
WAGYANIZER_POSITIONS = [
    [400, 500],
    [1150, 500],
    [2000, 500],
]

# 敵の初期配置定義: scene がこれを見て Enemy インスタンスを生成する
# kind: "patrol"（地面を歩く）/ "island"（中州に常駐）
ENEMY_DEFS = [
    {"kind": "patrol", "x": 500, "min_x": 450, "max_x": 650},
    {"kind": "island", "x": 865, "min_x": 835, "max_x": 895},
    {"kind": "island", "x": 1785, "min_x": 1755, "max_x": 1815},
    {"kind": "patrol", "x": 2200, "min_x": 2150, "max_x": 2260},
    {"kind": "patrol", "x": 2550, "min_x": 2480, "max_x": 2650},
    {"kind": "patrol", "x": 2780, "min_x": 2720, "max_x": 2860},
]

GOAL_X = WAGYAN_GOAL_X


def is_pit(x):
    """x 座標が隙間（島を除く）にあるか。"""
    for gx0, gx1 in GAPS:
        if gx0 <= x <= gx1:
            for isl in ISLANDS:
                if isl.left <= x <= isl.right:
                    return False
            return True
    return False


class Stage:
    def __init__(self):
        self.wagyanizers = [
            {"x": p[0], "y": p[1], "collected": False} for p in WAGYANIZER_POSITIONS
        ]
        self._ground_rects = self._build_ground_segments()

    def _build_ground_segments(self):
        """GAPS を除いた地面区間の Rect リスト。"""
        points = [0]
        for gx0, gx1 in GAPS:
            points.append(gx0)
            points.append(gx1)
        points.append(WAGYAN_WORLD_WIDTH)
        segments = []
        for i in range(0, len(points), 2):
            x0, x1 = points[i], points[i + 1]
            if x1 > x0:
                segments.append(pygame.Rect(x0, WAGYAN_GROUND_Y, x1 - x0,
                                            GROUND_BOTTOM - WAGYAN_GROUND_Y))
        return segments

    def solid_rects(self):
        """地面・中州・浮遊足場（敵を除く静的地形）。"""
        return self._ground_rects + ISLANDS + PLATFORMS

    def collect_wagyanizer(self, player_rect):
        """プレイヤーと重なる未取得のワギャナイザーがあれば回収して返す。"""
        for w in self.wagyanizers:
            if w["collected"]:
                continue
            wr = pygame.Rect(w["x"] - 14, w["y"] - 14, 28, 28)
            if player_rect.colliderect(wr):
                w["collected"] = True
                return w
        return None

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen, cam_x):
        self._draw_ground(screen, cam_x)
        for isl in ISLANDS:
            self._draw_block(screen, isl, cam_x)
        for plat in PLATFORMS:
            self._draw_block(screen, plat, cam_x, platform=True)
        self._draw_wagyanizers(screen, cam_x)
        self._draw_goal(screen, cam_x)

    def _draw_ground(self, screen, cam_x):
        for rect in self._ground_rects:
            self._draw_block(screen, rect, cam_x)

    def _draw_block(self, screen, rect, cam_x, platform=False):
        sx = rect.x - cam_x
        if sx + rect.width < 0 or sx > SCREEN_WIDTH:
            return
        tile = load_wagyan_sprite("platform_tile" if platform else "ground_tile")
        tw, th = tile.get_size()
        for tx in range(rect.x, rect.x + rect.width, tw):
            for ty in range(rect.y, rect.y + rect.height, th):
                screen.blit(tile, (tx - cam_x, ty))

    def _draw_wagyanizers(self, screen, cam_x):
        sprite = load_wagyan_sprite("wagyanizer")
        for w in self.wagyanizers:
            if w["collected"]:
                continue
            x = int(w["x"] - cam_x)
            y = int(w["y"])
            if x < -30 or x > SCREEN_WIDTH + 30:
                continue
            screen.blit(sprite, sprite.get_rect(center=(x, y)))

    def _draw_goal(self, screen, cam_x):
        x = int(GOAL_X - cam_x)
        if x < -50 or x > SCREEN_WIDTH + 50:
            return
        sprite = load_wagyan_sprite("goal")
        pole_top = WAGYAN_GROUND_Y - 130
        screen.blit(sprite, (x, pole_top))
