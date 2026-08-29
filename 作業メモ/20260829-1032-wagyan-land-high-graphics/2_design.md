# 実装方針・影響範囲

## 全体方針

- 当たり判定・位置計算・ステート管理などのロジックには一切手を入れない。
  変更対象は各モジュールの `draw()` 系メソッドのみ。
- スプライトは「ドット絵を低解像度で1ドットずつ定義 → 整数倍に拡大 → PNG保存」で
  作る。既存のオブジェクトサイズ（例: プレイヤー 30×32）にそのまま1:1でドットを
  敷き詰めると図形描画とほぼ変わらない見た目になるため、**低解像度キャンバスで
  デザインしてから nearest-neighbor で2倍前後に拡大**し、ドット感のある質感を
  意図的に出す。
- 生成は実行時ではなく**事前生成**。生成スクリプトを実行して PNG を
  `src/assets/wagyan/` に書き出し、その PNG をゲーム本体がロードする
  （PNG 自体もリポジトリにコミットし、通常のプレイでは生成スクリプトの実行は不要）。
- 追加ライブラリなし。PNG の書き出し・読み込みは pygame 標準機能
  （`pygame.image.save` / `pygame.image.load`）のみで行う（`synth_audio.py` が
  numpy を使わない方針としているのと同様、依存を増やさない）。

## ディレクトリ構成

```
src/
├── assets/
│   └── wagyan/              # 生成済み PNG（コミット対象）
│       ├── wagyan_stand.png
│       ├── wagyan_walk1.png
│       ├── wagyan_walk2.png
│       ├── wagyan_air.png
│       ├── wagyan_dying.png
│       ├── enemy_normal.png
│       ├── enemy_stunned1.png
│       ├── enemy_stunned2.png
│       ├── ground_tile.png
│       ├── platform_tile.png
│       ├── wagyanizer.png
│       ├── goal.png
│       ├── boss_dr_devil.png
│       └── boss_wagyan_faceoff.png
├── tools/
│   └── generate_wagyan_sprites.py   # ドット絵定義 → PNG 書き出しスクリプト
└── utils/
    └── sprite_loader.py             # PNG 読み込み・キャッシュの共通ヘルパー
```

`src/tools/` は本作業で新設する（生成スクリプト置き場。実行時には import されない）。

## 生成スクリプト（`src/tools/generate_wagyan_sprites.py`）

- 単独実行スクリプト：`python src/tools/generate_wagyan_sprites.py`
- 各スプライトを「文字グリッド（行の文字列リスト）＋ パレット（文字→RGBA）」で
  定義する。空白は透過。
- `pygame.Surface((w, h), pygame.SRCALPHA)` にキャラクタごと `set_at` で色を置き、
  `pygame.transform.scale`（`scale_by` ではなく最近傍拡大）で例えば2倍に拡大してから
  `pygame.image.save()` で PNG 保存。
- 実行には描画サーフェスが必要な環境があるため、スクリプト冒頭で
  `SDL_VIDEODRIVER=dummy` を設定し `pygame.display.init()` する
  （既存 `synth_audio.py` の「表示なし環境でも壊れない」方針と揃える）。
- 出力先ディレクトリが無ければ作成する。

## スプライト一覧

| ファイル | 用途 | サイズ目安（拡大後） | 元図形の対応 |
|---|---|---|---|
| `wagyan_stand.png` | ワギャン静止 | 30×32 | 現 `_build_sprite()` の静止コマ |
| `wagyan_walk1.png` / `wagyan_walk2.png` | ワギャン歩行2コマ | 30×32 | 現 `swing` の左右2パターン |
| `wagyan_air.png` | ジャンプ中 | 30×32 | 現 `airborne` 分岐 |
| `wagyan_dying.png` | やられ演出 | 30×32 | 現状と同様、実行時に `pygame.transform.rotate` を適用して流用 |
| `enemy_normal.png` | 敵・通常 | 30×26 | 現 `WAGYAN_COLOR_ENEMY` の楕円 |
| `enemy_stunned1.png` / `enemy_stunned2.png` | 敵・しびれ中（目回り2コマ） | 30×26 | 現 `paralyzed` 時の目回り演出 |
| `ground_tile.png` | 地面タイル（40×40、敷き詰め用） | 40×40 | 現 `_draw_block` の地面版 |
| `platform_tile.png` | 浮遊足場タイル（40×40、敷き詰め用） | 40×40 | 現 `_draw_block` の platform 版 |
| `wagyanizer.png` | ワギャナイザー（拡声器） | 28×28 | 現 `_draw_wagyanizers` の多角形 |
| `goal.png` | ゴール（旗＋ポール） | 50×130 | 現 `_draw_goal` |
| `boss_dr_devil.png` | ボス戦：Dr.デビル立ち絵 | 80×90 | 現 `_draw_boss_scene` 内の楕円+円+三角 |
| `boss_wagyan_faceoff.png` | ボス戦：対峙ワギャン | 36×42 | 現 `_draw_boss_scene` 内のワギャン簡易表示 |

中州（island）は地面と同じ `ground_tile.png` を敷き詰めて描画し、専用画像は作らない
（現行コードでも `_draw_block` を共用しているため踏襲）。

## `src/utils/sprite_loader.py`

```python
_cache = {}

def load_wagyan_sprite(name):
    """src/assets/wagyan/{name}.png を読み込み convert_alpha() してキャッシュする。"""
```

- モジュール内 dict でパスをキーにキャッシュし、シーン再入場のたびに毎回ディスク
  読み込みしないようにする。
- 敵・アイテム等サイズが固定のスプライトはそのまま返し、拡大縮小は行わない
  （生成時点で最終サイズに揃える）。

## 各ファイルの変更内容

### `player.py`
- `_build_sprite()` を削除し、状態（`ground`/`air`/`dying`）と `walk_anim` の
  コマ判定から `wagyan_stand` / `wagyan_walk1` / `wagyan_walk2` / `wagyan_air` を
  選ぶだけの処理に置き換える。
- `draw()` 内の「`facing < 0` で `flip`」「`dying` で `rotate`」ロジックはそのまま
  流用する（画像に対しても同じ変換が使えるため）。

### `enemy.py`
- `draw()` 内の `pygame.draw.ellipse` 等を `enemy_normal` /
  `enemy_stunned1` / `enemy_stunned2` の切り替えに置き換える。
- しびれ解除直前の点滅（`blink_off`）は、既存同様「通常スプライトと交互に切替える」
  ことで表現する（色を戻すのではなくスプライトを戻す）。
- 目回り2コマは `self.anim` に応じて一定間隔でトグルする（現在の
  `math.cos/sin` による連続回転から簡略化。しびれ中は演出用の別コマが交互に
  出るだけでも十分に「目を回している」感が出るため許容範囲とする）。

### `stage.py`
- `_draw_block`：`base`/`dark` 矩形塗りを、`ground_tile.png` または
  `platform_tile.png` を rect の範囲にタイル状に敷き詰めるループへ置き換える
  （`for tx in range(rect.left, rect.right, tile_w): for ty in range(rect.top, rect.bottom, tile_h): blit(...)`）。
  画面外クリップの早期 return は現行のまま維持。
- `_draw_wagyanizers`：多角形描画を `wagyanizer.png` の blit に置き換える。
- `_draw_goal`：矩形＋多角形描画を `goal.png` 1枚の blit に置き換える。

### `wagyan_land_scene.py`
- `_draw_boss_scene` 内の Dr.デビル（楕円+円+三角）を `boss_dr_devil.png`、
  対峙ワギャン（楕円+円2つ）を `boss_wagyan_faceoff.png` の blit に置き換える。
  背景の単色 `fill` とアリーナ床の矩形はスコープ外（今回は据え置き）。
- HUD 内の残機アイコン（`pygame.draw.ellipse` の小さいワギャン）は
  `wagyan_stand.png` を縮小 blit に置き換える。

## 影響範囲

- 見た目のみの変更。`solid_rects`・当たり判定・ステートマシン・スコア・SE呼び出し
  タイミングには触れない。
- `config.py` の `WAGYAN_COLOR_*` 定数は生成スクリプトのパレット決定に使うが、
  ランタイム側（各 draw メソッド）ではほぼ参照しなくなる
  （HUD 文字色・音波エフェクトの色など、図形のまま残す一部は除く）。
- 既存の受け入れ済みテスト（起動確認・通しプレイ）を再実行し、デグレがないことを
  確認する。

## 動作確認方法

- `SDL_VIDEODRIVER=dummy` でのヘッドレス起動 + キー入力スクリプトで
  スタート〜ゴール〜ボス戦〜クリアまで例外なく通ることを確認する
  （既存の受け入れ条件と同じ方式）。
- 生成した PNG 単体、および実プレイ画面のスクリーンショットを保存し、目視で
  見た目を確認する。
