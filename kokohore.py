import pyxel
import json

pyxel.init(128, 128, title="Kokohore WANWAN")
pyxel.load("kokohore.pyxres")  # イメージバンク0にタイルマップ
# pyxel.mouse(True)

# 定数
STAGE_WIDTH = 128 * 1
STAGE_HEIGHT = 128 * 1

# シーン番号の定義
SNO_TITLE = 0
SNO_STAGESET = 10
SNO_PLAY = 11
SNO_SFINISH = 12
SNO_GAMEOVER = 13
SNO_END = 20

# 音楽のパス
MUSIC_FILE = "music/game"

# 変数
scroll_x = 0
scroll_y = 0
x = 0
y = 0
u = 0
v = 0
dx = 0
dy = 0
pldir = 1
is_animating = 0
scene = SNO_TITLE  # ゲームの進行を管理する変数
tmr = 0  # シーン内でカウントするタイマー変数
treasure = 0
music = ""

# ステージデータ 下記タプルのリスト
#               0 タイルマップ番号(0-7)
#               1 ステージ左上 x座標
#               2 ステージ左上 y座標
#               3 ステージ幅
#               4 ステージ高さ
#               5 くんくん回数
#               6 掘り回数
#               7 開始位置
stagedata = [
    (0, 0 * 8, 0, 128 * 1, 128 * 1, 10, 4, (56, 56)),
    (0, 16 * 8, 0, 128 * 1, 128 * 1, 5, 5, (56, 56)),
    (0, 32 * 8, 0, 128 * 1, 128 * 1, 5, 5, (56, 56)),
    (0, 48 * 8, 0, 128 * 1, 128 * 1, 5, 3, (56, 56)),
    (0, 64 * 8, 0, 128 * 1, 128 * 1, 7, 3, (56, 56)),
]
stage = 0  # 現在のステージ
kunkun_limit = 99  # 嗅げる回数
dig_limit = 99  # 掘れる回数

PLY_TITLE_ANIM = [
    (16, 16),
    (0, 16),
    (32, 16),
    (0, 16),
    (16, 16),
    (0, 16),
    (32, 16),
    (0, 16),
    (0, 16),
    (0, 32),
    (16, 32),
    (0, 32),
    (16, 32),
    (0, 32),
    (16, 32),
    (0, 32),
    (16, 32),
    (0, 16),
    (0, 16),
    (0, 64),
    (16, 64),
    (0, 64),
    (16, 64),
    (0, 64),
    (16, 64),
    (0, 64),
    (16, 64),
    (0, 16),
    (0, 16),
    (0, 16),
]
PLY_ANIM = [(0, 16), (16, 16), (0, 16), (32, 16)]
PLY_KUNKUN_ANIM_1 = [(0, 32), (16, 32), (0, 32), (16, 32), (0, 32), (0, 48)]
PLY_KUNKUN_ANIM_2 = [(0, 32), (16, 32), (0, 32), (16, 32), (0, 32), (16, 48)]
PLY_KUNKUN_ANIM_3 = [(0, 32), (16, 32), (0, 32), (16, 32), (0, 32), (32, 48)]
PLY_DIG_ANIM = [(0, 64), (16, 64), (0, 64), (16, 64)]
PLY_END_ANIM = [(0, 32), (16, 32), (0, 32), (16, 32)]
FRAME_INTERVAL = 48
animation_timer = 0
ply_ani = 0

# 壁タイル
walltile = [
    (1, 0),
]

# 壁との接触判定用
chkpoint = [
    (6, 9),
    (10, 9),
    (6, 15),
    (10, 15),
]

# お宝の場所
tile_positions = []
treasure_position = (0, 0)

# 今まで掘った場所
dig_positions = []
# 新しく掘った場所
dig_position = (-1, -1)


# 初期化
def initgame():
    global stage, scroll_x, scroll_y, dig_positions, dig_position, treasure, music

    dig_positions.clear()
    dig_position = (-1, -1)
    stage = 0
    scroll_x = 0
    scroll_y = 0
    treasure = 0

    if pyxel.play_pos(0) is None:
        with open(f"./{MUSIC_FILE}.json", "rt") as fin:
            music = json.loads(fin.read())

    return


# ステージセット
def setstage():
    global x, y, scroll_x, scroll_y, stage, stage_width, stage_height, dig_positions, dig_position, tile_positions, treasure, kunkun_limit, dig_limit

    scroll_x = stagedata[stage][1]
    scroll_y = stagedata[stage][2]
    pos_x, pos_y = stagedata[stage][7]
    x = scroll_x + pos_x
    y = scroll_y + pos_y
    stage_width = scroll_x + stagedata[stage][3]
    stage_height = scroll_y + stagedata[stage][4]
    dig_positions.clear()
    dig_position = (-1, -1)
    tile_positions.clear()
    treasure = 0
    kunkun_limit = stagedata[stage][5]
    dig_limit = stagedata[stage][6]

    return


# 引数(進行先のx,進行先のy)
# return 0じゃなかったら進行不可
def chkwall(cx, cy):
    c = 0
    # 画面端に到達したとき
    # if cx < 0 or STAGE_WIDTH - 8 < cx:
    #     c = c + 1
    # ステージ端に到達したとき
    if cx < 0 or scroll_x + STAGE_WIDTH - 16 < cx:
        c = c + 1
    if scroll_y + STAGE_HEIGHT - 16 < cy:
        c = c + 1
    if scroll_y - 8 > cy:
        c = c + 1

    # 座標を8で割ると座標が出せる(タイルは8ドットで構成されているため)
    # // 切り捨て除算
    for cpx, cpy in chkpoint:
        # プレイヤーの衝突判定をする座標+進行先の座標//8すると進行先の座標が出せる
        xi = (cx + cpx) // 8
        yi = (cy + cpy) // 8
        # タイルマップの指定座標になんのタイルが使われているか確認
        # 壁系タイルだったら進行不可
        for wx, wy in walltile:
            if (wx, wy) == pyxel.tilemaps[0].pget(xi, yi):
                c = c + 1

    return c


def moveplayer():
    global scene, scroll_x, scroll_y, x, y, u, v, dx, dy, pldir, tmr, ply_ani, is_animating, animation_timer, kunkun_limit
    # 操作判定
    if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
        # -2まで徐々に変化
        if -2 < dx:
            dx = dx - 1
        pldir = -1
        ply_ani += 1
    elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
        # 2まで徐々に変化
        if dx < 2:
            dx = dx + 1
        pldir = 1
        ply_ani += 1
    else:
        # dx = int(dx * 0.7)  # 急には止まれない
        dx = 0  # 今回は慣性無し

    if pyxel.btn(pyxel.KEY_UP) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP):
        # -2まで徐々に変化
        if -2 < dy:
            dy = dy - 1
        # 横も押されているときにアニメーション速度が2倍になる対策
        if not (
            pyxel.btn(pyxel.KEY_LEFT)
            or pyxel.btn(pyxel.KEY_RIGHT)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)
        ):
            ply_ani += 1
    elif pyxel.btn(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN):
        # 2まで徐々に変化
        if dy < 2:
            dy = dy + 1
        # 横も押されているときにアニメーション速度が2倍になる対策
        if not (
            pyxel.btn(pyxel.KEY_LEFT)
            or pyxel.btn(pyxel.KEY_RIGHT)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)
        ):
            ply_ani += 1
    else:
        # dy = int(dy * 0.7)  # 急には止まれない
        dy = 0  # 今回は慣性無し

    if dx == 0 and dy == 0 and is_animating == 0:
        ply_ani = 0

    # 横方向の移動
    # sgn 正:1 0:0 負:-1(どっちに進もうとしているか)
    lr = pyxel.sgn(dx)
    ud = pyxel.sgn(dy)

    # キャラクターの移動
    # 分けることで同時押ししてても問題ない
    if 0 == chkwall(x + dx, y):
        x += dx
    if 0 == chkwall(x, y + dy):
        y += dy

    # くんくん
    if (
        (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A))
        and kunkun_limit > 0
        and is_animating == 0
    ):

        ply_ani = 0
        pyxel.play(3, 0)
        is_animating = check_treasure()
        kunkun_limit -= 1

    # 掘る
    if (
        (pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B))
        and dig_limit > 0
        and is_animating == 0
    ):

        ply_ani = 0
        pyxel.play(3, 1)
        is_animating = 4

        dig_treasure()

        if treasure == 1:
            scene = SNO_SFINISH
            tmr = 0


# 特定のタイルを探索して座標を取得する関数
# 穴タイルにランダムでお宝を配置
def set_treasure():
    global treasure_position, scroll_x, scroll_y
    for tile_y in range(scroll_y // 8, (scroll_y // 8) + 16):
        for tile_x in range(scroll_x // 8, (scroll_x // 8) + 16):
            tile = pyxel.tilemaps[0].pget(tile_x, tile_y)  # タイルマップの座標を取得
            if tile == (1, 1):  # 特定のタイルか判定
                # タイル座標からピクセル座標に変換
                pixel_x = tile_x * 8
                pixel_y = tile_y * 8
                tile_positions.append((pixel_x, pixel_y))

    treasure_position = tile_positions[pyxel.rndi(0, len(tile_positions) - 1)]
    # print(treasure_position)


def check_treasure():
    # print("お宝の位置")
    # print(treasure_position)
    # print("プレイヤx")
    # print(x)
    # print("プレイヤy")
    # print(y)
    # 土判定
    anim = 0

    pos_x, pos_y = treasure_position
    distance = abs(pos_x - (x + 8)) + abs(pos_y - (y + 15))
    # print("お宝までの距離")
    # print(distance)

    if distance <= 15:
        # 近い場合
        anim = 3
    elif distance <= 45:
        # ちょっと近い場合
        anim = 2
    else:
        # 遠い場合
        anim = 1

    return anim


def dig_treasure():
    global scene, dig_position, treasure, dig_limit, tmr
    # 土判定
    # for cpx, cpy in chkpoint:
    xi = (x + 8) // 8
    yi = (y + 15) // 8
    tile = pyxel.tilemaps[0].pget(xi, yi)
    # print(xi)
    # print(yi)
    # print(tile)
    if (1, 1) == tile:  # 割れ目
        # pyxel.tilemaps[0].pset(xi, yi, (0, 0))
        # item_list.append((xi, yi, tile))  # 消したアイテムを記録
        if (xi, yi) not in dig_positions:
            dig_position = (xi, yi)

            wx, wy = dig_position
            if (wx * 8, wy * 8) == treasure_position:
                treasure += 1
            # print(dig_positions)
            dig_limit -= 1

            if treasure == 0 and dig_limit == 0:
                scene = SNO_GAMEOVER
                tmr = 0


def update():
    global scene, stage, scroll_x, scroll_y, x, y, dx, dy, pldir, treasure, ply_ani, animation_timer, treasure_position, tmr, is_animating, music
    tmr += 1

    if scene == SNO_TITLE:
        ply_ani += 1
        if tmr == 1:
            initgame()

        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B):
            scene = SNO_STAGESET
            ply_ani = 0
            tmr = 0

    elif scene == SNO_STAGESET:
        if tmr == 1:
            setstage()
            set_treasure()
            scene = SNO_PLAY
            tmr = 0

            for ch, sound in enumerate(music):
                pyxel.sounds[ch].set(*sound)
                pyxel.play(ch, ch, loop=True)

            pyxel.load("kokohore.pyxres")

    elif scene == SNO_PLAY or scene == SNO_SFINISH or scene == SNO_GAMEOVER:

        if scene == SNO_PLAY:
            if is_animating == 0:
                moveplayer()

        if scene == SNO_SFINISH:

            if is_animating == 0:
                if FRAME_INTERVAL == tmr:
                    pyxel.stop()
                    pyxel.play(3, 2)

                # 5秒経過後にステージ更新(1秒30フレームなので3倍待つ)
                if 30 * 5 < tmr:
                    stage += 1  # 次のステージに変更
                    if stage < len(stagedata):
                        scene = SNO_STAGESET
                        tmr = 0
                    else:
                        # 最後のステージをクリアしたのでエンド画面へ
                        scene = SNO_END
                        tmr = 0

        if scene == SNO_GAMEOVER:
            if is_animating == 0:
                if FRAME_INTERVAL == tmr:
                    pyxel.stop()
                    pyxel.play(3, 3)

            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B):
                scene = SNO_TITLE
                pyxel.stop()
                ply_ani = 0
                tmr = 0

        if is_animating != 0:
            ply_ani += 1

            animation_timer += 1
            if animation_timer >= FRAME_INTERVAL:
                animation_timer = 0
                ply_ani = 0
                is_animating = 0  # アニメーション終了

        # デバッグ用
        # if pyxel.btnp(pyxel.KEY_X):
        #     scene = SNO_END
        #     pyxel.stop()
        #     tmr = 0
        # elif pyxel.btnp(pyxel.KEY_C):
        #     scene = SNO_GAMEOVER
        #     pyxel.stop()
        #     tmr = 0

    elif scene == SNO_END:
        ply_ani += 1

        if tmr == 1:
            pyxel.playm(0)

        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B):
            scene = SNO_TITLE
            pyxel.stop()
            ply_ani = 0
            tmr = 0

    # デバッグ用
    # if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
    #     print("x,y")
    #     print(pyxel.mouse_x)
    #     print(pyxel.mouse_y)

    #     print("wei")
    #     print(dig_positions)

    return


def draw():
    pyxel.cls(0)
    pyxel.camera()

    if scene == SNO_TITLE:
        # pyxel.text(0, 16, "TITLE", 7)
        pyxel.blt(30, 16, 1, 0, 0, 64, 32, 0)

        u, v = PLY_TITLE_ANIM[ply_ani // 8 % 29]
        pyxel.blt(53, 55, 0, u, v, 16, 16, 0)

        pyxel.text(36, 82, "PRESS [SPACE]", 7)
        pyxel.text(42, 90, "GAME START", 7)

        pyxel.text(28, 105, "2024 OSUSHI TABEZO", 7)

    if scene == SNO_PLAY or scene == SNO_SFINISH or scene == SNO_GAMEOVER:
        # マップ読み込み
        pyxel.bltm(0, 0, 0, scroll_x, scroll_y, pyxel.width, pyxel.height, 0)
        # pyxel.bltm(0, 0, 0, scroll_x, scroll_y, pyxel.width, pyxel.height, 0)

        pyxel.camera(scroll_x, scroll_y)

        # 穴
        for wx, wy in dig_positions:

            pyxel.blt((wx) * 8, wy * 8, 0, 0, 0, 8, 8, 1)
            pyxel.blt((wx) * 8, wy * 8, 0, 0, 1 * 8, 8, 8, 0)

        # 自機
        if is_animating == 0:
            # 新しく掘った部分があれば追加
            if (dig_position != (-1, -1)) and (dig_position not in dig_positions):
                dig_positions.append(dig_position)

            u, v = PLY_ANIM[ply_ani // 4 % 4]

        elif is_animating == 1:
            u, v = PLY_KUNKUN_ANIM_1[ply_ani // 8 % 6]
        elif is_animating == 2:
            u, v = PLY_KUNKUN_ANIM_2[ply_ani // 8 % 6]
        elif is_animating == 3:
            u, v = PLY_KUNKUN_ANIM_3[ply_ani // 8 % 6]
        elif is_animating == 4:
            u, v = PLY_DIG_ANIM[ply_ani // 8 % 4]

        pyxel.camera(scroll_x, scroll_y)
        pyxel.blt(x, y, 0, u, v, pldir * 16, 16, 0)

        if is_animating == 0 and scene == SNO_SFINISH:

            # クリア時
            pyxel.rect(20 + scroll_x, 16, 88, 48, 1)
            pyxel.rectb(20 + scroll_x, 16, 88, 48, 10)
            pyxel.blt(25 + scroll_x, 25, 0, 0, 80, 16, 16, 2)
            pyxel.text(50 + scroll_x, 30, "Find The Bone!", 7)
            pyxel.text(45 + scroll_x, 50, "STAGE CLEAR", 7)

        elif is_animating == 0 and scene == SNO_GAMEOVER:

            # ゲームオーバー時
            pyxel.rect(20 + scroll_x, 16, 88, 48, 1)
            pyxel.rectb(20 + scroll_x, 16, 88, 48, 10)
            pyxel.text(45 + scroll_x, 35, "GAME OVER", 7)
            pyxel.text(38 + scroll_x, 48, "PRESS [SPACE] ", 7)
            pyxel.text(38 + scroll_x, 56, "BACK TO TITLE", 7)

        # UI
        pyxel.text(2 + scroll_x, 2, "STAGE:" + str(stage + 1), 7)
        pyxel.text(83 + scroll_x, 2, "x" + str(kunkun_limit), 7)
        pyxel.text(115 + scroll_x, 2, "x" + str(dig_limit), 7)

        # デバッグ用
        # お宝が埋まっているタイルの位置を描画
        # pos_x, pos_y = treasure_position
        # pyxel.rectb(pos_x, pos_y, 8, 8, 10)  # 黄色い矩形で表示

        # # お宝掘り嗅ぎの数
        # pyxel.text(0 + scroll_x, 0, "TREASURE:" + str(treasure), 7)
        # pyxel.text(0 + scroll_x, 32, "KUNKUN:" + str(kunkun_limit), 7)
        # pyxel.text(0 + scroll_x, 40, "DIG:" + str(dig_limit), 7)
        # pyxel.text(0 + scroll_x, 48, "x:" + str(x) + " y:" + str(y), 7)
        # pyxel.text(
        #     0 + scroll_x, 56, "scx:" + str(scroll_x) + " scy:" + str(scroll_y), 7
        # )
        # pyxel.text(0 + scroll_x, 64, "TREASUREPOS:" + str(pos_x) + "," + str(pos_y), 7)

    if scene == SNO_END:

        u, v = PLY_END_ANIM[ply_ani // 8 % 4]

        pyxel.text(43, 25, "GAME CLEAR", 7)
        pyxel.text(32, 33, "CONGRATULATION!!", 7)
        pyxel.blt(40, 55, 0, u, v, 16, 16, 0)
        pyxel.blt(60, 55, 0, 16, 80, 8, 8, 0)
        pyxel.blt(68, 55, 0, 16, 80, 8, 8, 0)
        pyxel.blt(60, 63, 0, 16, 80, 8, 8, 0)
        pyxel.blt(68, 63, 0, 16, 80, 8, 8, 0)
        pyxel.blt(76, 63, 0, 16, 80, 8, 8, 0)

        pyxel.text(36, 82, "PRESS [SPACE]", 7)
        pyxel.text(36, 90, "BACK TO TITLE", 7)

    return


pyxel.run(update, draw)
