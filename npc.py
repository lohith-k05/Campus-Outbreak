import pygame


class NPC:
    """
    Simple top-down story NPC.

    Used for Viveka Mam in the AI Block control room.
    """

    def __init__(self, name, x, y, color=(80, 140, 220)):
        self.name = name

        self.x = float(x)
        self.y = float(y)

        self.width = 32
        self.height = 42

        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height
        )

        self.color = color

    def draw(self, screen, camera):

        x = int(
            self.rect.x - camera.x
        )

        y = int(
            self.rect.y - camera.y
        )

        # Shadow.
        pygame.draw.ellipse(
            screen,
            (18, 22, 24),
            (
                x + 2,
                y + 34,
                29,
                9
            )
        )

        # Legs.
        pygame.draw.rect(
            screen,
            (38, 45, 52),
            (x + 7, y + 27, 8, 12)
        )

        pygame.draw.rect(
            screen,
            (38, 45, 52),
            (x + 18, y + 27, 8, 12)
        )

        # Body / coat.
        pygame.draw.rect(
            screen,
            (45, 75, 115),
            (
                x + 5,
                y + 12,
                23,
                19
            ),
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            self.color,
            (
                x + 8,
                y + 14,
                17,
                14
            ),
            border_radius=3
        )

        # Head.
        pygame.draw.rect(
            screen,
            (120, 88, 68),
            (
                x + 7,
                y + 1,
                21,
                19
            ),
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            (184, 135, 100),
            (
                x + 9,
                y + 3,
                17,
                15
            ),
            border_radius=4
        )

        # Hair.
        pygame.draw.rect(
            screen,
            (45, 32, 27),
            (
                x + 8,
                y + 1,
                20,
                7
            ),
            border_radius=4
        )

        # Eyes.
        pygame.draw.rect(
            screen,
            (35, 35, 35),
            (x + 12, y + 11, 3, 3)
        )

        pygame.draw.rect(
            screen,
            (35, 35, 35),
            (x + 20, y + 11, 3, 3)
        )

        # Name.
        font = pygame.font.Font(
            None,
            21
        )

        shadow = font.render(
            self.name,
            True,
            (8, 8, 8)
        )

        label = font.render(
            self.name,
            True,
            (245, 245, 235)
        )

        rect = label.get_rect(
            center=(
                x + self.width // 2,
                y - 12
            )
        )

        screen.blit(
            shadow,
            rect.move(2, 2)
        )

        screen.blit(
            label,
            rect
        )
