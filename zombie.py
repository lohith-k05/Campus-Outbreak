import pygame
import math


class Zombie:
    def __init__(self, x, y, speed=75):
        self.x = float(x)
        self.y = float(y)

        self.width = 34
        self.height = 42

        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height
        )

        self.speed = speed
        self.max_health = 3
        self.health = self.max_health
        self.alive = True

        self.attack_cooldown = 0.0
        self.attack_delay = 0.9
        self.attack_damage = 5

        self.animation = 0.0

    def update(self, player, dt, world_rect):
        if not self.alive:
            return

        self.animation += dt
        self.attack_cooldown = max(
            0.0,
            self.attack_cooldown - dt
        )

        target = pygame.Vector2(
            player.rect.centerx,
            player.rect.centery
        )

        current = pygame.Vector2(
            self.rect.centerx,
            self.rect.centery
        )

        direction = target - current
        distance = direction.length()

        if distance > 55:
            direction.normalize_ip()

            self.x += direction.x * self.speed * dt
            self.y += direction.y * self.speed * dt

            self.x = max(
                world_rect.left,
                min(
                    self.x,
                    world_rect.right - self.width
                )
            )

            self.y = max(
                world_rect.top,
                min(
                    self.y,
                    world_rect.bottom - self.height
                )
            )

            self.rect.topleft = (
                int(self.x),
                int(self.y)
            )

        elif self.attack_cooldown <= 0:
            # The current Player has no health system yet.
            # For this step, attacks are visual only.
            self.attack_cooldown = self.attack_delay

    def take_damage(self, damage=1):
        if not self.alive:
            return False

        self.health -= damage

        if self.health <= 0:
            self.health = 0
            self.alive = False
            return True

        return False

    def draw(self, screen, camera):
        if not self.alive:
            return

        x = int(self.rect.x - camera.x)
        y = int(self.rect.y - camera.y)

        bob = 0
        if int(self.animation * 8) % 2:
            bob = -1

        # Shadow
        pygame.draw.ellipse(
            screen,
            (22, 27, 23),
            (x + 2, y + 34, 31, 10)
        )

        skin = (105, 145, 96)
        skin_dark = (65, 91, 61)
        shirt = (76, 73, 70)
        shirt_dark = (47, 48, 46)
        pants = (43, 46, 48)

        # Legs
        pygame.draw.rect(
            screen,
            pants,
            (x + 7, y + 27 + bob, 8, 12)
        )

        pygame.draw.rect(
            screen,
            pants,
            (x + 19, y + 27 + bob, 8, 12)
        )

        # Body
        pygame.draw.rect(
            screen,
            shirt_dark,
            (x + 5, y + 12 + bob, 25, 19),
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            shirt,
            (x + 8, y + 14 + bob, 19, 14),
            border_radius=3
        )

        # Head
        pygame.draw.rect(
            screen,
            skin_dark,
            (x + 7, y + 1 + bob, 21, 19),
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            skin,
            (x + 9, y + 3 + bob, 17, 15),
            border_radius=4
        )

        # Hair
        pygame.draw.rect(
            screen,
            (35, 35, 31),
            (x + 8, y + 1 + bob, 20, 7),
            border_radius=4
        )

        # Eyes
        pygame.draw.rect(
            screen,
            (235, 72, 55),
            (x + 12, y + 11 + bob, 3, 3)
        )

        pygame.draw.rect(
            screen,
            (235, 72, 55),
            (x + 20, y + 11 + bob, 3, 3)
        )

        # Health bar
        bar_w = 36
        bar_h = 5

        pygame.draw.rect(
            screen,
            (35, 35, 35),
            (x - 1, y - 9, bar_w, bar_h)
        )

        ratio = self.health / self.max_health

        pygame.draw.rect(
            screen,
            (205, 55, 55),
            (
                x - 1,
                y - 9,
                int(bar_w * ratio),
                bar_h
            )
        )


class Bullet:
    def __init__(self, x, y, target_x, target_y):
        self.position = pygame.Vector2(x, y)

        direction = pygame.Vector2(
            target_x - x,
            target_y - y
        )

        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)

        direction.normalize_ip()

        self.velocity = direction * 720
        self.radius = 4
        self.life = 1.4

    def update(self, dt):
        self.position += self.velocity * dt
        self.life -= dt

    def alive(self):
        return self.life > 0

    def draw(self, screen, camera):
        pygame.draw.circle(
            screen,
            (255, 220, 80),
            (
                int(self.position.x - camera.x),
                int(self.position.y - camera.y)
            ),
            self.radius
        )
