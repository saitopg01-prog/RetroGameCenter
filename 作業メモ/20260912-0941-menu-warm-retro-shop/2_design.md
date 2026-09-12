# 実装方針・影響範囲

## DONKEY KONG カード削除

`src/scenes/menu_scene.py` の `GAMES` から以下の1行のみを削除する（他は変更しない）。

```python
("DONKEY KONG", "donkey_kong", "donkey_kong"),
```

`donkey_kong_scene.py` / `main.py` のシーン登録 / `menu_thumbnails.py` の
`_draw_donkey_kong` はそのまま残す。`DONKEY KONG '81` は別エントリなので影響なし。

## 配色（`config.py` に `MENU_` 接頭辞で追加）

既存の `COLOR_GIRDER` 等、他ゲームが使う定数は変更しない。メニュー専用の新規定数を
追加する。

| 定数 | 値 (RGB) | 用途 |
|---|---|---|
| `MENU_COLOR_BG_TOP` | (60, 38, 22) | 背景グラデーション上端（焦げ茶） |
| `MENU_COLOR_BG_BOTTOM` | (120, 70, 30) | 背景グラデーション下端（明るい琥珀茶） |
| `MENU_COLOR_FRAME` | (110, 70, 40) | 外枠（木目の板） |
| `MENU_COLOR_FRAME_DARK` | (70, 42, 24) | 外枠の木目ライン・カード枠線 |
| `MENU_COLOR_TITLE` | (255, 170, 60) | タイトル文字（オレンジ） |
| `MENU_COLOR_TITLE_SHADOW` | (120, 60, 20) | タイトル影 |
| `MENU_COLOR_TEXT` | (255, 224, 170) | 通常文字（クリーム） |
| `MENU_COLOR_CARD_BAND` | (90, 55, 30) | カード下部帯（プレイ可） |
| `MENU_COLOR_CARD_BAND_LOCKED` | (60, 40, 28) | カード下部帯（COMING SOON） |
| `MENU_COLOR_GLOW` | (255, 170, 60) | 選択中カードの発光基準色 |
| `MENU_COLOR_BULB_ON` | (255, 200, 90) | イルミネーション：点灯 |
| `MENU_COLOR_BULB_OFF` | (110, 80, 50) | イルミネーション：消灯 |
| `MENU_COLOR_BULB_WIRE` | (40, 25, 15) | イルミネーションの電線 |

`COLOR_GRAY`（COMING SOON のラベル色）は変更せず流用する（無機質な「準備中」感を
むしろ活かす）。

## `menu_scene.py` の変更内容

### 背景グラデーション
`on_enter()` で `SCREEN_WIDTH × SCREEN_HEIGHT` の `Surface` を1度だけ生成し、
上端 `MENU_COLOR_BG_TOP` → 下端 `MENU_COLOR_BG_BOTTOM` の線形補間で1行ずつ塗って
`self.bg_surface` にキャッシュする（毎フレーム計算しない）。`draw()` 冒頭の
`screen.fill(COLOR_BLACK)` をこの `self.bg_surface` の blit に置き換える。

### 外枠（木目調）
`_draw_border` を「太めの帯（`MENU_COLOR_FRAME`）＋ 数本の濃い木目ライン
（`MENU_COLOR_FRAME_DARK`）」に置き換える。四辺の帯を `pygame.draw.rect` の
`width` 指定で描き、各辺に沿って `pygame.draw.line` で2〜3本の木目ラインを足す。

### タイトル・文字色
- タイトル影：`COLOR_RED` → `MENU_COLOR_TITLE_SHADOW`
- タイトル本体：`COLOR_YELLOW` → `MENU_COLOR_TITLE`
- サブタイトル・操作ヒント：`COLOR_WHITE` → `MENU_COLOR_TEXT`

### カード
- 下部帯：`(34,34,44)` / `(24,24,30)` → `MENU_COLOR_CARD_BAND` /
  `MENU_COLOR_CARD_BAND_LOCKED`
- 非選択カードの枠線色：`(70,70,85)` → `MENU_COLOR_FRAME_DARK`
  （画面全体の暖色トーンに合わせる、地味な範囲の調整）
- 選択中カードの発光：現在の黄色パルス `(glow, glow, 40)` を、
  `MENU_COLOR_GLOW` を基準に明滅させる形に変更する
  （`brightness = 0.55 + 0.45 * abs(sin(time*4))` を各チャンネルへ掛ける）
- ラベル色（選択中/プレイ可/準備中）は現状の使い分けロジックを維持しつつ、
  地の色を `MENU_COLOR_TEXT` 系に差し替える

### 電球イルミネーション（新規）
`_draw_bulbs(screen)` を新設し、`draw()` 内でタイトルより前（背景の直後）に呼ぶ。

- 画面上端付近（外枠の内側、`y≈34`）に電球を横一列に並べる（本数はおよそ
  16〜20個、画面幅に応じて等間隔）
- 各電球の x は等間隔、y はゆるい弧を描く（中央がわずかに垂れ下がる
  `sin` カーブ）ことで「電飾の配線」らしい見た目にする
- 電球同士を `MENU_COLOR_BULB_WIRE` の線でつなぐ（先に線を描いてから円を重ねる）
- 点灯／消灯は `self.time` と電球ごとのインデックスをずらした `sin` 判定で、
  マーキーライトのように順番に点滅して見えるようにする
- 点灯中の電球は外側にもう1回り薄い縁取りの円を重ねて簡易的な「光暈」を出す

## 影響範囲

- ゲームロジック・入力処理・シーン遷移（`handle_input` / `update` の判定部分）には
  触れない。変更は `GAMES` リストと描画関連のみ。
- 他ゲームのシーン・サムネイル描画・`config.py` の既存定数には影響しない
  （すべて `MENU_` 接頭辞の新規追加）。

## 動作確認方法

- `python src/main.py` を実際に起動し、メニュー画面を目視で確認する
  （配色・電飾アニメーション・DONKEY KONG カードが表示されないこと）
- ヘッドレス実行（`SDL_VIDEODRIVER=dummy`）で `MenuScene` の `update`/`draw` を
  数フレーム回し、例外が出ないことを確認する
