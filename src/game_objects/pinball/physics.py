"""ピンボールの当たり判定・反射計算の共通ヘルパー。

自作のシンプルな2D物理（専用エンジンは使わない）：
円（ボール）と線分（壁・フリッパー）、円と円（バンパー）の衝突判定・反射のみ。
"""

import math


def closest_point_on_segment(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return ax, ay
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    return ax + dx * t, ay + dy * t


def reflect_velocity(vx, vy, nx, ny, restitution):
    """速度 (vx, vy) を法線 (nx, ny)（正規化済み）で反射する。"""
    dot = vx * nx + vy * ny
    if dot > 0:
        return vx, vy  # すでに法線方向へ離れつつあるなら何もしない
    factor = (1 + restitution) * dot
    return vx - factor * nx, vy - factor * ny


def circle_segment_collide(cx, cy, radius, ax, ay, bx, by):
    """円と線分（太さ込み）が衝突していれば (nx, ny, penetration) を返す。"""
    qx, qy = closest_point_on_segment(cx, cy, ax, ay, bx, by)
    dx, dy = cx - qx, cy - qy
    dist = math.hypot(dx, dy)
    if dist >= radius:
        return None
    if dist < 1e-6:
        return 0.0, -1.0, radius
    nx, ny = dx / dist, dy / dist
    return nx, ny, radius - dist


def circle_circle_collide(ax, ay, ar, bx, by, br):
    dx, dy = ax - bx, ay - by
    dist = math.hypot(dx, dy)
    min_dist = ar + br
    if dist >= min_dist:
        return None
    if dist < 1e-6:
        return 0.0, -1.0, min_dist
    nx, ny = dx / dist, dy / dist
    return nx, ny, min_dist - dist


def point_in_rect(px, py, rect):
    return rect.left <= px <= rect.right and rect.top <= py <= rect.bottom
