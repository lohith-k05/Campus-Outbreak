
import pygame


class MechanicalCombatUI:
    def __init__(self):
        self.title = pygame.font.Font(None, 30)
        self.big = pygame.font.Font(None, 40)
        self.font = pygame.font.Font(None, 23)
        self.small = pygame.font.Font(None, 18)

    def panel(self, screen, rect, border=(100, 91, 70)):
        pygame.draw.rect(
            screen, (7, 10, 13), rect, border_radius=10
        )
        pygame.draw.rect(
            screen, border, rect, 2, border_radius=10
        )

    def draw(self, screen, combat):
        # Stage card.
        card = pygame.Rect(20, 18, 365, 118)
        self.panel(screen, card)

        screen.blit(
            self.title.render(
                "MECHANICAL BLOCK",
                True, (224, 190, 106)
            ),
            (card.x + 15, card.y + 12)
        )

        screen.blit(
            self.font.render(
                f"STAGE {combat.stage} / 3",
                True, (235, 235, 229)
            ),
            (card.x + 15, card.y + 48)
        )

        screen.blit(
            self.small.render(
                f"INFECTED STUDENTS  {combat.target_total}",
                True, (195, 198, 193)
            ),
            (card.x + 125, card.y + 50)
        )

        screen.blit(
            self.small.render(
                f"SPAWNED  {combat.spawned}/{combat.target_total}",
                True, (155, 163, 160)
            ),
            (card.x + 15, card.y + 80)
        )

        # Immunity.
        hp = pygame.Rect(405, 18, 250, 76)
        self.panel(screen, hp, (86, 94, 91))

        screen.blit(
            self.small.render(
                "IMMUNITY",
                True, (170, 178, 174)
            ),
            (hp.x + 14, hp.y + 10)
        )

        value_color = (
            (105, 225, 125)
            if combat.immunity > 35
            else (225, 75, 60)
        )

        screen.blit(
            self.font.render(
                f"{combat.immunity}/100",
                True, value_color
            ),
            (hp.x + 14, hp.y + 34)
        )

        # Ammo.
        ammo = pygame.Rect(
            screen.get_width() - 245,
            screen.get_height() - 100,
            225, 80
        )
        self.panel(screen, ammo, (105, 96, 76))

        screen.blit(
            self.big.render(
                f"{combat.ammo:02d}/12",
                True, (239, 222, 183)
            ),
            (ammo.x + 15, ammo.y + 9)
        )

        reload_text = (
            f"RELOADING  {max(0, combat.reload_timer):.1f}s"
            if combat.reloading else
            "R  RELOAD"
        )

        screen.blit(
            self.small.render(
                reload_text,
                True, (225, 179, 72)
                if combat.reloading else (160, 166, 163)
            ),
            (ammo.x + 15, ammo.y + 51)
        )

        # Respawns.
        screen.blit(
            self.small.render(
                f"RESPAWNS  {combat.respawns_left}/3",
                True, (195, 198, 193)
            ),
            (screen.get_width() - 180, 105)
        )

        # Controls.
        controls = pygame.Rect(
            20, screen.get_height() - 58, 480, 40
        )
        self.panel(screen, controls, (70, 75, 77))

        screen.blit(
            self.small.render(
                "WASD / ARROWS  MOVE    LMB  FIRE    R  RELOAD",
                True, (205, 209, 204)
            ),
            (controls.x + 12, controls.y + 11)
        )

        if combat.stage_complete and not combat.chapter_complete:
            message = self.font.render(
                f"STAGE {combat.stage} CLEARED  •  PRESS E",
                True, (110, 230, 125)
            )
            screen.blit(
                message,
                message.get_rect(
                    center=(screen.get_width() // 2, 112)
                )
            )

        if combat.chapter_complete:
            self._completion(screen)

    def _completion(self, screen):
        overlay = pygame.Surface(
            screen.get_size(), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 145))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect(290, 220, 700, 250)
        self.panel(screen, box, (100, 220, 125))

        screen.blit(
            self.big.render(
                "MECHANICAL BLOCK SECURED",
                True, (110, 230, 125)
            ),
            self.big.render(
                "MECHANICAL BLOCK SECURED",
                True, (110, 230, 125)
            ).get_rect(center=(box.centerx, box.y + 62))
        )

        for i, line in enumerate([
            "10 students have been rescued.",
            "They know about faculty members in the Library.",
        ]):
            s = self.font.render(
                line, True, (235, 237, 233)
            )
            screen.blit(
                s,
                s.get_rect(
                    center=(box.centerx, box.y + 120 + i * 35)
                )
            )
