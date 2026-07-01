
import pygame


class MechanicalBlock:
    """Dark workshop/classroom combat arena for the Mechanical Block."""

    def __init__(self, screen_width=1280, screen_height=720):
        self.width = 1700
        self.height = 1050
        self.entry_point = (120, 500)

        self.player_bounds = pygame.Rect(
            70, 100, self.width - 140, self.height - 170
        )

        self.walls = [
            pygame.Rect(0, 0, self.width, 35),
            pygame.Rect(0, self.height - 35, self.width, 35),
            pygame.Rect(0, 0, 35, self.height),
            pygame.Rect(self.width - 35, 0, 35, self.height),

            pygame.Rect(550, 130, 25, 250),
            pygame.Rect(550, 680, 25, 260),
            pygame.Rect(1110, 130, 25, 250),
            pygame.Rect(1110, 680, 25, 260),
        ]

        self.obstacles = [
            pygame.Rect(175, 330, 190, 38),
            pygame.Rect(175, 575, 190, 38),
            pygame.Rect(395, 450, 110, 38),

            pygame.Rect(650, 285, 225, 46),
            pygame.Rect(650, 620, 225, 46),
            pygame.Rect(900, 445, 130, 42),

            pygame.Rect(1190, 275, 245, 50),
            pygame.Rect(1190, 650, 245, 50),
            pygame.Rect(1470, 450, 110, 45),
        ]

    def get_collision_rects(self):
        return self.walls + self.obstacles

    def random_spawn_points(self):
        return [
            (110, 175), (110, 850),
            (410, 190), (430, 825),
            (650, 180), (850, 180),
            (990, 840), (1060, 185),
            (1230, 185), (1510, 185),
            (1540, 820), (1290, 850),
        ]

    def draw(self, screen, camera):
        screen.fill((12, 13, 15))

        floor = pygame.Rect(
            -camera.x, -camera.y, self.width, self.height
        )
        pygame.draw.rect(screen, (39, 39, 40), floor)

        # Floor grid.
        tile = 50
        sx0 = int(camera.x // tile) * tile
        sy0 = int(camera.y // tile) * tile

        for x in range(sx0, int(camera.x + screen.get_width()) + tile, tile):
            sx = x - camera.x
            pygame.draw.line(
                screen, (49, 50, 50),
                (sx, 0), (sx, screen.get_height())
            )

        for y in range(sy0, int(camera.y + screen.get_height()) + tile, tile):
            sy = y - camera.y
            pygame.draw.line(
                screen, (49, 50, 50),
                (0, sy), (screen.get_width(), sy)
            )

        # Rear wall and chalkboard.
        rear = pygame.Rect(
            35 - camera.x, 35 - camera.y,
            self.width - 70, 105
        )
        pygame.draw.rect(screen, (47, 45, 43), rear)
        pygame.draw.rect(screen, (18, 18, 19), rear, 3)

        board = pygame.Rect(
            370 - camera.x, 58 - camera.y, 620, 70
        )
        pygame.draw.rect(screen, (21, 35, 34), board, border_radius=4)
        pygame.draw.rect(screen, (100, 85, 60), board, 5)

        font = pygame.font.Font(None, 30)
        text = font.render(
            "MECHANICAL ENGINEERING  //  WORKSHOP",
            True, (172, 177, 165)
        )
        screen.blit(text, text.get_rect(center=board.center))

        # Benches/desks.
        for rect in self.obstacles:
            r = rect.move(-camera.x, -camera.y)
            pygame.draw.rect(
                screen, (59, 49, 41), r, border_radius=3
            )
            pygame.draw.rect(
                screen, (18, 19, 20), r, 3, border_radius=3
            )
            pygame.draw.line(
                screen, (112, 100, 81),
                (r.left + 5, r.top + 5),
                (r.right - 5, r.top + 5), 2
            )

        # Lockers.
        for x, y in [
            (72, 245), (72, 315),
            (1510, 245), (1510, 315),
            (1510, 565), (72, 565)
        ]:
            r = pygame.Rect(
                x - camera.x, y - camera.y, 72, 52
            )
            pygame.draw.rect(screen, (56, 58, 59), r)
            pygame.draw.rect(screen, (18, 19, 20), r, 3)
            pygame.draw.line(
                screen, (105, 107, 106),
                (r.centerx, r.y + 7),
                (r.centerx, r.bottom - 7), 2
            )

        # Pipes.
        for y in (185, 215):
            pygame.draw.line(
                screen, (71, 73, 70),
                (70 - camera.x, y - camera.y),
                (1620 - camera.x, y - camera.y), 7
            )

        # Section dividers.
        for x in (575, 1135):
            pygame.draw.line(
                screen, (100, 83, 55),
                (x - camera.x, 130 - camera.y),
                (x - camera.x, 940 - camera.y), 3
            )

        # Emergency lights.
        for x in (95, 535, 1080, 1580):
            pygame.draw.rect(
                screen, (115, 38, 34),
                (x - camera.x, 150 - camera.y, 38, 8),
                border_radius=3
            )

        # Section labels.
        small = pygame.font.Font(None, 22)
        for label, x in [
            ("WORKSHOP 01", 245),
            ("ENGINE LAB 02", 700),
            ("MACHINE BAY 03", 1260),
        ]:
            s = small.render(label, True, (125, 122, 113))
            screen.blit(s, (x - camera.x, 235 - camera.y))

        # Spawn-door markings.
        for x, y in self.random_spawn_points():
            pygame.draw.rect(
                screen, (58, 47, 39),
                (x - camera.x - 13, y - camera.y - 13, 26, 26), 2
            )

        # Entry door.
        door = pygame.Rect(
            self.entry_point[0] - camera.x - 30,
            self.entry_point[1] - camera.y - 60,
            60, 120
        )
        pygame.draw.rect(screen, (12, 14, 15), door)
        pygame.draw.rect(screen, (126, 101, 62), door, 3)

        # Vignette.
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(
            overlay, (0, 0, 0, 85),
            (0, 0, screen.get_width(), 58)
        )
        pygame.draw.rect(
            overlay, (0, 0, 0, 105),
            (0, screen.get_height() - 70,
             screen.get_width(), 70)
        )
        pygame.draw.rect(
            overlay, (0, 0, 0, 65),
            (0, 0, 55, screen.get_height())
        )
        pygame.draw.rect(
            overlay, (0, 0, 0, 65),
            (screen.get_width() - 55, 0,
             55, screen.get_height())
        )
        screen.blit(overlay, (0, 0))
