import pygame


class AIBlock:
    """
    Separate playable AI Block scene.

    This is deliberately independent from the campus map.
    When this scene is active, only this scene is drawn.
    """

    def __init__(self):
        self.width = 1600
        self.height = 1000

        self.entry_point = (
            170,
            self.height // 2 - 21
        )

        self.player_bounds = pygame.Rect(
            45,
            45,
            self.width - 90,
            self.height - 90
        )

    def draw(self, screen, camera):
        screen.fill((38, 43, 47))

        # =====================================================
        # OUTER FLOOR
        # =====================================================

        floor = pygame.Rect(
            40 - camera.x,
            40 - camera.y,
            self.width - 80,
            self.height - 80
        )

        pygame.draw.rect(
            screen,
            (104, 88, 67),
            floor
        )

        pygame.draw.rect(
            screen,
            (216, 176, 103),
            floor,
            5
        )

        # =====================================================
        # MAIN BATTLE ARENA
        # =====================================================

        arena = pygame.Rect(
            260 - camera.x,
            145 - camera.y,
            1080,
            710
        )

        pygame.draw.rect(
            screen,
            (55, 105, 62),
            arena
        )

        pygame.draw.rect(
            screen,
            (222, 187, 111),
            arena,
            6
        )

        # Arena floor grid.
        for x in range(300, 1320, 80):
            pygame.draw.line(
                screen,
                (67, 119, 71),
                (x - camera.x, 150 - camera.y),
                (x - camera.x, 850 - camera.y),
                1
            )

        for y in range(190, 850, 80):
            pygame.draw.line(
                screen,
                (67, 119, 71),
                (265 - camera.x, y - camera.y),
                (1335 - camera.x, y - camera.y),
                1
            )

        # =====================================================
        # LEFT ENTRY CORRIDOR
        # =====================================================

        corridor = pygame.Rect(
            70 - camera.x,
            390 - camera.y,
            250,
            220
        )

        pygame.draw.rect(
            screen,
            (74, 66, 57),
            corridor
        )

        pygame.draw.rect(
            screen,
            (229, 195, 119),
            corridor,
            5
        )

        # Entry door.
        door = pygame.Rect(
            245 - camera.x,
            450 - camera.y,
            55,
            100
        )

        pygame.draw.rect(
            screen,
            (35, 42, 45),
            door
        )

        pygame.draw.rect(
            screen,
            (245, 201, 55),
            door,
            3
        )

        # =====================================================
        # BATTLE OBSTACLES
        # =====================================================

        obstacles = [
            (390, 250, 90, 90),
            (1110, 250, 90, 90),
            (390, 690, 90, 90),
            (1110, 690, 90, 90),
            (740, 300, 120, 70),
            (740, 630, 120, 70),
        ]

        for x, y, w, h in obstacles:
            r = pygame.Rect(
                x - camera.x,
                y - camera.y,
                w,
                h
            )

            pygame.draw.rect(
                screen,
                (74, 79, 82),
                r
            )

            pygame.draw.rect(
                screen,
                (35, 39, 41),
                r,
                4
            )

            pygame.draw.rect(
                screen,
                (110, 120, 122),
                (
                    r.x + 10,
                    r.y + 10,
                    r.width - 20,
                    12
                )
            )

        # =====================================================
        # CONTROL ROOM / HOD AREA
        # =====================================================

        control = pygame.Rect(
            1260 - camera.x,
            420 - camera.y,
            240,
            190
        )

        pygame.draw.rect(
            screen,
            (93, 63, 55),
            control
        )

        pygame.draw.rect(
            screen,
            (239, 191, 100),
            control,
            5
        )

        # Computer desks.
        for px in (1290, 1370):
            pygame.draw.rect(
                screen,
                (38, 46, 49),
                (
                    px - camera.x,
                    475 - camera.y,
                    60,
                    35
                )
            )

            pygame.draw.rect(
                screen,
                (74, 143, 173),
                (
                    px + 7 - camera.x,
                    482 - camera.y,
                    46,
                    22
                )
            )

        # =====================================================
        # WARNING SIGNS
        # =====================================================

        self._warning(
            screen,
            520 - camera.x,
            180 - camera.y
        )

        self._warning(
            screen,
            1030 - camera.x,
            180 - camera.y
        )

        # =====================================================
        # LABELS
        # =====================================================

        self._label(
            screen,
            "AI BLOCK - RESTRICTED AREA",
            800 - camera.x,
            78 - camera.y,
            30,
            (245, 201, 55)
        )

        self._label(
            screen,
            "BATTLEFIELD",
            800 - camera.x,
            125 - camera.y,
            22,
            (235, 235, 225)
        )

        self._label(
            screen,
            "HOD CONTROL ROOM",
            1380 - camera.x,
            645 - camera.y,
            20,
            (255, 230, 150)
        )

        # =====================================================
        # OBJECTIVE PANEL
        # =====================================================

        panel = pygame.Rect(
            70,
            25,
            365,
            105
        )

        pygame.draw.rect(
            screen,
            (12, 16, 18),
            panel,
            border_radius=8
        )

        pygame.draw.rect(
            screen,
            (245, 201, 55),
            panel,
            2,
            border_radius=8
        )

        font = pygame.font.Font(None, 26)
        small = pygame.font.Font(None, 21)

        screen.blit(
            font.render(
                "AI BLOCK MISSION",
                True,
                (245, 201, 55)
            ),
            (panel.x + 18, panel.y + 15)
        )

        screen.blit(
            small.render(
                "Objective: Secure the AI Block",
                True,
                (240, 240, 235)
            ),
            (panel.x + 18, panel.y + 49)
        )

        screen.blit(
            small.render(
                "Investigate the infected area.",
                True,
                (185, 195, 195)
            ),
            (panel.x + 18, panel.y + 74)
        )

    def _warning(self, screen, x, y):
        points = [
            (x, y - 22),
            (x - 22, y + 18),
            (x + 22, y + 18)
        ]

        pygame.draw.polygon(
            screen,
            (245, 201, 55),
            points
        )

        pygame.draw.polygon(
            screen,
            (30, 30, 30),
            [
                (x, y - 15),
                (x - 15, y + 12),
                (x + 15, y + 12)
            ]
        )

        pygame.draw.rect(
            screen,
            (245, 201, 55),
            (x - 2, y - 8, 4, 13)
        )

        pygame.draw.circle(
            screen,
            (245, 201, 55),
            (x, y + 10),
            2
        )

    def _label(
        self,
        screen,
        text,
        x,
        y,
        size,
        color
    ):
        font = pygame.font.Font(None, size)

        shadow = font.render(
            text,
            True,
            (10, 10, 10)
        )

        surface = font.render(
            text,
            True,
            color
        )

        rect = surface.get_rect(
            center=(int(x), int(y))
        )

        screen.blit(
            shadow,
            rect.move(3, 3)
        )

        screen.blit(
            surface,
            rect
        )
