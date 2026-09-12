"""ピンボールのフリッパー（左右）。

pivot（回転軸）＋現在角度で表現する。角度は「水平から時計回り」の度数法で、
side=+1（左フリッパー）は pivot から (+cos, +sin) 方向へ、side=-1（右フリッパー）
は (-cos, +sin) 方向へ伸びる（左右対称に同じ角度パラメータを共有できる）。

静止角（下向き・外側）から作動角（上向き・内側）へ高速回転し、振り上げ中に
ボールへ触れると強いキックを与える。振り上げ切った後や静止中に触れた場合は
通常の反射のみ（＝連続で置いたままにしていても暴発しない）。
"""

import math

import pygame

from config import (
    PINBALL_FLIPPER_LENGTH, PINBALL_FLIPPER_THICKNESS,
    PINBALL_FLIPPER_REST_ANGLE, PINBALL_FLIPPER_UP_ANGLE,
    PINBALL_FLIPPER_ANGULAR_SPEED, PINBALL_FLIPPER_KICK,
    PINBALL_WALL_RESTITUTION, PINBALL_COLOR_FLIPPER,
)
from game_objects.pinball.physics import circle_segment_collide, reflect_velocity


class Flipper:
    def __init__(self, pivot_x, pivot_y, side):
        self.px = pivot_x
        self.py = pivot_y
        self.side = side  # +1: 左, -1: 右
        self.rest_angle = math.radians(PINBALL_FLIPPER_REST_ANGLE)
        self.up_angle = math.radians(PINBALL_FLIPPER_UP_ANGLE)
        self.angle = self.rest_angle
        self.active = False
        self.swinging_up = False

    def set_active(self, active):
        self.active = active

    def tip(self):
        tx = self.px + self.side * math.cos(self.angle) * PINBALL_FLIPPER_LENGTH
        ty = self.py + math.sin(self.angle) * PINBALL_FLIPPER_LENGTH
        return tx, ty

    def update(self, dt):
        target = self.up_angle if self.active else self.rest_angle
        max_step = math.radians(PINBALL_FLIPPER_ANGULAR_SPEED) * dt
        diff = target - self.angle
        self.swinging_up = self.active and diff < -1e-4
        if abs(diff) <= max_step:
            self.angle = target
        else:
            self.angle += max_step if diff > 0 else -max_step

    def collide_ball(self, ball):
        ax, ay = self.px, self.py
        bx, by = self.tip()
        radius = ball.radius + PINBALL_FLIPPER_THICKNESS / 2
        hit = circle_segment_collide(ball.x, ball.y, radius, ax, ay, bx, by)
        if hit is None:
            return False
        nx, ny, penetration = hit
        ball.x += nx * penetration
        ball.y += ny * penetration
        if self.swinging_up:
            ball.vx = self.side * PINBALL_FLIPPER_KICK * 0.55
            ball.vy = -PINBALL_FLIPPER_KICK * 0.9
        else:
            ball.vx, ball.vy = reflect_velocity(
                ball.vx, ball.vy, nx, ny, PINBALL_WALL_RESTITUTION)
        return True

    def draw(self, screen):
        tip = self.tip()
        pygame.draw.line(screen, PINBALL_COLOR_FLIPPER, (self.px, self.py), tip,
                         PINBALL_FLIPPER_THICKNESS)
        pygame.draw.circle(screen, PINBALL_COLOR_FLIPPER,
                           (int(self.px), int(self.py)), PINBALL_FLIPPER_THICKNESS // 2)
        pygame.draw.circle(screen, PINBALL_COLOR_FLIPPER,
                           (int(tip[0]), int(tip[1])), PINBALL_FLIPPER_THICKNESS // 2)
