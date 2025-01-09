import pygame
from sys import exit
import math
import random
from settings import *

pygame.init()

# Creating the window object
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Top Down Shooter")  # Naam van het spel (kunnen we nog veranderen)
clock = pygame.time.Clock()

# Load images
background = pygame.image.load("background/ground.png").convert()


# Functie voor het spawnen van een nieuwe vijand
def spawn_enemy():
    # Bepaal een willekeurige spawnpositie buiten het scherm
    spawn_x = random.randint(0, WIDTH)
    spawn_y = random.randint(0, HEIGHT)

    # Maak een nieuwe vijand en voeg deze toe aan de groepen
    enemy = Enemy((spawn_x, spawn_y))
    enemy_group.add(enemy)
    all_sprites_group.add(enemy)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.pos = pygame.math.Vector2(PLAYER_START_X, PLAYER_START_Y)
        self.image = pygame.transform.rotozoom(pygame.image.load("player/player.png").convert_alpha(), 0, PLAYER_SIZE)
        self.base_player_image = self.image
        self.hitbox_rect = self.base_player_image.get_rect(center=self.pos)
        self.rect = self.hitbox_rect.copy()
        self.speed = PLAYER_SPEED
        self.shoot = False
        self.shoot_cooldown = 0
        self.gun_barrel_offset = pygame.math.Vector2(GUN_OFFSET_X, GUN_OFFSET_Y)
        self.kill_count = 0  # Nieuw: bijhouden van het aantal gedode vijanden
        self.alive = True  # Speler is in leven bij start

    def player_rotation(self):
        self.mouse_coords = pygame.mouse.get_pos()
        self.x_change_mouse_player = (self.mouse_coords[0] - WIDTH // 2)
        self.y_change_mouse_player = (self.mouse_coords[1] - HEIGHT // 2)
        self.angle = math.degrees(math.atan2(self.y_change_mouse_player, self.x_change_mouse_player))
        self.image = pygame.transform.rotate(self.base_player_image, int(-self.angle))
        self.rect = self.image.get_rect(center=self.hitbox_rect.center)

    def user_input(self):
        self.velocity_x = 0
        self.velocity_y = 0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.velocity_x = -self.speed
        if keys[pygame.K_d]:
            self.velocity_x = self.speed
        if keys[pygame.K_w]:
            self.velocity_y = -self.speed
        if keys[pygame.K_s]:
            self.velocity_y = self.speed

        if self.velocity_x != 0 and self.velocity_y != 0:  # Diagonal movement
            self.velocity_x /= math.sqrt(2)
            self.velocity_y /= math.sqrt(2)

        if pygame.mouse.get_pressed() == (1, 0, 0) or keys[pygame.K_SPACE]:
            self.shoot = True
            self.is_shooting()
        else:
            self.shoot = False

    def is_shooting(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_bullet_pos = self.pos + self.gun_barrel_offset.rotate(self.angle)
            self.bullet = Bullet(spawn_bullet_pos[0], spawn_bullet_pos[1], self.angle)
            bullet_group.add(self.bullet)
            all_sprites_group.add(self.bullet)

    def move(self):
        self.pos += pygame.math.Vector2(self.velocity_x, self.velocity_y)
        self.hitbox_rect.center = self.pos
        self.rect.center = self.hitbox_rect.center

    def increment_kill_count(self):
        self.kill_count += 1

    def check_win_condition(self):
        if self.kill_count >= 5:
            return True
        return False

    def check_collision_with_enemies(self):
        # Detecteer botsing met vijanden
        hit_enemies = pygame.sprite.spritecollide(self, enemy_group, False)
        if hit_enemies:
            self.alive = False  # Speler is dood wanneer een vijand hem raakt

    def update(self):
        if self.alive:
            self.user_input()
            self.move()
            self.player_rotation()

            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1

            self.check_collision_with_enemies()  # Controleer of de speler door een vijand wordt geraakt
        else:
            self.handle_death()  # Behandel de dood van de speler

    def handle_death(self):
        # Speler is dood stop het spel
        self.kill()
        global game_over
        game_over = True

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.image.load("bullet/bullet.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, BULLET_SCALE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = BULLET_SPEED
        self.x_velocity = math.cos(self.angle * (2 * math.pi / 360)) * self.speed
        self.y_velocity = math.sin(self.angle * (2 * math.pi / 360)) * self.speed
        self.bullet_lifetime = BULLET_LIFETIME
        self.spawn_time = pygame.time.get_ticks()  # Gets the specific time the bullet was created

    def bullet_movement(self):
        self.x += self.x_velocity
        self.y += self.y_velocity
        self.rect.x = int(self.x)  # Float naar int
        self.rect.y = int(self.y)

        # Verwijder de kogel als hij te lang bestaat
        if pygame.time.get_ticks() - self.spawn_time > self.bullet_lifetime:
            self.kill()  # Verwijder de kogel

        # Controleer of de kogel een vijand raakt
        self.check_for_enemy_collision()

    def check_for_enemy_collision(self):
        # Detecteer botsing met vijanden
        hit_enemies = pygame.sprite.spritecollide(self, enemy_group, False)
        if hit_enemies:
            for enemy in hit_enemies:
                enemy.kill()  # Verwijder de vijand
            self.kill()  # Verwijder de kogel na de botsing

            # Spawn een nieuwe vijand
            spawn_enemy()

            # Verhoog de killcount van de speler
            player.increment_kill_count()

    def update(self):
        self.bullet_movement()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__(enemy_group, all_sprites_group)
        self.image = pygame.image.load("enemy/enemy.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, ENEMY_SCALE)

        self.rect = self.image.get_rect()
        self.rect.center = position

        self.position = pygame.math.Vector2(position)
        self.direction = pygame.math.Vector2()
        self.velocity = pygame.math.Vector2()
        self.speed = ENEMY_SPEED

    def hunt_player(self):
        player_vector = pygame.math.Vector2(player.hitbox_rect.center)
        enemy_vector = pygame.math.Vector2(self.rect.center)
        distance = self.get_vector_distance(player_vector, enemy_vector)

        if distance > 0:
            self.direction = (player_vector - enemy_vector).normalize()
        else:
            self.direction = pygame.math.Vector2()

        self.velocity = self.direction * self.speed
        self.position += self.velocity

        self.rect.centerx = self.position.x
        self.rect.centery = self.position.y

    def update(self):
        self.hunt_player()

    def get_vector_distance(self, vector_1, vector_2):
        return (vector_1 - vector_2).magnitude()

class Camara(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.math.Vector2()
        self.floor_rect = background.get_rect(topleft=(0, 0))

    def custom_draw(self):
        self.offset.x = player.rect.centerx - (WIDTH // 2)  # gotta blit the player rect not base rect
        self.offset.y = player.rect.centery - (HEIGHT // 2)

        # draw the floor
        floor_offset_pos = self.floor_rect.topleft - self.offset
        screen.blit(background, floor_offset_pos)

        for sprite in all_sprites_group:
            offset_pos = sprite.rect.topleft - self.offset
            screen.blit(sprite.image, offset_pos)

all_sprites_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()

camera = Camara()
player = Player()
enemy = Enemy((500, 0))

all_sprites_group.add(player)

def show_win_screen():
    font = pygame.font.Font(None, 74)
    text = font.render("You Win!", True, (0, 255, 0))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    pygame.display.update()
    pygame.time.wait(2000)  # Wacht 2 seconden voor het afsluiten

def show_game_over_screen():
    font = pygame.font.Font(None, 74)
    text = font.render("Game Over!", True, (255, 0, 0))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    pygame.display.update()
    pygame.time.wait(2000)  # Wacht 2 seconden voor het afsluiten

game_over = False
while True:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
            pygame.quit()
            exit()

    if not game_over:
        all_sprites_group.update()

        # Controleer de winconditie
        if player.check_win_condition():
            show_win_screen()
            pygame.quit()
            exit()

        camera.custom_draw()
        pygame.display.update()
        clock.tick(60)
    else:
        show_game_over_screen()
        pygame.quit()
        exit()
