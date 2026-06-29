
import random
import pygame


class StudentZombie:
    """Six-hit infected student used only in Mechanical Block."""

    SHIRTS = [
        ((45, 72, 95), (30, 42, 56), (54, 38, 31)),
        ((91, 57, 45), (54, 39, 34), (25, 28, 31)),
        ((66, 78, 54), (38, 48, 35), (42, 32, 28)),
        ((83, 67, 93), (52, 42, 60), (32, 27, 25)),
    ]

    def __init__(self, x, y, speed=72, variant=None):
        self.x = float(x)
        self.y = float(y)
        self.width = 38
        self.height = 48
        self.rect = pygame.Rect(int(x), int(y), 38, 48)

        self.speed = speed
        self.max_health = 6
        self.health = 6
        self.alive = True

        self.attack_cooldown = random.uniform(0.2, 0.7)
        self.attack_delay = 0.85
        self.attack_damage = 8
        self.animation = random.random() * 10

        self.variant = (
            random.randrange(4) if variant is None else variant
        )

    def update(self, player, dt, bounds, obstacles):
        if not self.alive:
            return

        self.animation += dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)

        target = pygame.Vector2(
            player.rect.centerx, player.rect.centery
        )
        current = pygame.Vector2(self.rect.center)

        direction = target - current
        distance = direction.length()

        if distance > 50:
            direction.normalize_ip()
            self._move(direction.x * self.speed * dt, 0, bounds, obstacles)
            self._move(0, direction.y * self.speed * dt, bounds, obstacles)

        elif self.attack_cooldown <= 0:
            if hasattr(player, "mechanical_immunity"):
                player.mechanical_immunity = max(
                    0, player.mechanical_immunity - self.attack_damage
                )
            self.attack_cooldown = self.attack_delay

        self.rect.topleft = (round(self.x), round(self.y))

    def _move(self, dx, dy, bounds, obstacles):
        test = self.rect.move(round(dx), round(dy))

        if not bounds.contains(test):
            return

        for obstacle in obstacles:
            if test.colliderect(obstacle):
                return

        self.x += dx
        self.y += dy

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

        bob = -2 if int(self.animation * 7) % 2 else 0
        shirt, shirt_dark, hair = self.SHIRTS[self.variant]

        skin = (154, 103, 82)
        skin_light = (190, 137, 105)
        pants = (34, 36, 41)
        shoes = (18, 19, 21)

        pygame.draw.ellipse(
            screen, (8, 9, 9),
            (x + 2, y + 38, 35, 11)
        )

        pygame.draw.rect(
            screen, pants,
            (x + 7, y + 29 + bob, 9, 14)
        )
        pygame.draw.rect(
            screen, pants,
            (x + 22, y + 29 + bob, 9, 14)
        )

        pygame.draw.rect(
            screen, shoes,
            (x + 5, y + 40 + bob, 12, 5)
        )
        pygame.draw.rect(
            screen, shoes,
            (x + 21, y + 40 + bob, 12, 5)
        )

        body = pygame.Rect(x + 5, y + 13 + bob, 29, 20)

        pygame.draw.rect(
            screen, shirt_dark, body, border_radius=4
        )
        pygame.draw.rect(
            screen, shirt,
            (body.x + 3, body.y + 2, 23, 15),
            border_radius=3
        )

        # Torn sleeve.
        pygame.draw.polygon(
            screen, shirt,
            [
                (body.left, body.top + 4),
                (body.left - 6, body.top + 11),
                (body.left + 3, body.top + 14),
            ]
        )

        # Student ID.
        pygame.draw.rect(
            screen, (205, 188, 138),
            (x + 17, y + 20 + bob, 7, 9)
        )

        head = pygame.Rect(x + 8, y + 1 + bob, 22, 19)
        pygame.draw.rect(screen, skin, head, border_radius=6)
        pygame.draw.rect(
            screen, skin_light,
            (head.x + 2, head.y + 2, 18, 14),
            border_radius=5
        )

        pygame.draw.rect(
            screen, hair,
            (head.x + 1, head.y, 20, 8),
            border_radius=4
        )

        # Infected eyes.
        pygame.draw.rect(
            screen, (214, 52, 45),
            (x + 12, y + 11 + bob, 4, 3)
        )
        pygame.draw.rect(
            screen, (214, 52, 45),
            (x + 22, y + 11 + bob, 4, 3)
        )

        # Blood mark.
        pygame.draw.line(
            screen, (120, 35, 30),
            (x + 9, y + 18 + bob),
            (x + 14, y + 23 + bob), 2
        )

        # Six-hit health bar.
        pygame.draw.rect(
            screen, (15, 16, 17),
            (x - 2, y - 10, 42, 5)
        )
        pygame.draw.rect(
            screen, (190, 50, 45),
            (
                x - 2, y - 10,
                int(42 * self.health / self.max_health), 5
            )
        )
