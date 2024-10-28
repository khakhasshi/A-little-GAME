import pygame
import sys
import math
import random
import numpy as np

# 初始化 Pygame
pygame.init()
screen = pygame.display.set_mode((1200, 800))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)  # 字体用于显示文本

# 加载并调整素材尺寸
player_image = pygame.image.load('player.png')
player_image = pygame.transform.scale(player_image, (80, 100))  # 调整玩家图片尺寸

enemy_image = pygame.image.load('enemy.png')
enemy_image = pygame.transform.scale(enemy_image, (100, 130))  # 调整敌人图片尺寸

bullet_image = pygame.image.load('bullet.png')
bullet_image = pygame.transform.scale(bullet_image, (70, 70))  # 调整子弹图片尺寸

enemy_bullet_image = pygame.image.load('enemy_bullet.png')
enemy_bullet_image = pygame.transform.scale(enemy_bullet_image, (30, 30))  # 调整敌人子弹图片尺寸

background_image = pygame.image.load('background.png')
background_image = pygame.transform.scale(background_image, (1200, 800))  # 调整背景图片尺寸

# 加载背景音乐
pygame.mixer.music.load('background_music.mp3')
pygame.mixer.music.play(-1)  # 循环播放背景音乐

# 生成自定义声音波形
def generate_beep(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    wave = np.array([wave, wave]).T * 32767
    return np.ascontiguousarray(wave, dtype=np.int16)

# 创建声音对象
beep_sound = pygame.sndarray.make_sound(generate_beep(440, 0.1))

# 定义玩家类
class Player:
    def __init__(self):
        self.image = player_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (400, 300)
        self.speed = 3
        self.health = 5  # 玩家初始血量为5
        self.radius = 15  # 玩家碰撞半径
        self.shield = 0  # 玩家防护罩（击败10个敌人后激活）

    def move(self, direction):
        self.rect.x += direction[0] * self.speed
        self.rect.y += direction[1] * self.speed
        # 边界检查
        self.rect.x = max(0, min(self.rect.x, 1200 - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, 800 - self.rect.height))

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        # 绘制玩家血条
        health_bar_width = 50
        health_bar_height = 5
        health_ratio = self.health / 5
        pygame.draw.rect(screen, (0, 255, 0), (self.rect.centerx - health_bar_width // 2, self.rect.top - 20, health_bar_width * health_ratio, health_bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (self.rect.centerx - health_bar_width // 2, self.rect.top - 20, health_bar_width, health_bar_height), 1)
        
        # 绘制防护罩状态
        if self.shield > 0:
            pygame.draw.circle(screen, (0, 255, 255), self.rect.center, self.radius + 10, 2)

# 定义敌人类
class Enemy:
    def __init__(self, x, y):
        self.image = enemy_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.radius = 20
        self.speed = 1  # 敌人移动速度
        self.health = 3  # 敌人初始血量为3
        self.can_shoot = random.random() < 0.33
        self.last_shot_time = pygame.time.get_ticks()

    def move_towards_player(self, player_x, player_y):
        dx = player_x - self.rect.x
        dy = player_y - self.rect.y
        distance = math.hypot(dx, dy)
        if distance > 0:
            self.rect.x += dx / distance * self.speed
            self.rect.y += dy / distance * self.speed
        # 边界检查
        self.rect.x = max(self.radius, min(self.rect.x, 1200 - self.radius))
        self.rect.y = max(self.radius, min(self.rect.y, 800 - self.radius))

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        health_bar_width = 40
        health_bar_height = 5
        health_ratio = self.health / 3
        pygame.draw.rect(screen, (255, 0, 0), (self.rect.centerx - health_bar_width // 2, self.rect.top - 10, health_bar_width * health_ratio, health_bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (self.rect.centerx - health_bar_width // 2, self.rect.top - 10, health_bar_width, health_bar_height), 1)

# 定义子弹类
class Bullet:
    def __init__(self, x, y, target_x, target_y, speed=5, image=bullet_image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.radius = 5
        self.speed = speed

        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        self.dx = dx / distance * self.speed
        self.dy = dy / distance * self.speed

    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

    def is_colliding(self, target):
        distance = math.hypot(self.rect.centerx - target.rect.centerx, self.rect.centery - target.rect.centery)
        return distance <= self.radius + target.radius

# 定义摇杆类
class Joystick:
    def __init__(self, x, y, radius):
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.handle_radius = radius // 2
        self.handle_x = x
        self.handle_y = y
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if math.hypot(event.pos[0] - self.handle_x, event.pos[1] - self.handle_y) < self.handle_radius:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            self.handle_x = self.center_x
            self.handle_y = self.center_y
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx = event.pos[0] - self.center_x
            dy = event.pos[1] - self.center_y
            distance = math.hypot(dx, dy)
            if distance > self.radius:
                dx = dx / distance * self.radius
                dy = dy / distance * self.radius
            self.handle_x = self.center_x + dx
            self.handle_y = self.center_y + dy

    def get_direction(self):
        dx = self.handle_x - self.center_x
        dy = self.handle_y - self.center_y
        distance = math.hypot(dx, dy)
        if distance == 0:
            return (0, 0)
        return (dx / distance, dy / distance)

    def draw(self, screen):
        pygame.draw.circle(screen, (200, 200, 200), (self.center_x, self.center_y), self.radius)
        pygame.draw.circle(screen, (100, 100, 255), (int(self.handle_x), int(self.handle_y)), self.handle_radius)

# 定义环绕物类
class Orbiter:
    def __init__(self, player, angle, distance, speed):
        self.player = player
        self.angle = angle
        self.distance = distance
        self.speed = speed
        self.radius = 10

    def update(self):
        self.angle += self.speed
        self.x = self.player.rect.centerx + self.distance * math.cos(self.angle)
        self.y = self.player.rect.centery + self.distance * math.sin(self.angle)

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), self.radius)

    def is_colliding(self, bullet):
        distance = math.hypot(self.x - bullet.rect.centerx, self.y - bullet.rect.centery)
        return distance <= self.radius + bullet.radius

# 初始化玩家、摇杆、敌人和子弹列表
def initialize_game():
    global player, joystick, enemies, bullets, enemy_bullets, enemies_defeated, shoot_interval, last_shot_time, start_time, game_over, bullet_speed, orbiters
    player = Player()
    joystick = Joystick(100, 700, 50)
    enemies = []
    bullets = []
    enemy_bullets = []
    orbiters = []
    enemies_defeated = 0
    shoot_interval = 500
    bullet_speed = 5  # 初始子弹速度
    last_shot_time = pygame.time.get_ticks()
    start_time = pygame.time.get_ticks()  # 记录游戏开始时间
    game_over = False

    # 初始生成3个敌人
    for _ in range(3):
        spawn_enemy()

# 敌人刷新函数
def spawn_enemy():
    x = random.randint(100, 1100)
    y = random.randint(100, 700)
    new_enemy = Enemy(x, y)
    enemies.append(new_enemy)

# 初始化游戏
initialize_game()

# 主循环
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if 550 <= mouse_x <= 650 and 375 <= mouse_y <= 425:
                    initialize_game()
        else:
            joystick.handle_event(event)

    if not game_over:
        # 获取摇杆方向并移动玩家
        direction = joystick.get_direction()
        player.move(direction)

        # 自动发射子弹
        current_time = pygame.time.get_ticks()
        if current_time - last_shot_time >= shoot_interval and enemies:
            closest_enemy = min(enemies, key=lambda e: math.hypot(e.rect.centerx - player.rect.centerx, e.rect.centery - player.rect.centery))
            bullet = Bullet(player.rect.centerx, player.rect.centery, closest_enemy.rect.centerx, closest_enemy.rect.centery, speed=bullet_speed)
            bullets.append(bullet)
            last_shot_time = current_time  # 重置计时器

        # 移动敌人朝向玩家并发射子弹
        for enemy in enemies:
            enemy.move_towards_player(player.rect.centerx, player.rect.centery)

            if enemy.can_shoot and current_time - enemy.last_shot_time >= 1000:
                enemy_bullet = Bullet(enemy.rect.centerx, enemy.rect.centery, player.rect.centerx, player.rect.centery, speed=3, image=enemy_bullet_image)
                enemy_bullets.append(enemy_bullet)
                enemy.last_shot_time = current_time

            # 检查敌人和玩家的碰撞
            if math.hypot(player.rect.centerx - enemy.rect.centerx, player.rect.centery - enemy.rect.centery) < enemy.radius + player.radius:
                if player.shield > 0:
                    player.shield -= 1
                else:
                    player.health -= 1
                enemies.remove(enemy)
                spawn_enemy()
                if player.health <= 0:
                    game_over = True
                    break

        # 移动子弹并检查碰撞
        for bullet in bullets[:]:
            bullet.move()
            for enemy in enemies[:]:
                if bullet.is_colliding(enemy):
                    enemy.health -= 1
                    bullets.remove(bullet)
                    if enemy.health <= 0:
                        enemies_defeated += 1
                        enemies.remove(enemy)
                        spawn_enemy()

                        # 播放蜂鸣器声音
                        beep_sound.play()

                        # 每击杀10个敌人，射速加快20%
                        if enemies_defeated % 10 == 0:
                            shoot_interval = int(shoot_interval * 0.8)

                        # 每击杀15个敌人，玩家子弹速度加快20%
                        if enemies_defeated % 15 == 0:
                            bullet_speed = int(bullet_speed * 1.2)
                            # 敌人速度加快20%
                            for enemy in enemies:
                                enemy.speed *= 1.2

                        # 每击杀20个敌人，生成三个环绕物
                        if enemies_defeated == 20:
                            for i in range(3):
                                angle = i * (2 * math.pi / 3)
                                orbiters.append(Orbiter(player, angle, 50, 0.05))

                        if enemies_defeated == 10:
                            player.shield = 10
                    break

        # 移动敌人子弹并检查与玩家的碰撞
        for enemy_bullet in enemy_bullets[:]:
            enemy_bullet.move()
            if enemy_bullet.is_colliding(player):
                if player.shield > 0:
                    player.shield -= 1
                else:
                    player.health -= 1
                enemy_bullets.remove(enemy_bullet)
                if player.health <= 0:
                    game_over = True
                    break

        # 更新并绘制环绕物
        for orbiter in orbiters:
            orbiter.update()
            orbiter.draw(screen)

        # 检查子弹与环绕物的碰撞
        for bullet in bullets[:]:
            for orbiter in orbiters:
                if orbiter.is_colliding(bullet):
                    bullets.remove(bullet)
                    break

    # 绘制背景
    screen.blit(background_image, (0, 0))

    # 计算并显示生存时间和击杀敌人数
    survival_time = (pygame.time.get_ticks() - start_time) // 1000
    kills_text = font.render(f"Kills: {enemies_defeated}", True, (255, 255, 255))
    time_text = font.render(f"Time: {survival_time}s", True, (255, 255, 255))
    screen.fill((0, 100, 0))
    player.draw(screen)
    joystick.draw(screen)
    for enemy in enemies:
        enemy.draw(screen)
    for bullet in bullets:
        bullet.draw(screen)
    for enemy_bullet in enemy_bullets:
        enemy_bullet.draw(screen)

    # 绘制击杀敌人数在左上角
    screen.blit(kills_text, (10, 10))
    # 绘制生存时间在屏幕顶部中间
    screen.blit(time_text, (screen.get_width() // 2 - time_text.get_width() // 2, 10))

    if game_over:
        # 绘制“restart”按钮
        restart_text = font.render("Restart", True, (255, 255, 255))
        pygame.draw.rect(screen, (0, 0, 0), (550, 375, 100, 50))
        screen.blit(restart_text, (screen.get_width() // 2 - restart_text.get_width() // 2, 385))

    pygame.display.flip()
    clock.tick(60)