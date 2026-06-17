import pygame


class Camera:
    """
    Smooth-feeling top-down camera with a dead zone.

    The player is NOT permanently locked to the center of the screen.
    The camera only moves when the player leaves the inner safe area.
    """

    def __init__(
        self,
        screen_width,
        screen_height,
        world_width,
        world_height
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.world_width = world_width
        self.world_height = world_height

        self.x = 0.0
        self.y = 0.0

        # The player can move inside this area without the camera moving.
        self.deadzone_left = int(screen_width * 0.30)
        self.deadzone_right = int(screen_width * 0.70)
        self.deadzone_top = int(screen_height * 0.30)
        self.deadzone_bottom = int(screen_height * 0.70)

    def update(self, target):
        target_screen_x = target.rect.centerx - self.x
        target_screen_y = target.rect.centery - self.y

        # Horizontal camera movement.
        if target_screen_x < self.deadzone_left:
            self.x = target.rect.centerx - self.deadzone_left

        elif target_screen_x > self.deadzone_right:
            self.x = target.rect.centerx - self.deadzone_right

        # Vertical camera movement.
        if target_screen_y < self.deadzone_top:
            self.y = target.rect.centery - self.deadzone_top

        elif target_screen_y > self.deadzone_bottom:
            self.y = target.rect.centery - self.deadzone_bottom

        # Keep camera inside world.
        max_x = max(
            0,
            self.world_width - self.screen_width
        )

        max_y = max(
            0,
            self.world_height - self.screen_height
        )

        self.x = max(
            0,
            min(self.x, max_x)
        )

        self.y = max(
            0,
            min(self.y, max_y)
        )
