"""ピンボールのテーブル（静的ジオメトリ）。

壁・ポップバンパー・スタンドターゲット・ランプ・ループレーン・発射レーンを
保持し、ボールとの当たり判定（壁は反射、ランプ/ループは「入口→出口へのワープ」）
を行う。得点・演出は呼び出し側（scene）に「イベント」のリストとして返し、
スコア加算やSE再生はそこで行う。
"""

import pygame

from config import (
    PINBALL_TABLE_X, PINBALL_TABLE_Y, PINBALL_TABLE_W, PINBALL_TABLE_H,
    PINBALL_LANE_W, PINBALL_WALL_RESTITUTION,
    PINBALL_BUMPER_RADIUS, PINBALL_BUMPER_KICK,
    PINBALL_TARGET_W, PINBALL_TARGET_H,
    PINBALL_COLOR_BG, PINBALL_COLOR_WALL, PINBALL_COLOR_BUMPER,
    PINBALL_COLOR_BUMPER_LIT, PINBALL_COLOR_TARGET, PINBALL_COLOR_TARGET_LIT,
    PINBALL_COLOR_RAMP, PINBALL_COLOR_LOOP, PINBALL_COLOR_LANE,
)
from game_objects.pinball.physics import (
    circle_segment_collide, circle_circle_collide, reflect_velocity, point_in_rect,
)

FIELD_LEFT = PINBALL_TABLE_X
FIELD_TOP = PINBALL_TABLE_Y
FIELD_RIGHT_OUTER = PINBALL_TABLE_X + PINBALL_TABLE_W
LANE_LEFT = FIELD_RIGHT_OUTER - PINBALL_LANE_W
FIELD_RIGHT = LANE_LEFT
FIELD_BOTTOM = PINBALL_TABLE_Y + PINBALL_TABLE_H  # ドレインライン
LANE_BOTTOM = FIELD_BOTTOM - 20
FUNNEL_Y = FIELD_TOP + 380

LAUNCH_X = (LANE_LEFT + FIELD_RIGHT_OUTER) / 2
LAUNCH_Y = LANE_BOTTOM - 8

TARGET_HIT_FLASH = 0.25
BUMPER_HIT_FLASH = 0.2


class Table:
    def __init__(self):
        self.walls = [
            (FIELD_LEFT, FIELD_TOP, FIELD_RIGHT_OUTER, FIELD_TOP),           # 天井
            (FIELD_LEFT, FIELD_TOP, FIELD_LEFT, FUNNEL_Y),                    # 左壁
            (FIELD_LEFT, FUNNEL_Y, 325, 565),                                 # 左ファンネル
            (LANE_LEFT, FIELD_TOP + 30, LANE_LEFT, FUNNEL_Y),                 # 右壁（レーン仕切り上部）
            (LANE_LEFT, FUNNEL_Y, 478, 560),                                  # 右ファンネル
            (LANE_LEFT, FUNNEL_Y, LANE_LEFT, LANE_BOTTOM),                    # レーン仕切り下部
            (FIELD_RIGHT_OUTER, FIELD_TOP, FIELD_RIGHT_OUTER, LANE_BOTTOM),   # レーン外壁
            (LANE_LEFT, LANE_BOTTOM, FIELD_RIGHT_OUTER, LANE_BOTTOM),         # レーン床
        ]

        cx = (FIELD_LEFT + FIELD_RIGHT) / 2
        self.bumpers = [
            {"x": cx - 53, "y": FIELD_TOP + 140, "hit_flash": 0.0},
            {"x": cx + 53, "y": FIELD_TOP + 140, "hit_flash": 0.0},
            {"x": cx, "y": FIELD_TOP + 210, "hit_flash": 0.0},
        ]

        self.targets = [
            {"key": "A", "x": cx - 113, "y": FIELD_TOP + 70, "lit": False, "hit_flash": 0.0},
            {"key": "B", "x": cx, "y": FIELD_TOP + 60, "lit": False, "hit_flash": 0.0},
            {"key": "C", "x": cx + 113, "y": FIELD_TOP + 70, "lit": False, "hit_flash": 0.0},
        ]

        self.ramps = [
            {
                "entry": pygame.Rect(FIELD_LEFT + 4, FUNNEL_Y - 100, 44, 46),
                "exit": (FIELD_LEFT + 40, FIELD_TOP + 30),
                "exit_vel": (120.0, -380.0),
                "combo": 0,
                "flash": 0.0,
            },
            {
                "entry": pygame.Rect(FIELD_RIGHT - 48, FUNNEL_Y - 100, 44, 46),
                "exit": (FIELD_RIGHT - 40, FIELD_TOP + 30),
                "exit_vel": (-120.0, -380.0),
                "combo": 0,
                "flash": 0.0,
            },
        ]

        self.loop = {
            "entry": pygame.Rect(FIELD_RIGHT - 36, FIELD_TOP + 220, 32, 46),
            "exit": (FIELD_LEFT + 90, FIELD_TOP + 20),
            "exit_vel": (60.0, -350.0),
            "flash": 0.0,
        }

    # --- リセット（新しいターン開始時） ---------------------------------
    def reset_targets(self):
        for t in self.targets:
            t["lit"] = False

    def all_targets_lit(self):
        return all(t["lit"] for t in self.targets)

    # --- 当たり判定（呼び出し側でサブステップごとに呼ぶ） -----------------
    def resolve_wall_collisions(self, ball):
        for ax, ay, bx, by in self.walls:
            hit = circle_segment_collide(ball.x, ball.y, ball.radius, ax, ay, bx, by)
            if hit is None:
                continue
            nx, ny, penetration = hit
            ball.x += nx * penetration
            ball.y += ny * penetration
            ball.vx, ball.vy = reflect_velocity(
                ball.vx, ball.vy, nx, ny, PINBALL_WALL_RESTITUTION)

    def resolve_bumper_collisions(self, ball):
        events = []
        for b in self.bumpers:
            hit = circle_circle_collide(ball.x, ball.y, ball.radius, b["x"], b["y"],
                                        PINBALL_BUMPER_RADIUS)
            if hit is None:
                continue
            nx, ny, penetration = hit
            ball.x += nx * penetration
            ball.y += ny * penetration
            ball.vx = nx * PINBALL_BUMPER_KICK
            ball.vy = ny * PINBALL_BUMPER_KICK
            b["hit_flash"] = BUMPER_HIT_FLASH
            events.append(("bumper",))
        return events

    def resolve_target_collisions(self, ball):
        events = []
        half_w, half_h = PINBALL_TARGET_W / 2, PINBALL_TARGET_H / 2
        for t in self.targets:
            ax, ay = t["x"] - half_w, t["y"]
            bx, by = t["x"] + half_w, t["y"]
            hit = circle_segment_collide(ball.x, ball.y, ball.radius, ax, ay, bx, by)
            if hit is None:
                continue
            nx, ny, penetration = hit
            ball.x += nx * penetration
            ball.y += ny * penetration
            ball.vx, ball.vy = reflect_velocity(
                ball.vx, ball.vy, nx, ny, PINBALL_WALL_RESTITUTION)
            if not t["lit"]:
                t["lit"] = True
                t["hit_flash"] = TARGET_HIT_FLASH
                events.append(("target", t["key"]))
        return events

    def resolve_ramp_collisions(self, ball):
        events = []
        for r in self.ramps:
            if point_in_rect(ball.x, ball.y, r["entry"]):
                ball.x, ball.y = r["exit"]
                ball.vx, ball.vy = r["exit_vel"]
                r["combo"] += 1
                r["flash"] = 0.4
                events.append(("ramp", r["combo"]))
        return events

    def resolve_loop_collision(self, ball):
        r = self.loop
        if point_in_rect(ball.x, ball.y, r["entry"]):
            ball.x, ball.y = r["exit"]
            ball.vx, ball.vy = r["exit_vel"]
            r["flash"] = 0.4
            return [("loop",)]
        return []

    def update(self, dt):
        for b in self.bumpers:
            if b["hit_flash"] > 0:
                b["hit_flash"] = max(0.0, b["hit_flash"] - dt)
        for t in self.targets:
            if t["hit_flash"] > 0:
                t["hit_flash"] = max(0.0, t["hit_flash"] - dt)
        for r in self.ramps:
            if r["flash"] > 0:
                r["flash"] = max(0.0, r["flash"] - dt)
        if self.loop["flash"] > 0:
            self.loop["flash"] = max(0.0, self.loop["flash"] - dt)

    # --- 描画 -----------------------------------------------------------
    def draw(self, screen):
        table_rect = pygame.Rect(FIELD_LEFT, FIELD_TOP,
                                 FIELD_RIGHT_OUTER - FIELD_LEFT, LANE_BOTTOM - FIELD_TOP)
        pygame.draw.rect(screen, PINBALL_COLOR_BG, table_rect, border_radius=18)
        pygame.draw.rect(screen, PINBALL_COLOR_LANE,
                         (LANE_LEFT, FIELD_TOP + 30, FIELD_RIGHT_OUTER - LANE_LEFT,
                          LANE_BOTTOM - FIELD_TOP - 30))

        for ax, ay, bx, by in self.walls:
            pygame.draw.line(screen, PINBALL_COLOR_WALL, (ax, ay), (bx, by), 4)

        for r in self.ramps:
            color = PINBALL_COLOR_RAMP if r["flash"] <= 0 else (200, 255, 240)
            pygame.draw.rect(screen, color, r["entry"], border_radius=6)

        loop_color = PINBALL_COLOR_LOOP if self.loop["flash"] <= 0 else (255, 220, 255)
        pygame.draw.rect(screen, loop_color, self.loop["entry"], border_radius=6)

        for t in self.targets:
            half_w, half_h = PINBALL_TARGET_W / 2, PINBALL_TARGET_H / 2
            rect = pygame.Rect(int(t["x"] - half_w), int(t["y"] - half_h),
                               PINBALL_TARGET_W, PINBALL_TARGET_H)
            color = PINBALL_COLOR_TARGET_LIT if t["lit"] else PINBALL_COLOR_TARGET
            if t["hit_flash"] > 0:
                color = (255, 255, 255)
            pygame.draw.rect(screen, color, rect, border_radius=3)

        for b in self.bumpers:
            color = PINBALL_COLOR_BUMPER if b["hit_flash"] <= 0 else PINBALL_COLOR_BUMPER_LIT
            pygame.draw.circle(screen, color, (int(b["x"]), int(b["y"])), PINBALL_BUMPER_RADIUS)
            pygame.draw.circle(screen, (20, 10, 30), (int(b["x"]), int(b["y"])),
                               PINBALL_BUMPER_RADIUS, 2)
