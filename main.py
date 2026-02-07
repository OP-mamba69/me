import pygame
from dataclasses import dataclass

# Screen and world constants
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60
GRAVITY = 0.8
PLAYER_SPEED = 5
JUMP_STRENGTH = -15
MAX_HEALTH = 3


@dataclass
class Platform:
    x: int
    y: int
    width: int
    height: int

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (90, 64, 40), self.rect)


class Entity:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.rect = pygame.Rect(x, y, w, h)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False

    def apply_gravity(self) -> None:
        self.vel_y += GRAVITY


class Player(Entity):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, 40, 50)
        self.health = MAX_HEALTH
        self.invincible_timer = 0
        self.score = 0

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

    def take_damage(self) -> None:
        if self.invincible_timer <= 0:
            self.health -= 1
            self.invincible_timer = 60

    def update(self, platforms: list[Platform]) -> None:
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        self.apply_gravity()

        # Horizontal movement + collision
        self.rect.x += int(self.vel_x)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:
                    self.rect.left = platform.rect.right

        # Vertical movement + collision
        self.rect.y += int(self.vel_y)
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:  # falling
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:  # rising
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

    def draw(self, surface: pygame.Surface) -> None:
        color = (80, 180, 255) if self.invincible_timer % 10 < 5 else (140, 220, 255)
        pygame.draw.rect(surface, color, self.rect)


class Enemy(Entity):
    def __init__(self, x: int, y: int, patrol_min: int, patrol_max: int):
        super().__init__(x, y, 40, 40)
        self.patrol_min = patrol_min
        self.patrol_max = patrol_max
        self.vel_x = 2

    def update(self, platforms: list[Platform]) -> None:
        self.apply_gravity()

        self.rect.x += int(self.vel_x)
        if self.rect.left < self.patrol_min or self.rect.right > self.patrol_max:
            self.vel_x *= -1

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:
                    self.rect.right = platform.rect.left
                    self.vel_x *= -1
                else:
                    self.rect.left = platform.rect.right
                    self.vel_x *= -1

        self.rect.y += int(self.vel_y)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (220, 70, 70), self.rect)


class Level:
    def __init__(self):
        self.platforms = [
            Platform(0, 500, 960, 40),
            Platform(120, 420, 180, 20),
            Platform(380, 350, 180, 20),
            Platform(650, 280, 200, 20),
            Platform(760, 430, 140, 20),
        ]
        self.enemies = [
            Enemy(180, 380, 120, 300),
            Enemy(430, 310, 380, 560),
            Enemy(700, 240, 650, 850),
        ]
        self.goal = pygame.Rect(900, 220, 30, 280)

    def draw(self, surface: pygame.Surface) -> None:
        for platform in self.platforms:
            platform.draw(surface)
        for enemy in self.enemies:
            enemy.draw(surface)
        pygame.draw.rect(surface, (255, 215, 0), self.goal)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2D Platformer (Class 11 project)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 24)
        self.big_font = pygame.font.SysFont("consolas", 48)

        self.state = "menu"  # menu, playing, game_over, win
        self.level = Level()
        self.player = Player(60, 300)

    def reset(self) -> None:
        self.level = Level()
        self.player = Player(60, 300)
        self.state = "playing"

    def handle_enemy_collisions(self) -> None:
        for enemy in self.level.enemies[:]:
            if self.player.rect.colliderect(enemy.rect):
                # If player falls on enemy, defeat enemy
                if self.player.vel_y > 0 and self.player.rect.bottom - enemy.rect.top < 18:
                    self.level.enemies.remove(enemy)
                    self.player.vel_y = JUMP_STRENGTH * 0.6
                    self.player.score += 100
                else:
                    self.player.take_damage()
                    # Small knock-back
                    if self.player.rect.centerx < enemy.rect.centerx:
                        self.player.rect.x -= 25
                    else:
                        self.player.rect.x += 25

    def update_playing(self) -> None:
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(self.level.platforms)

        for enemy in self.level.enemies:
            enemy.update(self.level.platforms)

        self.handle_enemy_collisions()

        if self.player.health <= 0 or self.player.rect.top > SCREEN_HEIGHT:
            self.state = "game_over"

        if self.player.rect.colliderect(self.level.goal):
            self.state = "win"

    def draw_hud(self) -> None:
        health_text = self.font.render(f"Health: {self.player.health}", True, (255, 255, 255))
        score_text = self.font.render(f"Score: {self.player.score}", True, (255, 255, 255))
        self.screen.blit(health_text, (20, 16))
        self.screen.blit(score_text, (20, 42))

    def draw_center_text(self, title: str, subtitle: str) -> None:
        title_surface = self.big_font.render(title, True, (255, 255, 255))
        subtitle_surface = self.font.render(subtitle, True, (220, 220, 220))
        self.screen.blit(title_surface, title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)))
        self.screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

    def draw(self) -> None:
        self.screen.fill((30, 34, 48))

        if self.state == "menu":
            self.draw_center_text("2D Platformer", "Press ENTER to start")
        elif self.state == "playing":
            self.level.draw(self.screen)
            self.player.draw(self.screen)
            self.draw_hud()
        elif self.state == "game_over":
            self.draw_center_text("Game Over", "Press R to retry | ESC to quit")
        elif self.state == "win":
            self.draw_center_text("You Win!", f"Score: {self.player.score} | Press R to play again")

        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if self.state == "menu" and event.key == pygame.K_RETURN:
                        self.state = "playing"
                    elif self.state in {"game_over", "win"} and event.key == pygame.K_r:
                        self.reset()

            if self.state == "playing":
                self.update_playing()

            self.draw()

        pygame.quit()


if __name__ == "__main__":
    Game().run()
