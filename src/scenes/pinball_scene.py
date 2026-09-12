"""ピンボール。

マルチボール・ランプ・ループレーンを備えた本格構成の1台のみ実装する。
「クリア」は無いスコアアタック型（テトリス・スネーク・ぷよぷよと同方針）。

ボール数（ターン）とマルチボール中の同時ボール数は別概念として扱う：
`current_ball_number` がターン（残り球）、`active_balls` がその時点で場に
あるボールのリスト。マルチボールはターンを消費せず `active_balls` を増やす
だけなので、「3球」という総枠と矛盾しない（詳細は 2_design.md 参照）。
"""

import pygame

from scenes.base_scene import BaseScene
from game_objects.pinball.ball import Ball
from game_objects.pinball.flipper import Flipper
from game_objects.pinball.table import (
    Table, LAUNCH_X, LAUNCH_Y, FIELD_LEFT, FIELD_RIGHT, FIELD_BOTTOM,
)
from utils.synth_audio import SoundBank
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_YELLOW, COLOR_RED,
    PINBALL_START_BALLS, PINBALL_SUBSTEPS, PINBALL_LAUNCH_SPEED,
    PINBALL_BUMPER_SCORE, PINBALL_BUMPER_COMBO_WINDOW, PINBALL_BUMPER_COMBO_STEP,
    PINBALL_BUMPER_COMBO_MAX, PINBALL_TARGET_SCORE, PINBALL_RAMP_SCORE,
    PINBALL_RAMP_JACKPOT_COUNT, PINBALL_RAMP_JACKPOT_BONUS, PINBALL_LOOP_SCORE,
    PINBALL_MULTIBALL_BONUS, PINBALL_FLIPPER_PIVOT_Y, PINBALL_FLIPPER_GAP,
    PINBALL_COLOR_TARGET_LIT, PINBALL_COLOR_TARGET,
)

FIELD_CENTER_X = (FIELD_LEFT + FIELD_RIGHT) / 2


class PinballScene(BaseScene):
    HIGH_SCORE = 0  # 実行中のみ保持（他ゲームと同方針）

    def on_enter(self):
        super().on_enter()
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 60)
        self.sound = SoundBank()

        self.table = Table()
        self.left_flipper = Flipper(FIELD_CENTER_X - PINBALL_FLIPPER_GAP / 2,
                                    PINBALL_FLIPPER_PIVOT_Y, side=1)
        self.right_flipper = Flipper(FIELD_CENTER_X + PINBALL_FLIPPER_GAP / 2,
                                     PINBALL_FLIPPER_PIVOT_Y, side=-1)

        self.score = 0
        self.current_ball_number = 1
        self.bumper_combo = 0
        self.bumper_combo_timer = 0.0
        self.message = ""
        self.message_timer = 0.0

        self._start_turn()
        self.state = "intro"
        self.intro_timer = 1.4

    def _start_turn(self):
        self.table.reset_targets()
        self.active_balls = [Ball(LAUNCH_X, LAUNCH_Y)]
        self.state = "launch"

    # --- 入力 -----------------------------------------------------------
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "intro":
            self.state = "launch"
            return
        if self.state == "launch" and event.key == pygame.K_SPACE:
            ball = self.active_balls[0]
            ball.vy = -PINBALL_LAUNCH_SPEED
            ball.launched = True
            self.sound.play_se("launch")
            self.state = "play"

    # --- 更新 ---------------------------------------------------------
    def update(self, dt):
        if self.state == "intro":
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.state = "launch"
            return

        if self.state == "game_over":
            return

        keys = pygame.key.get_pressed()
        self.left_flipper.set_active(keys[pygame.K_LEFT] or keys[pygame.K_z])
        self.right_flipper.set_active(keys[pygame.K_RIGHT] or keys[pygame.K_x])
        self.left_flipper.update(dt)
        self.right_flipper.update(dt)

        if self.message_timer > 0:
            self.message_timer -= dt
        if self.bumper_combo_timer > 0:
            self.bumper_combo_timer -= dt
            if self.bumper_combo_timer <= 0:
                self.bumper_combo = 0

        self._update_balls(dt)
        self.table.update(dt)

        if self.state == "play" and not self.active_balls:
            self._end_turn()

        self._update_high()

    def _update_balls(self, dt):
        sub_dt = dt / PINBALL_SUBSTEPS
        for _ in range(PINBALL_SUBSTEPS):
            for ball in list(self.active_balls):
                ball.apply_gravity(sub_dt)
                ball.integrate(sub_dt)
                self.table.resolve_wall_collisions(ball)
                self.left_flipper.collide_ball(ball)
                self.right_flipper.collide_ball(ball)
                self._apply_events(self.table.resolve_bumper_collisions(ball))
                self._apply_events(self.table.resolve_target_collisions(ball))
                self._apply_events(self.table.resolve_ramp_collisions(ball))
                self._apply_events(self.table.resolve_loop_collision(ball))

            for ball in list(self.active_balls):
                if ball.y - ball.radius > FIELD_BOTTOM:
                    self.active_balls.remove(ball)
                    self.sound.play_se("drain")

            if self.state == "play" and self.table.all_targets_lit():
                self._trigger_multiball()

    def _apply_events(self, events):
        for event in events:
            kind = event[0]
            if kind == "bumper":
                self.bumper_combo = min(
                    self.bumper_combo + PINBALL_BUMPER_COMBO_STEP, PINBALL_BUMPER_COMBO_MAX)
                self.bumper_combo_timer = PINBALL_BUMPER_COMBO_WINDOW
                self.score += PINBALL_BUMPER_SCORE + self.bumper_combo
                self.sound.play_se("bumper")
            elif kind == "target":
                self.score += PINBALL_TARGET_SCORE
                self.sound.play_se("target")
            elif kind == "ramp":
                combo = event[1]
                self.score += PINBALL_RAMP_SCORE
                self.sound.play_se("ramp")
                if combo % PINBALL_RAMP_JACKPOT_COUNT == 0:
                    self.score += PINBALL_RAMP_JACKPOT_BONUS
                    self._show_message("JACKPOT!")
                    self.sound.play_se("jackpot")
            elif kind == "loop":
                self.score += PINBALL_LOOP_SCORE
                self.sound.play_se("loop")

    def _trigger_multiball(self):
        self.table.reset_targets()
        self.score += PINBALL_MULTIBALL_BONUS
        origin = self.active_balls[0] if self.active_balls else Ball(LAUNCH_X, LAUNCH_Y)
        for _ in range(2):
            self.active_balls.append(Ball(origin.x, origin.y, vx=0.0, vy=-300.0))
        self._show_message("MULTIBALL!")
        self.sound.play_se("multiball")

    def _end_turn(self):
        if self.current_ball_number < PINBALL_START_BALLS:
            self.current_ball_number += 1
            self._start_turn()
        else:
            self._update_high()
            self.request_scene("game_over", score=self.score)
            self.state = "game_over"

    def _show_message(self, text):
        self.message = text
        self.message_timer = 1.4

    def _update_high(self):
        if self.score > PinballScene.HIGH_SCORE:
            PinballScene.HIGH_SCORE = self.score

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen):
        screen.fill((10, 6, 20))
        self.table.draw(screen)
        self.left_flipper.draw(screen)
        self.right_flipper.draw(screen)
        for ball in self.active_balls:
            ball.draw(screen)

        self._draw_hud(screen)

        if self.state == "intro":
            self._draw_center(screen, "PINBALL", COLOR_YELLOW, self.big_font)
        elif self.message_timer > 0:
            self._draw_center(screen, self.message, COLOR_YELLOW, self.big_font, y=200)
        elif self.state == "launch":
            hint = self.font_small.render("SPACE: LAUNCH", True, COLOR_WHITE)
            screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)))

    def _draw_hud(self, screen):
        score = self.font.render(f"SCORE  {self.score:06d}", True, COLOR_WHITE)
        screen.blit(score, (16, 14))
        high = self.font.render(f"HIGH  {PinballScene.HIGH_SCORE:06d}", True, COLOR_RED)
        screen.blit(high, (16, 38))
        ball_no = self.font.render(
            f"BALL {self.current_ball_number}/{PINBALL_START_BALLS}", True, COLOR_WHITE)
        screen.blit(ball_no, (SCREEN_WIDTH - ball_no.get_width() - 16, 14))

        for i, t in enumerate(self.table.targets):
            color = PINBALL_COLOR_TARGET_LIT if t["lit"] else PINBALL_COLOR_TARGET
            pygame.draw.circle(screen, color, (18 + i * 22, SCREEN_HEIGHT - 20), 7)

    def _draw_center(self, screen, text, color, font, y=None):
        surf = font.render(text, True, color)
        cy = y if y is not None else SCREEN_HEIGHT // 2
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, cy)))
