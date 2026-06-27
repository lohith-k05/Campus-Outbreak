import pygame


class AIBlockInteraction:
    """
    AI Block entrance interaction.

    Behavior:
    1. Show [E] ENTER AI BLOCK when player is near the entrance.
    2. When E is pressed, show a visible ENTERING AI BLOCK overlay.
    3. Keep the overlay visible for 2 seconds.
    4. Return True once when E is pressed.
    """

    def __init__(self, campus):
        self.campus = campus

        self.active = False
        self.enter_requested = False

        self.entering = False
        self.enter_timer = 0.0

        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 64)

    def update(self, player, events, dt=0.0):
        # Detect the entrance every frame.
        self.active = player.near(
            self.campus.ai_entrance_zone
        )

        self.enter_requested = False

        # Do not allow another E press while the entry screen is active.
        if not self.entering and self.active:

            for event in events:

                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_e
                ):
                    self.enter_requested = True
                    self.entering = True
                    self.enter_timer = 0.0

                    print("AI BLOCK ENTERED")
                    print("ENTERING AI BLOCK...")

                    break

        # Run the visible entry screen timer.
        if self.entering:

            self.enter_timer += dt

            if self.enter_timer >= 2.0:
                self.entering = False

        return self.enter_requested

    def draw(self, screen):

        # =====================================================
        # NORMAL [E] PROMPT
        # =====================================================

        if self.active and not self.entering:

            width = 300
            height = 54

            x = screen.get_width() // 2 - width // 2
            y = screen.get_height() - 105

            panel = pygame.Rect(
                x,
                y,
                width,
                height
            )

            pygame.draw.rect(
                screen,
                (8, 8, 10),
                panel.move(5, 5),
                border_radius=8
            )

            pygame.draw.rect(
                screen,
                (20, 25, 28),
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

            text = self.font.render(
                "[E]  ENTER AI BLOCK",
                True,
                (245, 245, 235)
            )

            screen.blit(
                text,
                text.get_rect(center=panel.center)
            )

            info = self.small_font.render(
                "Press E to enter",
                True,
                (180, 190, 190)
            )

            screen.blit(
                info,
                info.get_rect(
                    center=(
                        panel.centerx,
                        panel.bottom + 18
                    )
                )
            )

        # =====================================================
        # ENTRY SCREEN
        # =====================================================

        if self.entering:

            overlay = pygame.Surface(
                screen.get_size(),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 210)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            title = self.big_font.render(
                "ENTERING AI BLOCK",
                True,
                (245, 201, 55)
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(
                        screen.get_width() // 2,
                        screen.get_height() // 2 - 35
                    )
                )
            )

            subtitle = self.font.render(
                "Investigating the outbreak...",
                True,
                (235, 235, 235)
            )

            screen.blit(
                subtitle,
                subtitle.get_rect(
                    center=(
                        screen.get_width() // 2,
                        screen.get_height() // 2 + 25
                    )
                )
            )

            # Simple loading bar.
            bar_width = 420
            bar_height = 10

            bar_x = (
                screen.get_width() // 2
                - bar_width // 2
            )

            bar_y = (
                screen.get_height() // 2
                + 70
            )

            pygame.draw.rect(
                screen,
                (55, 55, 60),
                (
                    bar_x,
                    bar_y,
                    bar_width,
                    bar_height
                ),
                border_radius=5
            )

            progress = min(
                self.enter_timer / 2.0,
                1.0
            )

            pygame.draw.rect(
                screen,
                (245, 201, 55),
                (
                    bar_x,
                    bar_y,
                    int(bar_width * progress),
                    bar_height
                ),
                border_radius=5
            )
