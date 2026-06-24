import pygame


class AICombat:
    """
    Wave-based combat used only inside the AI Block.

    The player enters the AI scene and receives four waves:
        Wave 1: 3 zombies
        Wave 2: 5 zombies
        Wave 3: 7 zombies
        Wave 4: 9 zombies

    After the final wave is defeated, combat_complete becomes True.
    """

    def __init__(self, zombie_class, bullet_class):
        self.Zombie = zombie_class
        self.Bullet = bullet_class

        self.waves = [
            (3, 72),
            (5, 80),
            (7, 88),
            (9, 96),
        ]

        self.wave_index = -1
        self.zombies = []
        self.bullets = []

        self.spawn_points = [
            (430, 235),
            (650, 230),
            (900, 230),
            (1160, 255),
            (380, 680),
            (620, 735),
            (930, 720),
            (1180, 675),
            (1320, 500),
        ]

        self.wave_started = False
        self.wave_delay = 1.0
        self.wave_timer = 0.0

        self.combat_complete = False

        self.shots_fired = 0
        self.kills = 0

    def start(self):
        if self.wave_started or self.combat_complete:
            return

        self.wave_index = 0
        self.wave_timer = self.wave_delay
        self.wave_started = True

    def _spawn_wave(self):
        count, speed = self.waves[self.wave_index]

        self.zombies.clear()

        for i in range(count):
            x, y = self.spawn_points[
                i % len(self.spawn_points)
            ]

            # Slight offset prevents identical overlap.
            x += (i // len(self.spawn_points)) * 35
            y += (i // len(self.spawn_points)) * 25

            self.zombies.append(
                self.Zombie(
                    x,
                    y,
                    speed
                )
            )

    def update(self, player, dt, world_rect):
        if not self.wave_started:
            return

        if self.combat_complete:
            return

        # Start current wave after its intro delay.
        if self.wave_timer > 0:
            self.wave_timer -= dt

            if self.wave_timer <= 0:
                self._spawn_wave()

            return

        for zombie in self.zombies:
            zombie.update(
                player,
                dt,
                world_rect
            )

        for bullet in self.bullets:
            bullet.update(dt)

        # Bullet / zombie collisions.
        for bullet in self.bullets:
            if not bullet.alive():
                continue

            bullet_rect = pygame.Rect(
                int(
                    bullet.position.x
                    - bullet.radius
                ),
                int(
                    bullet.position.y
                    - bullet.radius
                ),
                bullet.radius * 2,
                bullet.radius * 2
            )

            for zombie in self.zombies:

                if (
                    zombie.alive
                    and
                    bullet_rect.colliderect(
                        zombie.rect
                    )
                ):
                    killed = zombie.take_damage(1)

                    bullet.life = 0

                    if killed:
                        self.kills += 1

                    break

        self.bullets = [
            bullet
            for bullet in self.bullets
            if bullet.alive()
        ]

        self.zombies = [
            zombie
            for zombie in self.zombies
            if zombie.alive
        ]

        # Current wave finished.
        if len(self.zombies) == 0:

            if self.wave_index >= len(self.waves) - 1:
                self.combat_complete = True
                return

            self.wave_index += 1
            self.wave_timer = self.wave_delay

    def shoot(self, player, mouse_x, mouse_y):
        if not self.wave_started:
            return

        if self.combat_complete:
            return

        bullet = self.Bullet(
            player.rect.centerx,
            player.rect.centery,
            mouse_x,
            mouse_y
        )

        self.bullets.append(bullet)
        self.shots_fired += 1

    def draw(self, screen, camera):
        for bullet in self.bullets:
            bullet.draw(
                screen,
                camera
            )

        for zombie in self.zombies:
            zombie.draw(
                screen,
                camera
            )

    def get_wave_text(self):
        if self.combat_complete:
            return "AREA SECURED"

        if not self.wave_started:
            return "COMBAT READY"

        if self.wave_timer > 0:
            return (
                f"WAVE {self.wave_index + 1} INCOMING"
            )

        return (
            f"WAVE {self.wave_index + 1}/"
            f"{len(self.waves)}   "
            f"INFECTED: {len(self.zombies)}"
        )
