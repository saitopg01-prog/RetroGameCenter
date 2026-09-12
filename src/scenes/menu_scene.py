"""メニューシーン。各ゲームのイメージ画像つきカードを並べて選択させる。"""

import math
import pygame
from scenes.base_scene import BaseScene
from scenes.menu_thumbnails import get_thumbnail
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_GRAY,
    MENU_COLOR_BG_TOP, MENU_COLOR_BG_BOTTOM, MENU_COLOR_FRAME,
    MENU_COLOR_FRAME_DARK, MENU_COLOR_TITLE, MENU_COLOR_TITLE_SHADOW,
    MENU_COLOR_TEXT, MENU_COLOR_CARD_BAND, MENU_COLOR_CARD_BAND_LOCKED,
    MENU_COLOR_GLOW, MENU_COLOR_BULB_ON, MENU_COLOR_BULB_OFF,
    MENU_COLOR_BULB_WIRE,
)

# (表示名, シーンキー or None=準備中, サムネイルキー)
# シーンキーが None（準備中）でも、サムネイルキーがあれば専用サムネイルを表示する。
GAMES = [
    ("DONKEY KONG '81", "donkey_kong_81", "donkey_kong_81"),
    ("TETRIS", "tetris", "tetris"),
    ("ICE CLIMBER", "ice_climber", "ice_climber"),
    ("PAC-MAN", None, None),
    ("SNAKE", "snake", "snake"),
    ("PUYO PUYO", "puyo_puyo", "puyo_puyo"),
    ("IKA JUMP", "ika_jump", "ika_jump"),
    ("DUCK HUNT", "duck_hunt", "duck_hunt"),
    ("SPACE INVADERS", "space_invaders", "space_invaders"),
    ("BREAKOUT", "block_breaker", "breakout"),
    ("WAGYAN LAND", "wagyan_land", "wagyan_land"),
    ("PINBALL", "pinball", "pinball"),
    ("MARIO KART", "mario_kart", "mario_kart"),
]

# グリッド設定
# カード枚数が増えたため 4 列に変更し、3 行で画面（600px）に収める。
COLS = 4
CARD_W = 178
CARD_H = 112
GAP_X = 16
GAP_Y = 16
GRID_TOP = 208


class MenuScene(BaseScene):
    def on_enter(self):
        super().on_enter()
        self.font_title = pygame.font.Font(None, 76)
        self.font_card = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 26)
        self.selected = 0
        self.time = 0.0
        self.bg_surface = self._build_background()

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        n = len(GAMES)
        if event.key == pygame.K_RIGHT:
            self.selected = (self.selected + 1) % n
        elif event.key == pygame.K_LEFT:
            self.selected = (self.selected - 1) % n
        elif event.key == pygame.K_DOWN:
            self.selected = min(self.selected + COLS, n - 1)
        elif event.key == pygame.K_UP:
            self.selected = max(self.selected - COLS, 0)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            scene_key = GAMES[self.selected][1]
            if scene_key:
                self.request_scene(scene_key)

    def update(self, dt):
        self.time += dt

    # --- レイアウト ---------------------------------------------------
    def _grid_origin_x(self):
        total_w = COLS * CARD_W + (COLS - 1) * GAP_X
        return (SCREEN_WIDTH - total_w) // 2

    def _card_rect(self, i):
        col = i % COLS
        row = i // COLS
        # 最終行がCOLS未満なら中央寄せ
        row_count = min(COLS, len(GAMES) - row * COLS)
        row_w = row_count * CARD_W + (row_count - 1) * GAP_X
        ox = (SCREEN_WIDTH - row_w) // 2
        x = ox + col * (CARD_W + GAP_X)
        y = GRID_TOP + row * (CARD_H + GAP_Y)
        return pygame.Rect(x, y, CARD_W, CARD_H)

    # --- 背景 -----------------------------------------------------------
    def _build_background(self):
        """焦げ茶→琥珀の縦グラデーションを1度だけ作ってキャッシュする。"""
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        r0, g0, b0 = MENU_COLOR_BG_TOP
        r1, g1, b1 = MENU_COLOR_BG_BOTTOM
        for y in range(SCREEN_HEIGHT):
            t = y / (SCREEN_HEIGHT - 1)
            color = (int(r0 + (r1 - r0) * t), int(g0 + (g1 - g0) * t),
                     int(b0 + (b1 - b0) * t))
            pygame.draw.line(surf, color, (0, y), (SCREEN_WIDTH, y))
        return surf

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen):
        screen.blit(self.bg_surface, (0, 0))
        self._draw_bulbs(screen)
        self._draw_border(screen)
        cx = SCREEN_WIDTH // 2

        # タイトル（影付き・上下にゆれる）
        bob = int(math.sin(self.time * 2) * 4)
        title = "RETRO GAME CENTER"
        shadow = self.font_title.render(title, True, MENU_COLOR_TITLE_SHADOW)
        main = self.font_title.render(title, True, MENU_COLOR_TITLE)
        screen.blit(shadow, shadow.get_rect(center=(cx + 3, 95 + bob + 3)))
        screen.blit(main, main.get_rect(center=(cx, 95 + bob)))

        sub = self.font_small.render("- SELECT A GAME -", True, MENU_COLOR_TEXT)
        screen.blit(sub, sub.get_rect(center=(cx, 155)))

        for i, (name, key, thumb_key) in enumerate(GAMES):
            self._draw_card(screen, i, name, key, thumb_key)

        # 操作説明（点滅）
        if int(self.time * 2) % 2 == 0:
            hint = self.font_small.render(
                "ARROWS: SELECT     ENTER: PLAY", True, MENU_COLOR_TEXT)
            screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 26)))

    def _draw_bulbs(self, screen):
        """画面上部の電球イルミネーション（軒先の電飾風）。"""
        count = 18
        margin = 50
        y_base = 34
        points = []
        for i in range(count):
            t = i / (count - 1)
            x = margin + t * (SCREEN_WIDTH - 2 * margin)
            y = y_base + math.sin(t * math.pi) * 8
            points.append((x, y))

        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            pygame.draw.line(screen, MENU_COLOR_BULB_WIRE, (x0, y0), (x1, y1), 2)

        for i, (x, y) in enumerate(points):
            phase = self.time * 2 + i * 0.5
            on = math.sin(phase) > 0
            color = MENU_COLOR_BULB_ON if on else MENU_COLOR_BULB_OFF
            pos = (int(x), int(y))
            if on:
                pygame.draw.circle(screen, color, pos, 8, 1)
            pygame.draw.circle(screen, color, pos, 5)

    def _draw_card(self, screen, i, name, key, thumb_key):
        rect = self._card_rect(i)
        selected = (i == self.selected)
        playable = key is not None
        thumb_h = CARD_H - 34  # 下部にタイトル帯

        # サムネイル（準備中でも専用サムネイルがあれば表示）
        thumb = get_thumbnail(thumb_key, (CARD_W - 8, thumb_h - 4))
        if not playable:
            thumb = thumb.copy()
            thumb.set_alpha(150)
        screen.blit(thumb, (rect.x + 4, rect.y + 4))

        # タイトル帯
        band = pygame.Rect(rect.x, rect.bottom - 30, rect.width, 30)
        band_color = MENU_COLOR_CARD_BAND if playable else MENU_COLOR_CARD_BAND_LOCKED
        pygame.draw.rect(screen, band_color, band)
        label_color = MENU_COLOR_GLOW if selected else (
            MENU_COLOR_TEXT if playable else COLOR_GRAY)
        label = self.font_card.render(name, True, label_color)
        if label.get_width() > rect.width - 10:
            label = self.font_small.render(name, True, label_color)
        screen.blit(label, label.get_rect(center=band.center))

        if not playable:
            cs = self.font_small.render("COMING SOON", True, MENU_COLOR_GLOW)
            screen.blit(cs, cs.get_rect(
                center=(rect.centerx, rect.y + 22)))

        # 枠：選択中は点滅発光、それ以外は控えめ
        if selected:
            brightness = 0.55 + 0.45 * abs(math.sin(self.time * 4))
            color = tuple(int(c * brightness) for c in MENU_COLOR_GLOW)
            pygame.draw.rect(screen, color, rect.inflate(8, 8), 4, border_radius=4)
        else:
            pygame.draw.rect(screen, MENU_COLOR_FRAME_DARK, rect, 2, border_radius=4)

    def _draw_border(self, screen):
        """木目調の外枠（板＋木目ライン）。"""
        outer = pygame.Rect(10, 10, SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20)
        thickness = 14
        pygame.draw.rect(screen, MENU_COLOR_FRAME, outer, thickness)

        # 木目ライン（上下辺は横線、左右辺は縦線）
        for offset in (4, 9):
            y_top = outer.top + offset
            y_bot = outer.bottom - offset
            pygame.draw.line(screen, MENU_COLOR_FRAME_DARK,
                             (outer.left, y_top), (outer.right, y_top), 1)
            pygame.draw.line(screen, MENU_COLOR_FRAME_DARK,
                             (outer.left, y_bot), (outer.right, y_bot), 1)
            x_left = outer.left + offset
            x_right = outer.right - offset
            pygame.draw.line(screen, MENU_COLOR_FRAME_DARK,
                             (x_left, outer.top), (x_left, outer.bottom), 1)
            pygame.draw.line(screen, MENU_COLOR_FRAME_DARK,
                             (x_right, outer.top), (x_right, outer.bottom), 1)
