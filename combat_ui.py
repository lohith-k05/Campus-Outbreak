import pygame


class CombatUI:

    def __init__(self):

        self.title_font = pygame.font.Font(
            None,
            28
        )

        self.text_font = pygame.font.Font(
            None,
            23
        )

        self.small_font = pygame.font.Font(
            None,
            20
        )

        self.large_font = pygame.font.Font(
            None,
            48
        )

    def _panel(
        self,
        screen,
        rect,
        fill=(10, 14, 16),
        border=(90, 100, 105),
        width=2
    ):

        pygame.draw.rect(
            screen,
            fill,
            rect,
            border_radius=9
        )

        pygame.draw.rect(
            screen,
            border,
            rect,
            width,
            border_radius=9
        )

    def draw(self, screen, combat):

        # =====================================================
        # COMBAT STATUS - TOP RIGHT
        # =====================================================

        panel = pygame.Rect(
            screen.get_width() - 430,
            24,
            405,
            155
        )

        self._panel(
            screen,
            panel,
            (8, 12, 15),
            (185, 55, 55),
            2
        )

        title = self.title_font.render(
            "AI BLOCK // COMBAT",
            True,
            (245, 201, 55)
        )

        screen.blit(
            title,
            (
                panel.x + 18,
                panel.y + 14
            )
        )

        pygame.draw.line(
            screen,
            (45, 52, 55),
            (
                panel.x + 18,
                panel.y + 48
            ),
            (
                panel.right - 18,
                panel.y + 48
            ),
            1
        )

        # Completed state.
        if combat.combat_complete:

            status = self.text_font.render(
                "AREA SECURED",
                True,
                (110, 230, 125)
            )

            screen.blit(
                status,
                (
                    panel.x + 18,
                    panel.y + 62
                )
            )

            infected = self.text_font.render(
                "INFECTED: 0",
                True,
                (110, 230, 125)
            )

            kills = self.text_font.render(
                f"KILLS: {combat.kills}",
                True,
                (210, 215, 215)
            )

            screen.blit(
                infected,
                (
                    panel.x + 18,
                    panel.y + 102
                )
            )

            screen.blit(
                kills,
                (
                    panel.x + 220,
                    panel.y + 102
                )
            )

        else:

            wave = self.text_font.render(
                combat.get_wave_text(),
                True,
                (240, 240, 235)
            )

            screen.blit(
                wave,
                (
                    panel.x + 18,
                    panel.y + 62
                )
            )

            infected = self.text_font.render(
                f"INFECTED: {sum(1 for zombie in combat.zombies if zombie.alive)}",
                True,
                (235, 235, 230)
            )

            screen.blit(
                infected,
                (
                    panel.x + 18,
                    panel.y + 102
                )
            )

            kills = self.text_font.render(
                f"KILLS: {combat.kills}",
                True,
                (200, 205, 205)
            )

            screen.blit(
                kills,
                (
                    panel.x + 220,
                    panel.y + 102
                )
            )

        # =====================================================
        # CONTROLS - BOTTOM RIGHT
        # =====================================================

        controls = pygame.Rect(
            screen.get_width() - 430,
            screen.get_height() - 68,
            405,
            44
        )

        self._panel(
            screen,
            controls,
            (8, 12, 15),
            (75, 85, 90),
            2
        )

        control_text = self.small_font.render(
            "WASD / ARROWS  MOVE     LMB  FIRE",
            True,
            (225, 228, 225)
        )

        screen.blit(
            control_text,
            control_text.get_rect(
                center=controls.center
            )
        )

        # =====================================================
        # NEXT OBJECTIVE
        # =====================================================

        if combat.combat_complete:

            objective = pygame.Rect(
                24,
                screen.get_height() - 120,
                460,
                72
            )

            self._panel(
                screen,
                objective,
                (8, 12, 15),
                (110, 230, 125),
                2
            )

            label = self.small_font.render(
                "NEXT OBJECTIVE",
                True,
                (245, 201, 55)
            )

            text = self.small_font.render(
                "Find Viveka Mam  •  Press E",
                True,
                (235, 235, 230)
            )

            screen.blit(
                label,
                (
                    objective.x + 16,
                    objective.y + 10
                )
            )

            screen.blit(
                text,
                (
                    objective.x + 16,
                    objective.y + 37
                )
            )
