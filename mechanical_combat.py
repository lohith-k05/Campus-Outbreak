
import random
import pygame

from zombie import Bullet
from student_zombie import StudentZombie
from rescued_student import RescuedStudent


class MechanicalCombat:
    """Three-stage, gradually spawning Mechanical Block combat."""

    STAGE_TOTALS = {1: 15, 2: 20, 3: 35}

    def __init__(self, block):
        self.block = block
        self.stage = 1

        self.zombies = []
        self.bullets = []

        self.spawned = 0
        self.kills = 0
        self.spawn_timer = 0.0
        self.spawn_interval = 2.0

        self.stage_started = False
        self.stage_complete = False
        self.chapter_complete = False

        self.immunity = 100
        self.max_immunity = 100

        self.magazine_size = 12
        self.ammo = 12
        self.reload_duration = 2.0
        self.reload_timer = 0.0
        self.reloading = False

        self.fire_cooldown = 0.0
        self.fire_delay = 0.16

        self.respawns_left = 3

        self.rescued_students = []

    @property
    def target_total(self):
        return self.STAGE_TOTALS[self.stage]

    def start(self):
        self.stage_started = True

    def set_stage(self, stage):
        self.stage = stage
        self.zombies.clear()
        self.bullets.clear()
        self.spawned = 0
        self.spawn_timer = 0.0
        self.spawn_interval = random.uniform(1.7, 2.5)
        self.stage_complete = False

        self.immunity = self.max_immunity
        self.ammo = self.magazine_size
        self.reload_timer = 0.0
        self.reloading = False
        self.fire_cooldown = 0.0
        self.stage_started = True

    def reset_for_retry(self):
        self.respawns_left = 3
        self.rescued_students.clear()
        self.chapter_complete = False
        self.set_stage(1)

    def start_reload(self):
        if not self.reloading and self.ammo < self.magazine_size:
            self.reloading = True
            self.reload_timer = self.reload_duration

    def shoot(self, player, target_x, target_y):
        if self.reloading or self.fire_cooldown > 0:
            return False

        if self.ammo <= 0:
            self.start_reload()
            return False

        dx = target_x - player.rect.centerx
        dy = target_y - player.rect.centery

        # Face the direction of fire.
        if abs(dx) > abs(dy):
            player.direction = "right" if dx > 0 else "left"
        else:
            player.direction = "down" if dy > 0 else "up"

        self.bullets.append(
            Bullet(
                player.rect.centerx,
                player.rect.centery,
                target_x,
                target_y
            )
        )

        self.ammo -= 1
        self.fire_cooldown = self.fire_delay

        if self.ammo == 0:
            self.start_reload()

        return True

    def update(self, player, dt):
        if not self.stage_started or self.chapter_complete:
            return

        self.fire_cooldown = max(0, self.fire_cooldown - dt)

        if self.reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.reloading = False
                self.reload_timer = 0
                self.ammo = self.magazine_size

        # Spawn 2-3 students every ~2 seconds.
        if not self.stage_complete and self.spawned < self.target_total:
            self.spawn_timer += dt

            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0
                remaining = self.target_total - self.spawned
                batch = min(remaining, random.randint(2, 3))

                for _ in range(batch):
                    self._spawn_one(player)

                self.spawn_interval = random.uniform(1.7, 2.6)

        obstacles = self.block.get_collision_rects()

        for zombie in self.zombies:
            zombie.update(
                player, dt,
                self.block.player_bounds,
                obstacles
            )

        for bullet in self.bullets:
            bullet.update(dt)

        new_bullets = []

        for bullet in self.bullets:
            hit = False

            rect = pygame.Rect(
                int(bullet.position.x - bullet.radius),
                int(bullet.position.y - bullet.radius),
                bullet.radius * 2,
                bullet.radius * 2
            )

            for zombie in self.zombies:
                if zombie.alive and rect.colliderect(zombie.rect):
                    if zombie.take_damage(1):
                        self.kills += 1
                    hit = True
                    break

            if not hit and bullet.life > 0:
                new_bullets.append(bullet)

        self.bullets = new_bullets
        self.zombies = [z for z in self.zombies if z.alive]

        # A stage ends only after the complete count has spawned
        # and all spawned students are defeated.
        if self.spawned >= self.target_total and not self.zombies:
            self.stage_complete = True

    def _spawn_one(self, player):
        points = self.block.random_spawn_points()
        random.shuffle(points)

        chosen = points[0]

        for point in points:
            if pygame.Vector2(point).distance_to(
                player.rect.center
            ) > 260:
                chosen = point
                break

        speed = random.uniform(
            68 + self.stage * 3,
            82 + self.stage * 4
        )

        self.zombies.append(
            StudentZombie(
                chosen[0], chosen[1], speed
            )
        )
        self.spawned += 1

    def handle_death(self):
        self.respawns_left -= 1

        if self.respawns_left >= 0:
            return "RESPAWN"

        self.respawns_left = 0
        return "RESTART"

    def next_stage(self):
        if self.stage < 3:
            self.set_stage(self.stage + 1)
        else:
            self.chapter_complete = True
            self.stage_complete = True
            self.zombies.clear()
            self.bullets.clear()
            self.create_rescued_students()

    def create_rescued_students(self):
        if self.rescued_students:
            return

        for i in range(10):
            self.rescued_students.append(
                RescuedStudent(
                    620 + (i % 5) * 48,
                    480 + (i // 5) * 58,
                    i
                )
            )

    def update_rescued_students(self, player, dt):
        if not self.chapter_complete:
            return

        for student in self.rescued_students:
            student.update_follow(
                player, dt, self.block.player_bounds
            )

    def draw(self, screen, camera):
        for bullet in self.bullets:
            bullet.draw(screen, camera)

        for zombie in self.zombies:
            zombie.draw(screen, camera)

        for student in self.rescued_students:
            student.draw(screen, camera)
