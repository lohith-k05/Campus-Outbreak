
import random
import pygame


class RescuedStudent:
    """Friendly student character shown after Mechanical Block rescue."""

    SHIRTS = [
        (43, 87, 127),
        (113, 73, 54),
        (72, 99, 70),
        (91, 72, 118),
        (108, 94, 54),
    ]

    def __init__(self, x, y, index):
        self.x = float(x)
        self.y = float(y)
        self.width = 30
        self.height = 42
        self.rect = pygame.Rect(int(x), int(y), 30, 42)

        self.shirt = self.SHIRTS[index % len(self.SHIRTS)]
        self.offset = (
            random.randint(-12, 12),
            random.randint(-12, 12)
        )
        self.animation = random.random() * 10

    def update_follow(self, target, dt, bounds):
        target_pos = pygame.Vector2(
            target.rect.centerx + self.offset[0],
            target.rect.centery + self.offset[1]
        )

        direction = target_pos - pygame.Vector2(self.rect.center)

        if direction.length_squared() > 55 ** 2:
            direction.normalize_ip()

            self.x += direction.x * 85 * dt
            self.y += direction.y * 85 * dt

            self.x = max(bounds.left, min(
                self.x, bounds.right - self.width
            ))
            self.y = max(bounds.top, min(
                self.y, bounds.bottom - self.height
            ))

            self.rect.topleft = (int(self.x), int(self.y))

        self.animation += dt

    def draw(self, screen, camera):
        x = int(self.rect.x - camera.x)
        y = int(self.rect.y - camera.y)

        bob = -1 if int(self.animation * 6) % 2 else 0

        pygame.draw.ellipse(
            screen, (9, 10, 10),
            (x + 2, y + 34, 27, 9)
        )

        pygame.draw.rect(
            screen, (45, 48, 55),
            (x + 6, y + 27 + bob, 8, 12)
        )
        pygame.draw.rect(
            screen, (45, 48, 55),
            (x + 17, y + 27 + bob, 8, 12)
        )

        pygame.draw.rect(
            screen, (23, 24, 26),
            (x + 4, y + 37 + bob, 10, 5)
        )
        pygame.draw.rect(
            screen, (23, 24, 26),
            (x + 17, y + 37 + bob, 10, 5)
        )

        pygame.draw.rect(
            screen, self.shirt,
            (x + 4, y + 12 + bob, 23, 18),
            border_radius=4
        )

        pygame.draw.rect(
            screen, (210, 192, 137),
            (x + 14, y + 19 + bob, 6, 7)
        )

        pygame.draw.rect(
            screen, (211, 158, 121),
            (x + 7, y + 1 + bob, 18, 17),
            border_radius=5
        )

        pygame.draw.rect(
            screen, (46, 34, 31),
            (x + 7, y + bob, 18, 7),
            border_radius=4
        )
