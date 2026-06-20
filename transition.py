import pygame


class SceneTransition:
    """
    Reliable full-screen fade transition.

    start_in():
        Game fades from visible -> black.

    start_out():
        Game fades from black -> visible.

    update(dt):
        Advances the transition.

    active:
        True while the fade is running.

    draw(screen):
        Draws the current black overlay.
    """

    def __init__(self, width, height, duration=0.75):
        self.width = width
        self.height = height
        self.duration = max(0.05, duration)

        self.active = False
        self.mode = None
        self.timer = 0.0
        self.alpha = 0

        self.surface = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )

    def start_in(self):
        # Visible -> black
        self.active = True
        self.mode = "IN"
        self.timer = 0.0
        self.alpha = 0

    def start_out(self):
        # Black -> visible
        self.active = True
        self.mode = "OUT"
        self.timer = 0.0
        self.alpha = 255

    def update(self, dt):
        if not self.active:
            return

        self.timer += max(0.0, dt)

        progress = min(
            self.timer / self.duration,
            1.0
        )

        if self.mode == "IN":
            self.alpha = int(255 * progress)

        elif self.mode == "OUT":
            self.alpha = int(255 * (1.0 - progress))

        if progress >= 1.0:
            self.alpha = 255 if self.mode == "IN" else 0
            self.active = False

    def draw(self, screen):
        if self.alpha <= 0:
            return

        self.surface.fill(
            (0, 0, 0, self.alpha)
        )

        screen.blit(
            self.surface,
            (0, 0)
        )
