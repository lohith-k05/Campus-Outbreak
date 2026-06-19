import pygame


class Player:
    """
    Top-down player for Campus Outbreak.

    Compatible with:
        Player(x, y)
        player.update(dt, world_width, world_height, collision=None)
        player.draw(screen, camera)

    Controls:
        WASD / Arrow Keys
    """

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

        self.width = 32
        self.height = 42

        self.speed = 250

        self.direction = "down"
        self.walking = False

        self.animation_time = 0.0
        self.animation_frame = 0

        self.interaction_radius = 70

        self.rect = pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height
        )

    # =============================================================
    # UPDATE
    # =============================================================

    def update(
        self,
        dt,
        world_width,
        world_height,
        collision=None
    ):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        self.walking = dx != 0 or dy != 0

        # ---------------------------------------------------------
        # Direction
        # ---------------------------------------------------------

        if dx < 0:
            self.direction = "left"
        elif dx > 0:
            self.direction = "right"
        elif dy < 0:
            self.direction = "up"
        elif dy > 0:
            self.direction = "down"

        # ---------------------------------------------------------
        # Normalize movement
        # ---------------------------------------------------------

        movement = pygame.Vector2(dx, dy)

        if movement.length_squared() > 0:
            movement = movement.normalize()

            move_x = movement.x * self.speed * dt
            move_y = movement.y * self.speed * dt

            # -----------------------------------------------------
            # X collision is checked separately.
            # This allows the player to slide along walls.
            # -----------------------------------------------------

            self._move_x(
                move_x,
                world_width,
                collision
            )

            # -----------------------------------------------------
            # Y collision is checked separately.
            # -----------------------------------------------------

            self._move_y(
                move_y,
                world_height,
                collision
            )

        # ---------------------------------------------------------
        # Animation
        # ---------------------------------------------------------

        if self.walking:
            self.animation_time += dt

            if self.animation_time >= 0.12:
                self.animation_time = 0.0
                self.animation_frame = (
                    self.animation_frame + 1
                ) % 4
        else:
            self.animation_time = 0.0
            self.animation_frame = 0

        self.rect.topleft = (
            round(self.x),
            round(self.y)
        )

    # =============================================================
    # COLLISION MOVEMENT
    # =============================================================

    def _move_x(
        self,
        amount,
        world_width,
        collision
    ):
        if amount == 0:
            return

        new_x = self.x + amount

        new_x = max(
            0,
            min(
                new_x,
                world_width - self.width
            )
        )

        test_rect = pygame.Rect(
            round(new_x),
            round(self.y),
            self.width,
            self.height
        )

        if collision is None or not collision.collides(test_rect):
            self.x = new_x

    def _move_y(
        self,
        amount,
        world_height,
        collision
    ):
        if amount == 0:
            return

        new_y = self.y + amount

        new_y = max(
            0,
            min(
                new_y,
                world_height - self.height
            )
        )

        test_rect = pygame.Rect(
            round(self.x),
            round(new_y),
            self.width,
            self.height
        )

        if collision is None or not collision.collides(test_rect):
            self.y = new_y

    # =============================================================
    # AIM / FACING (FIRING ONLY)
    # =============================================================

    def _update_facing_from_mouse(self, screen_x, screen_y):
        # Face the mouse cursor. This works with both cameras because
        # screen_x/screen_y are already camera-adjusted coordinates.
        mouse_x, mouse_y = pygame.mouse.get_pos()

        center_x = screen_x + self.width / 2
        center_y = screen_y + self.height / 2

        dx = mouse_x - center_x
        dy = mouse_y - center_y

        # Avoid jitter when the cursor is directly over the player.
        if abs(dx) < 8 and abs(dy) < 8:
            return

        # The current character art has four directions, so use the
        # dominant axis for stable diagonal aiming.
        if abs(dx) > abs(dy):
            self.direction = "left" if dx < 0 else "right"
        else:
            self.direction = "up" if dy < 0 else "down"

    # =============================================================
    # DRAW
    # =============================================================

    def draw(self, screen, camera):
        screen_x = self.rect.x - camera.x
        screen_y = self.rect.y - camera.y

        # Only use the mouse to change facing while actually firing.
        # When simply walking, the movement direction remains in control
        # of the character's facing direction.
        mouse_buttons = pygame.mouse.get_pressed()

        if mouse_buttons[0]:
            self._update_facing_from_mouse(
                screen_x,
                screen_y
            )

        self._draw_shadow(
            screen,
            screen_x,
            screen_y
        )

        self._draw_character(
            screen,
            screen_x,
            screen_y
        )

    # =============================================================
    # SHADOW
    # =============================================================

    def _draw_shadow(self, screen, x, y):
        pygame.draw.ellipse(
            screen,
            (24, 42, 25),
            (
                x + 2,
                y + 34,
                29,
                10
            )
        )

    # =============================================================
    # CHARACTER
    # =============================================================

    def _draw_character(self, screen, x, y):
        bob = 0

        if self.walking and self.animation_frame in (1, 3):
            bob = -2

        skin = (226, 177, 135)
        skin_dark = (174, 112, 82)

        hair = (45, 31, 28)
        hair_light = (72, 48, 38)

        shirt = (40, 86, 132)
        shirt_light = (62, 119, 170)
        shirt_dark = (27, 57, 91)

        pants = (45, 48, 58)
        pants_light = (69, 72, 82)

        shoes = (28, 28, 30)

        weapon = (45, 48, 50)
        weapon_light = (105, 108, 105)

        cx = x + self.width // 2
        top = y + 1 + bob

        # ---------------------------------------------------------
        # Legs
        # ---------------------------------------------------------

        left_leg_x = cx - 9
        right_leg_x = cx + 1

        if self.walking:
            if self.animation_frame in (1, 2):
                left_leg_x -= 2
                right_leg_x += 2
            else:
                left_leg_x += 2
                right_leg_x -= 2

        pygame.draw.rect(
            screen,
            pants,
            (left_leg_x, top + 27, 8, 11)
        )

        pygame.draw.rect(
            screen,
            pants_light,
            (right_leg_x, top + 27, 8, 11)
        )

        pygame.draw.rect(
            screen,
            shoes,
            (left_leg_x - 2, top + 36, 11, 5),
            border_radius=2
        )

        pygame.draw.rect(
            screen,
            shoes,
            (right_leg_x - 1, top + 36, 11, 5),
            border_radius=2
        )

        # ---------------------------------------------------------
        # Body
        # ---------------------------------------------------------

        body = pygame.Rect(
            cx - 12,
            top + 13,
            24,
            18
        )

        pygame.draw.rect(
            screen,
            shirt_dark,
            body,
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            shirt,
            (
                body.x + 3,
                body.y + 2,
                body.width - 6,
                body.height - 5
            ),
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            shirt_light,
            (
                body.x + 5,
                body.y + 4,
                5,
                9
            ),
            border_radius=2
        )

        pygame.draw.rect(
            screen,
            (235, 205, 82),
            (
                body.centerx - 3,
                body.y + 5,
                6,
                5
            )
        )

        # ---------------------------------------------------------
        # Head
        # ---------------------------------------------------------

        head = pygame.Rect(
            cx - 10,
            top + 1,
            20,
            18
        )

        pygame.draw.rect(
            screen,
            skin_dark,
            head,
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            skin,
            (
                head.x + 2,
                head.y + 2,
                16,
                14
            ),
            border_radius=5
        )

        # ---------------------------------------------------------
        # Hair
        # ---------------------------------------------------------

        pygame.draw.rect(
            screen,
            hair,
            (
                head.x + 2,
                head.y,
                16,
                7
            ),
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            hair_light,
            (
                head.x + 4,
                head.y + 1,
                7,
                3
            ),
            border_radius=2
        )

        # ---------------------------------------------------------
        # Face
        # ---------------------------------------------------------

        if self.direction == "down":
            pygame.draw.rect(
                screen,
                (55, 45, 42),
                (cx - 6, top + 11, 3, 2)
            )
            pygame.draw.rect(
                screen,
                (55, 45, 42),
                (cx + 3, top + 11, 3, 2)
            )

        elif self.direction == "left":
            pygame.draw.rect(
                screen,
                (55, 45, 42),
                (cx - 8, top + 10, 3, 2)
            )

        elif self.direction == "right":
            pygame.draw.rect(
                screen,
                (55, 45, 42),
                (cx + 5, top + 10, 3, 2)
            )

        # ---------------------------------------------------------
        # Weapon / arms
        # ---------------------------------------------------------

        if self.direction == "right":

            pygame.draw.rect(
                screen,
                skin,
                (cx + 8, top + 16, 10, 6),
                border_radius=3
            )

            pygame.draw.line(
                screen,
                weapon,
                (cx + 11, top + 19),
                (cx + 25, top + 13),
                5
            )

            pygame.draw.line(
                screen,
                weapon_light,
                (cx + 13, top + 18),
                (cx + 24, top + 14),
                2
            )

        elif self.direction == "left":

            pygame.draw.rect(
                screen,
                skin,
                (cx - 18, top + 16, 10, 6),
                border_radius=3
            )

            pygame.draw.line(
                screen,
                weapon,
                (cx - 11, top + 19),
                (cx - 25, top + 13),
                5
            )

            pygame.draw.line(
                screen,
                weapon_light,
                (cx - 13, top + 18),
                (cx - 24, top + 14),
                2
            )

        else:

            pygame.draw.line(
                screen,
                weapon,
                (cx + 8, top + 18),
                (cx + 18, top + 24),
                5
            )

            pygame.draw.line(
                screen,
                weapon_light,
                (cx + 9, top + 18),
                (cx + 17, top + 23),
                2
            )

    # =============================================================
    # INTERACTION HELPERS
    # =============================================================

    def get_center(self):
        return pygame.Vector2(
            self.rect.centerx,
            self.rect.centery
        )

    def distance_to(self, point):
        return self.get_center().distance_to(
            pygame.Vector2(point)
        )

    def near(self, rect):
        return self.rect.colliderect(
            rect.inflate(
                self.interaction_radius,
                self.interaction_radius
            )
        )
