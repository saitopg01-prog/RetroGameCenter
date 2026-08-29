"""ワギャンランド用スプライト（PNG）の読み込み・キャッシュ。

生成元は `src/tools/generate_wagyan_sprites.py`。素材は
`src/assets/wagyan/{name}.png` に配置されている前提。
"""

import os

import pygame

_ASSET_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "wagyan")
)

_cache = {}


def load_wagyan_sprite(name):
    """`name`（拡張子なし）の PNG を読み込み、convert_alpha 済みでキャッシュして返す。"""
    surf = _cache.get(name)
    if surf is None:
        path = os.path.join(_ASSET_DIR, f"{name}.png")
        surf = pygame.image.load(path)
        if pygame.display.get_surface() is not None:
            surf = surf.convert_alpha()
        _cache[name] = surf
    return surf
