"""ピンボールのボール。位置・速度と、重力＋移動の積分のみを持つ。

当たり判定・反射は Table / Flipper 側が Ball の位置・速度を直接書き換える形で行う
（専用の物理エンジンは使わないシンプルな自作方式）。
"""

import pygame

from config import PINBALL_BALL_RADIUS, PINBALL_GRAVITY, PINBALL_MAX_SPEED, PINBALL_COLOR_BALL


class Ball:
    def __init__(self, x, y, vx=0.0, vy=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = PINBALL_BALL_RADIUS
        self.launched = vx != 0.0 or vy != 0.0

    def apply_gravity(self, dt):
        self.vy += PINBALL_GRAVITY * dt

    def integrate(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        speed_sq = self.vx * self.vx + self.vy * self.vy
        max_sq = PINBALL_MAX_SPEED * PINBALL_MAX_SPEED
        if speed_sq > max_sq:
            scale = PINBALL_MAX_SPEED / (speed_sq ** 0.5)
            self.vx *= scale
            self.vy *= scale

    def draw(self, screen):
        pos = (int(self.x), int(self.y))
        pygame.draw.circle(screen, PINBALL_COLOR_BALL, pos, self.radius)
        pygame.draw.circle(screen, (130, 130, 150), pos, self.radius, 1)
        hi = (int(self.x - self.radius * 0.3), int(self.y - self.radius * 0.3))
        pygame.draw.circle(screen, (255, 255, 255), hi, max(1, self.radius // 3))
