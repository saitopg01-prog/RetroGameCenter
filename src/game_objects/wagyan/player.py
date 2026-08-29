"""ワギャンランドのプレイヤー「ワギャン」。

横スクロールのみ（縦カメラなし）なので、ワールド座標はそのまま画面座標として
扱い、cam_x だけを引いて描画する。

物理は標準的なプラットフォーマー方式：
  - 毎フレーム重力を加算し、位置を更新。
  - 落下中（vel_y >= 0）に、直前フレームで面の上・今フレームで面以下に
    到達した solid rect があれば着地。
  - solid_rects は毎フレーム scene から渡される（しびれ中の敵の背中も
    一時的に「乗れる地形」として含まれるため、静的地形と分けずに扱う）。

音波攻撃はレベル 1〜4（ワッ・ギャ・ガー・ギャー）で射程としびれ時間が変わる。
"""

import pygame

from config import (
    WAGYAN_PLAYER_W, WAGYAN_PLAYER_H, WAGYAN_PLAYER_SPEED, WAGYAN_JUMP_POWER,
    WAGYAN_GRAVITY, WAGYAN_WORLD_WIDTH,
    WAGYAN_VOICE_RANGE, WAGYAN_VOICE_STUN, WAGYAN_VOICE_COOLDOWN,
    WAGYAN_VOICE_ACTIVE_TIME,
)
from utils.sprite_loader import load_wagyan_sprite


class Wagyan:
    def __init__(self, x, bottom):
        self.width = WAGYAN_PLAYER_W
        self.height = WAGYAN_PLAYER_H
        self.cx = float(x)
        self.bottom = float(bottom)
        self.vel_y = 0.0
        self.state = "ground"
        self.facing = 1
        self.level = 1  # 1..4（ワッ・ギャ・ガー・ギャー）
        self.voice_cooldown = 0.0
        self.voice_timer = 0.0  # 現在発射中の音波が有効な残り時間
        self.walk_anim = 0.0
        self.spin_angle = 0.0
        self.moving = False

    # --- 位置ヘルパー -------------------------------------------------
    @property
    def x(self):
        return self.cx - self.width / 2

    @property
    def top(self):
        return self.bottom - self.height

    def get_world_rect(self):
        return pygame.Rect(int(self.x), int(self.top), self.width, self.height)

    def get_screen_rect(self, cam_x):
        r = self.get_world_rect()
        r.x -= int(cam_x)
        return r

    # --- 入力 -----------------------------------------------------------
    def jump(self):
        if self.state == "ground":
            self.vel_y = -WAGYAN_JUMP_POWER
            self.state = "air"
            return True
        return False

    def try_fire_voice(self):
        """クールダウン中でなければ音波を発射する。発射できたら True。"""
        if self.voice_cooldown > 0:
            return False
        self.voice_cooldown = WAGYAN_VOICE_COOLDOWN
        self.voice_timer = WAGYAN_VOICE_ACTIVE_TIME
        return True

    def voice_hitbox(self):
        """現在アクティブな音波の当たり判定矩形。アクティブでなければ None。"""
        if self.voice_timer <= 0:
            return None
        rng = WAGYAN_VOICE_RANGE[self.level - 1]
        h = 40
        y = self.bottom - self.height / 2 - h / 2
        x = self.cx if self.facing >= 0 else self.cx - rng
        return pygame.Rect(int(x), int(y), int(rng), int(h))

    def voice_stun_duration(self):
        return WAGYAN_VOICE_STUN[self.level - 1]

    def level_up(self):
        if self.level < 4:
            self.level += 1
            return True
        return False

    def start_dying(self):
        self.state = "dying"
        self.spin_angle = 0.0
        self.vel_y = -260

    # --- 更新 ---------------------------------------------------------
    def update(self, dt, keys, solid_rects):
        if self.voice_cooldown > 0:
            self.voice_cooldown = max(0.0, self.voice_cooldown - dt)
        if self.voice_timer > 0:
            self.voice_timer = max(0.0, self.voice_timer - dt)

        move = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
        self.moving = move != 0
        if move != 0:
            self.facing = move
            self.cx += move * WAGYAN_PLAYER_SPEED * dt
            self.walk_anim += dt * 11
        half = self.width / 2
        self.cx = max(half, min(WAGYAN_WORLD_WIDTH - half, self.cx))

        prev_bottom = self.bottom
        self.vel_y += WAGYAN_GRAVITY * dt
        self.bottom += self.vel_y * dt

        grounded = False
        if self.vel_y >= 0:
            left, right = self.cx - half, self.cx + half
            for rect in solid_rects:
                if right <= rect.left or left >= rect.right:
                    continue
                if prev_bottom <= rect.top + 1 and self.bottom >= rect.top:
                    self.bottom = rect.top
                    self.vel_y = 0.0
                    grounded = True
                    break
        self.state = "ground" if grounded else "air"

    def update_dying(self, dt):
        self.spin_angle += dt * 560
        self.vel_y += WAGYAN_GRAVITY * 0.6 * dt
        self.bottom += self.vel_y * dt

    # --- 描画 ---------------------------------------------------------
    def _sprite_name(self):
        if self.state == "dying":
            return "wagyan_dying"
        if self.state == "air":
            return "wagyan_air"
        if self.moving:
            return "wagyan_walk1" if int(self.walk_anim) % 2 == 0 else "wagyan_walk2"
        return "wagyan_stand"

    def draw(self, screen, cam_x, blink=False):
        if blink:
            return
        surf = load_wagyan_sprite(self._sprite_name())
        if self.facing < 0:
            surf = pygame.transform.flip(surf, True, False)
        if self.state == "dying":
            surf = pygame.transform.rotate(surf, self.spin_angle % 360)
        sx = int(self.cx - cam_x)
        sy = int(self.bottom - self.height / 2)
        screen.blit(surf, surf.get_rect(center=(sx, sy)))
