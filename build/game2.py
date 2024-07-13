import pyxel
import requests

SCENE_TITLE = 0
SCENE_PLAY = 1
SCENE_GAMEOVER = 2

NUM_STARS = 100
STAR_COLOR_HIGH = 12
STAR_COLOR_LOW = 5

PLAYER_WIDTH = 8
PLAYER_HEIGHT = 8
PLAYER_SPEED = 2

BULLET_WIDTH = 2
BULLET_HEIGHT = 8
BULLET_COLOR = 11
BULLET_SPEED = 4

ENEMY_WIDTH = 8
ENEMY_HEIGHT = 8
ENEMY_SPEED = 1.5

BLAST_START_RADIUS = 1
BLAST_END_RADIUS = 8
BLAST_COLOR_IN = 7
BLAST_COLOR_OUT = 10

enemies = []
bullets = []
blasts = []
texts = []


class TextSplash:
    def __init__(self, x, y, text):
        self.x = x
        self.y = y
        self.text = text
        self.timer = 30  # Show for 30 frames (1 second at 30fps)
        texts.append(self)

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            texts.remove(self)

    def draw(self):
        pyxel.text(self.x, self.y, self.text, 7)


def update_entities(entities):
    for entity in entities:
        entity.update()


def draw_entities(entities):
    for entity in entities:
        entity.draw()


def cleanup_entities(entities):
    for i in range(len(entities) - 1, -1, -1):
        if not entities[i].is_alive:
            del entities[i]


def load_bgm(msc, filename, snd1, snd2, snd3):
    import json

    with open(filename, "rt") as file:
        bgm = json.loads(file.read())
        pyxel.sounds[snd1].set(*bgm[0])
        pyxel.sounds[snd2].set(*bgm[1])
        pyxel.sounds[snd3].set(*bgm[2])
        pyxel.musics[msc].set([snd1], [snd2], [snd3])


class Background:
    def __init__(self):
        self.stars = []
        for i in range(NUM_STARS):
            self.stars.append(
                (
                    pyxel.rndi(0, pyxel.width - 1),
                    pyxel.rndi(0, pyxel.height - 1),
                    pyxel.rndf(1, 2.5),
                )
            )

    def update(self):
        for i, (x, y, speed) in enumerate(self.stars):
            y += speed
            if y >= pyxel.height:
                y -= pyxel.height
            self.stars[i] = (x, y, speed)

    def draw(self):
        for x, y, speed in self.stars:
            pyxel.pset(x, y, STAR_COLOR_HIGH if speed > 1.8 else STAR_COLOR_LOW)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = PLAYER_WIDTH
        self.h = PLAYER_HEIGHT
        self.is_alive = True
        self.touch_start_x = None

    def update(self):
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
            self.x -= PLAYER_SPEED
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
            self.x += PLAYER_SPEED
        if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP):
            self.y -= PLAYER_SPEED
        if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN):
            self.y += PLAYER_SPEED

        # Touch input to move the player
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            if self.touch_start_x is None:
                self.touch_start_x = pyxel.mouse_x
            self.x = pyxel.mouse_x - PLAYER_WIDTH / 2
        else:
            self.touch_start_x = None

        self.x = max(self.x, 0)
        self.x = min(self.x, pyxel.width - self.w)
        self.y = max(self.y, 0)
        self.y = min(self.y, pyxel.height - self.h)

        # Fire bullets continuously while holding touch
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            if pyxel.frame_count % 5 == 0:  # Adjust the firing rate here
                Bullet(
                    self.x + (PLAYER_WIDTH - BULLET_WIDTH) / 2,
                    self.y - BULLET_HEIGHT / 2,
                )
                pyxel.play(3, 0)

    def draw(self):
        pyxel.blt(self.x, self.y, 0, 0, 0, self.w, self.h, 0)
        pyxel.text(self.x - 10, self.y + 10, "Comviva", 7)  # Text below the shooter


class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = BULLET_WIDTH
        self.h = BULLET_HEIGHT
        self.is_alive = True
        bullets.append(self)

    def update(self):
        self.y -= BULLET_SPEED
        if self.y + self.h - 1 < 0:
            self.is_alive = False

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, BULLET_COLOR)


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = ENEMY_WIDTH
        self.h = ENEMY_HEIGHT
        self.dir = 1
        self.timer_offset = pyxel.rndi(0, 59)
        self.is_alive = True
        enemies.append(self)

    def update(self):
        if (pyxel.frame_count + self.timer_offset) % 60 < 30:
            self.x += ENEMY_SPEED
            self.dir = 1
        else:
            self.x -= ENEMY_SPEED
            self.dir = -1
        self.y += ENEMY_SPEED
        if self.y > pyxel.height - 1:
            self.is_alive = False

    def draw(self):
        pyxel.blt(self.x, self.y, 0, 8, 0, self.w * self.dir, self.h, 0)


class Blast:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = BLAST_START_RADIUS
        self.is_alive = True
        blasts.append(self)

    def update(self):
        self.radius += 1
        if self.radius > BLAST_END_RADIUS:
            self.is_alive = False

    def draw(self):
        pyxel.circ(self.x, self.y, self.radius, BLAST_COLOR_IN)
        pyxel.circb(self.x, self.y, self.radius, BLAST_COLOR_OUT)


class App:
    def __init__(self):
        pyxel.init(120, 160, title="MobiLytix Rewards - Comviva")

        # Original Shooter Sprite
        pyxel.images[0].set(
            0,
            0,
            [
                "00c00c00",
                "0c7007c0",
                "0c7007c0",
                "c703b07c",
                "77033077",
                "785cc587",
                "85c77c58",
                "0c0880c0",
            ],
        )

        # Original Alien Sprite
        pyxel.images[0].set(
            8,
            0,
            [
                "00088000",
                "00ee1200",
                "08e2b180",
                "02882820",
                "00222200",
                "00012280",
                "08208008",
                "80008000",
            ],
        )

        pyxel.sounds[0].set("a3a2c1a1", "p", "7", "s", 5)
        pyxel.sounds[1].set("a3a2c2c2", "n", "7742", "s", 10)
        load_bgm(0, "assets/bgm_title.json", 2, 3, 4)
        load_bgm(1, "assets/bgm_play.json", 5, 6, 7)
        self.scene = SCENE_TITLE
        self.score = 0
        self.earned_mb = 0  # Track MB earned
        self.game_over = False  # Track game over state
        self.background = Background()
        self.player = Player(pyxel.width / 2, pyxel.height - 20)
        pyxel.playm(0, loop=True)
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btn(pyxel.KEY_Q):
            pyxel.quit()

        self.background.update()
        if self.scene == SCENE_TITLE:
            self.update_title_scene()
        elif self.scene == SCENE_PLAY:
            self.update_play_scene()
        elif self.scene == SCENE_GAMEOVER:
            self.update_gameover_scene()

    def update_title_scene(self):
        if (
            pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X)
            or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        ):
            self.scene = SCENE_PLAY
            pyxel.playm(1, loop=True)

    def update_play_scene(self):
        if pyxel.frame_count % 6 == 0:
            Enemy(pyxel.rndi(0, pyxel.width - ENEMY_WIDTH), 0)

        for enemy in enemies:
            for bullet in bullets:
                if (
                    enemy.x + enemy.w > bullet.x
                    and bullet.x + bullet.w > enemy.x
                    and enemy.y + enemy.h > bullet.y
                    and bullet.y + bullet.h > enemy.y
                ):
                    enemy.is_alive = False
                    bullet.is_alive = False
                    blasts.append(
                        Blast(enemy.x + ENEMY_WIDTH / 2, enemy.y + ENEMY_HEIGHT / 2)
                    )
                    TextSplash(
                        enemy.x + ENEMY_WIDTH / 2, enemy.y + ENEMY_HEIGHT / 2, "1MB"
                    )
                    pyxel.play(2, 1, resume=True)
                    self.score += 10
                    self.earned_mb += 1  # Increment MB earned

        for enemy in enemies:
            if (
                self.player.x + self.player.w > enemy.x
                and enemy.x + enemy.w > self.player.x
                and self.player.y + self.player.h > enemy.y
                and enemy.y + enemy.h > self.player.y
            ):
                enemy.is_alive = False
                blasts.append(
                    Blast(
                        self.player.x + PLAYER_WIDTH / 2,
                        self.player.y + PLAYER_HEIGHT / 2,
                    )
                )
                pyxel.stop()
                pyxel.play(3, 1)
                self.scene = SCENE_GAMEOVER
                self.game_over = True  # Set game over state

        self.player.update()
        update_entities(bullets)
        update_entities(enemies)
        update_entities(blasts)
        update_entities(texts)
        cleanup_entities(enemies)
        cleanup_entities(bullets)
        cleanup_entities(blasts)

    def update_gameover_scene(self):
        update_entities(bullets)
        update_entities(enemies)
        update_entities(blasts)
        cleanup_entities(enemies)
        cleanup_entities(bullets)
        cleanup_entities(blasts)

        if (
            pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X)
            or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        ):
            self.scene = SCENE_PLAY
            self.player.x = pyxel.width / 2
            self.player.y = pyxel.height - 20
            self.score = 0
            self.earned_mb = 0  # Reset MB earned
            self.game_over = False  # Reset game over state
            enemies.clear()
            bullets.clear()
            blasts.clear()
            texts.clear()
            pyxel.playm(1, loop=True)

    def draw(self):
        pyxel.cls(0)
        self.background.draw()
        if self.scene == SCENE_TITLE:
            self.draw_title_scene()
        elif self.scene == SCENE_PLAY:
            self.draw_play_scene()
        elif self.scene == SCENE_GAMEOVER:
            self.draw_gameover_scene()
        pyxel.text(39, 4, f"{self.earned_mb} MB", 7)

    def draw_title_scene(self):
        pyxel.text(20, 66, "MobiLytix Rewards", pyxel.frame_count % 16)
        pyxel.text(43, 76, "by Comviva", pyxel.frame_count % 16)
        pyxel.text(20, 86, "Earn 1MB data", 7)
        pyxel.text(20, 96, "for every alien killed!", 7)
        pyxel.text(31, 126, "Touch to Play", 13)

    def draw_play_scene(self):
        self.player.draw()
        draw_entities(bullets)
        draw_entities(enemies)
        draw_entities(blasts)
        draw_entities(texts)

    def draw_gameover_scene(self):
        draw_entities(bullets)
        draw_entities(enemies)
        draw_entities(blasts)
        pyxel.text(43, 66, "GAME OVER", 8)
        pyxel.text(15, 76, f"Congrats! You have earned", 7)
        pyxel.text(30, 86, f"{self.earned_mb} MB of data!", 7)
        pyxel.text(31, 126, "Touch to Play", 13)
        if pyxel.frame_count % 30 < 15:
            # Add Blinking Text in 2 lines -
            # Powered By
            # MobiLytix Rewards
            pyxel.text(30, 106, "Powered By", 7)
            pyxel.text(30, 116, "MobiLytix Rewards", 7)
        # Add the game over logic to call the API
        if self.game_over:
            self.call_api(self.earned_mb)
            self.game_over = False  # Ensure the API is called only once

    def call_api(self, points_earned):
        url = "https://webhook.site/0b0af263-f235-49c4-a6bd-51c224822067"
        payload = {"mobile": "9902081508", "points_earned": points_earned}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Error sending API request: {e}")


App()
