import math
import random
import sys
import time
from typing import Any

import pygame as pg
from pygame.sprite import AbstractGroup


WIDTH = 1200  # ゲームウィンドウの幅
HEIGHT = 600  # ゲームウィンドウの高さ


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，戦闘機，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：戦闘機SurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクターに関するクラス
    """
    delta = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        画像Surfaceを生成する
        引数1 num：画像ファイル名の番号
        引数2 xy：画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        shield_img = pg.image.load("ex05/fig/shield.png")
        img = pg.transform.flip(img0, True, False)
        self.imgs = {
            (+1, 0): img,
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),
            (-1, 0): img0,
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

        self.shield = shield_img
        self.shield_timer = 0  # shieldの発生時間を管理するタイマー
        self.shield_rect = self.rect.inflate(120, 120).move(-25, -25)  # shieldの当たり判定領域を設定

    def change_img(self, num: int, screen: pg.Surface):
        """
        画像を切り替え，画面に転送する
        引数1 num：画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じて戦闘機を移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed * mv[0], +self.speed * mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed * mv[0], -self.speed * mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)

        # shieldの表示
        if self.shield_timer > 0:
            shield_rect = self.shield.get_rect()
            shield_rect.center = self.rect.center
            shield_rect.move_ip(5, -10)
            screen.blit(self.shield, shield_rect)
            self.shield_timer -= 1

    def get_direction(self) -> tuple[int, int]:
        return self.dire

    def collides_with_shield(self, other_rect: pg.Rect) -> bool:
        return self.shield_rect.colliderect(other_rect)
    
    


class  Atack(pg.sprite.Sprite):
    
    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象の戦闘機
        """
        saize = [0.25,0.05,0.15]
        super().__init__()
        img = pg.image.load("ex05/fig/bomb.png")
        self.image = pg.transform.rotozoom(img,1,random.choice(saize))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class BossBomb(pg.sprite.Sprite):

    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, boss: "BossEnemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象の戦闘機
        """
        super().__init__()
        size = 60  # 爆弾円の半径
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((120, 120))
        self.state = boss
        pg.draw.circle(self.image, color, (size, size), size)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(boss.rect, bird.rect)  
        self.rect.centerx = boss.rect.centerx
        self.rect.centery = boss.rect.centery+boss.rect.height/2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つ戦闘機
        """
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Atack|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するAtackまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex05/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"ex05/fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy

class BossEnemy(pg.sprite.Sprite):
    """
    Bossに関するクラス
    """
    imgs = pg.image.load(f"ex04/fig/alien1.png")
    boss= pg.transform.scale(imgs,(400,225))
    def __init__(self):
        super().__init__()
        self.image=__class__.boss
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH/2, 0
        self.vy=+5
        self.bound=70
        self.state="down"
        self.interval = 30

    def update(self):
        """
        ボスを速度ベクトルself.vyに基づき移動（降下）させる
        停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy

class Nuisance(pg.sprite.Sprite):
    """
    お邪魔ボールに関するクラス
    """

    imgs = [pg.image.load(f"ex05/fig/nsc_b{i}.png") for i in range(1, 4)]

    def __init__(self, life: int):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.imgs = [self.image, pg.transform.flip(self.image, 1, 0)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +1
        self.bound = random.randint(50, HEIGHT)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.life = life

    def update(self):
        """
        お邪魔ボールを速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        経過時間lifeに応じて消滅し画像を切り替えることで動きのあるキャラクターのようにする
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy

        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Cure(pg.sprite.Sprite):
    """
    速度回復アイテムに関するクラス
    """
    def __init__(self, life: int):
        super().__init__()
        img = pg.image.load("ex05/fig/item_cure.png")
        self.image = img
        self.rect = self.image.get_rect()
        self.recdct = WIDTH-120, HEIGHT-100
        self.life = life
    
    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()

class Meter:
    """
    戦闘機の速度を表示するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (255, 0, 0)
        self.meter = 10
        self.image = self.font.render(f"Speed: {self.meter}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 500, HEIGHT-50

    def meter_up(self, add):
        self.meter += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Speed: {self.meter}", 0, self.color)
        screen.blit(self.image, self.rect)



class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    ボス：100点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def score_up(self, add):
        self.score += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)


class Lives:
    """
    戦闘機の残機表示するクラス
    """
    def __init__(self, life_fig)->int:
        self.font = pg.font.Font(None, 50)
        self.color = (255, 255, 255)
        self.lives = life_fig
        
        self.lives_text = self.font.render(f"Lives: {self.lives}", 0, self.color)
        self.rect = self.lives_text.get_rect()
        self.rect.center = 300, HEIGHT-50
        
    def lives_decrease(self, dec=1)->int:
        self.lives -= dec #残機を減らす
    
    def update(self, screen: pg.Surface):
        self.lives_text = self.font.render(f"Lives: {self.lives}", 0, self.color)
        screen.blit(self.lives_text, self.rect)



class ItemA(pg.sprite.Sprite):
    """
    ItemAに関するクラス(未実装)
    """
    def __init__(self):
        super().__init__()
        self.image = pg.image.load("ex05/fig/itemA.png")
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.timer = random.randint(10000, 15000) * 100  # 10秒から15秒後のランダムな時間
        self.duration = 1 * 1  # 3秒
        self.active = True

    def update(self):
        """
        アイテムの状態を更新する
        """
        if self.active:
            self.duration -= 1
            if self.duration <= 0:
                self.active = False

    def activate(self):
        """
        アイテムをアクティブ状態にする
        """
        self.active = True
        self.duration = 3 * 50


class ItemB(pg.sprite.Sprite):
    """
    ItemBに関するクラス
    """
    def __init__(self):
        super().__init__()
        self.image = pg.image.load("ex05/fig/itemB.png")
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.timer = random.randint(10, 15) * 100  # 10秒から15秒後のランダムな時間
        self.duration = 3 * 50  # 3秒
        self.active = True

    def update(self):
        """
        アイテムの状態を更新する
        """
        if self.active:
            self.duration -= 1
            if self.duration <= 0:
                self.active = False

    def activate(self):
        """
        アイテムをアクティブ状態にする
        """
        self.active = True
        self.duration = 3 * 50

#C0A22036/item
def main():
    pg.display.set_caption("真！戦闘機無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex05/fig/pg_bg.jpg")
    shield_img = pg.image.load("ex05/fig/shield.png")
    score = Score()

    meter = Meter()
    life = Lives(3)

    bird = Bird(3, (900, 400))
    atacks = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    
    itemsA = pg.sprite.Group()
    itemsB = pg.sprite.Group()

    nscs = pg.sprite.Group()
    cure = pg.sprite.Group()

    boss = pg.sprite.Group()
    gameover_font = pg.font.SysFont(None, 150)
    gameover = gameover_font.render("GAME OVER", False, (0,0,255))
    gameclear_font = pg.font.SysFont(None, 150)
    gameclear = gameclear_font.render("GAME ClEAR!", False, (255,128,0))
    boss_life=3
    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_c and score.score>=50 and bird.speed < 10:
                cure.add(Cure(20))
                score.score_up(-50)
                bird.speed += 2
                meter.meter_up(2)
                
        screen.blit(bg_img, [0, 0])


        if tmr%250 == 0: # 250フレームに1回,お邪魔ボールを出現させる
            nscs.add(Nuisance(750)) #15秒で消滅

        if tmr < 500 and tmr%200 == 0:  # 1500フレーム以内かつ200フレームに1回，敵機を出現させる

            emys.add(Enemy())
        elif tmr==500:
            boss.add(BossEnemy())

        for emy in emys:

            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下

                atacks.add(Atack(emy, bird))
        
        for bossemy in boss:
            if bossemy.state == "stop" and tmr%bossemy.interval == 0:
                # Bossが停止状態に入ったら，intervalに応じて爆弾投下
                
                atacks.add(BossBomb(bossemy, bird))

        for bossemy in pg.sprite.groupcollide(boss, beams, False, True).keys():
            exps.add(Explosion(bossemy , 100))  # 爆発エフェクト
            if boss_life==0:
                pg.sprite.groupcollide(boss, beams, True, True).keys()
                score.score_up(100)  # 100点アップ
                screen.blit(gameclear,[240,250])
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            boss_life-=1

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))
            score.score_up(10)

        for atack in pg.sprite.groupcollide(atacks, beams, True, True).keys():
            exps.add(Explosion(atack, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        if len(pg.sprite.spritecollide(bird, nscs, True)) != 0:
            bird.speed -= 2 # スピードを2減速
            meter.meter_up(-2)
            if bird.speed == 0: # スピードが0の時にゲームオーバー
                score.update(screen)
                meter.update(screen)
                pg.display.update()
                time.sleep(2)
                return
                
        if len(pg.sprite.spritecollide(bird, atacks, True)) != 0:

            screen.blit(gameover,[260,250])
            score.update(screen)
            life.lives_decrease() # 残機を減らす
            life.update(screen)
            pg.display.update()
            time.sleep(2)
            if life.lives <= 0: # 残機が０以下なら終了
                return

        # itemAとの当たり判定
        if len(pg.sprite.spritecollide(bird, itemsA, True)) != 0:
            # itemAに触れた場合の処理
            for item in itemsA:
                item.kill()


        # アイテムによるshield表示の制御
        for item in itemsB:
            if item.active and item.rect.colliderect(bird.rect):
                bird.shield_timer = 50 * 50  # 5秒間shieldを表示する
                item.active = False

        # shieldとEnemyの当たり判定
        for enemy in emys:
            if bird.shield_timer > 0 and bird.collides_with_shield(enemy.rect):
                exps.add(Explosion(enemy, 100))
                enemy.kill()

        # shieldとbombの当たり判定
        for bomb in atacks:
            if bird.shield_timer > 0 and bird.collides_with_shield(bomb.rect):
                exps.add(Explosion(bomb, 50))
                bomb.kill()

        # アイテムの追加と更新
        if tmr % 500 == 0:
            if random.random() < 0.5:
                itemsA.add(ItemA())
            else:
                itemsB.add(ItemB())

        itemsA.update()
        itemsA.draw(screen)
        itemsA.remove([item for item in itemsA if not item.active])

        itemsB.update()
        itemsB.draw(screen)
        itemsB.remove([item for item in itemsB if not item.active])

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)

        atacks.update()
        atacks.draw(screen)

        nscs.update()
        nscs.draw(screen)
        cure.update()
        cure.draw(screen)

        boss.update()
        boss.draw(screen)

        atacks.update()

        atacks .draw(screen)

        exps.update()
        exps.draw(screen)
        score.update(screen)

        meter.update(screen)
        life.update(screen)

        pg.display.update()
        tmr += 1
        clock.tick(50) #ゲーム内時間設定（５０）
if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()