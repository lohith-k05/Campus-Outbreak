import pygame
import sys
import random
import os
import ctypes

# VLC/libVLC plays the final-shot MP4 with its embedded video + audio.
try:
    import vlc
except ImportError:
    vlc = None

from player import Player
from camera import Camera
from map import CampusMap
from collision import CollisionSystem
from ai_interaction import AIBlockInteraction
from transition import SceneTransition
from ai_block import AIBlock
from zombie import Zombie, Bullet
from combat import AICombat
from combat_ui import CombatUI
from npc import NPC
from mechanical_block import MechanicalBlock
from mechanical_combat import MechanicalCombat
from mechanical_ui import MechanicalCombatUI
from library_chapter import LibraryChapter
from research_department import ResearchDepartment


# =========================================================
# MAIN BLOCK AUDIO
# =========================================================
# Audio is isolated to the Main Block chapter so the locked
# AI, Mechanical, and Library chapters are not affected.

SOUND_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

_mainblock_sounds = {}
_mainblock_ambient_playing = False


def _load_mainblock_sound(filename):
    if filename in _mainblock_sounds:
        return _mainblock_sounds[filename]

    path = os.path.join(SOUND_ROOT, filename)
    try:
        if not os.path.isfile(path):
            return None
        sound = pygame.mixer.Sound(path)
        _mainblock_sounds[filename] = sound
        return sound
    except (pygame.error, OSError):
        # Missing/unreadable audio must never stop the game.
        return None


def play_mainblock_sound(filename, volume=0.75):
    sound = _load_mainblock_sound(filename)
    if sound is None:
        return
    try:
        sound.set_volume(max(0.0, min(1.0, volume)))
        sound.play()
    except pygame.error:
        pass


def start_mainblock_ambient():
    global _mainblock_ambient_playing
    if _mainblock_ambient_playing:
        return
    sound = _load_mainblock_sound(os.path.join("ambience", "mainblock_ambient.wav"))
    if sound is None:
        return
    try:
        sound.set_volume(0.28)
        sound.play(loops=-1)
        _mainblock_ambient_playing = True
    except pygame.error:
        pass


def stop_mainblock_ambient():
    global _mainblock_ambient_playing
    if not _mainblock_ambient_playing:
        return
    sound = _mainblock_sounds.get(os.path.join("ambience", "mainblock_ambient.wav"))
    if sound is not None:
        try:
            sound.stop()
        except pygame.error:
            pass
    _mainblock_ambient_playing = False


# Audio is optional. If the machine has no mixer/audio device, the game
# continues normally and simply runs without Main Block sounds.
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
except pygame.error:
    pass


# =========================================================
# LIBRARY CHAPTER
# =========================================================
# The Library chapter is intentionally self-contained.  It does
# not modify the AI Block or Mechanical Block combat systems.

LIBRARY_WIDTH = 1800
LIBRARY_HEIGHT = 1100
LIBRARY_MAGAZINE_SIZE = 50
LIBRARY_RELOAD_TIME = 1.0
LIBRARY_MAX_IMMUNITY = 100
LIBRARY_TOTAL_ZOMBIES = 25
LIBRARY_STUDENT_ZOMBIES = 18
LIBRARY_FACULTY_ZOMBIES = 7

LIBRARY_FALL_DURATION = 1.5
LIBRARY_DOOR_OBSERVE_DURATION = 4.0

class LibraryCollision:
    """Collision system for the Library interior."""
    def __init__(self, width, height, obstacles):
        self.width = width
        self.height = height
        self.obstacles = obstacles

    def collides(self, rect):
        if rect.left < 45 or rect.right > self.width - 45:
            return True
        if rect.top < 95 or rect.bottom > self.height - 45:
            return True
        return any(rect.colliderect(obstacle) for obstacle in self.obstacles)


class LibraryBullet:
    def __init__(self, x, y, target_x, target_y):
        self.pos = pygame.Vector2(x, y)
        direction = pygame.Vector2(target_x - x, target_y - y)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        direction.normalize_ip()
        self.velocity = direction * 920
        self.damage = 1
        self.radius = 4
        self.alive = True

    def update(self, dt, collision):
        self.pos += self.velocity * dt

        rect = pygame.Rect(
            int(self.pos.x - self.radius),
            int(self.pos.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )

        if collision.collides(rect):
            self.alive = False

    def draw(self, surface, camera):
        x = int(self.pos.x - camera.x)
        y = int(self.pos.y - camera.y)
        pygame.draw.circle(surface, (245, 215, 90), (x, y), self.radius)


class LibraryZombie:
    """Student or Faculty infected used only by the Library chapter."""
    def __init__(self, kind, x, y):
        self.kind = kind

        if kind == "faculty":
            self.width = 54
            self.height = 70
            # Faculty infected are larger and faster than the Hero.
            self.speed = 270
            self.max_health = 10
            self.health = 10
            self.damage = 13
            self.attack_interval = 0.55
            self.body_color = (155, 55, 62)
            self.shirt_color = (70, 70, 90)
        else:
            self.width = 40
            self.height = 52
            self.speed = 125
            self.max_health = 1
            self.health = 1
            self.damage = 7
            self.attack_interval = 0.80
            self.body_color = (118, 52, 58)
            self.shirt_color = (58, 78, 100)

        self.rect = pygame.Rect(
            int(x),
            int(y),
            self.width,
            self.height
        )
        self.attack_timer = 0.0
        self.hit_flash = 0.0
        self.alive = True

    def update(self, player, dt, collision):
        if not self.alive:
            return

        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)

        target = pygame.Vector2(player.rect.center)
        current = pygame.Vector2(self.rect.center)
        delta = target - current

        if delta.length_squared() > 1:
            delta.normalize_ip()
            dx = delta.x * self.speed * dt
            dy = delta.y * self.speed * dt

            # Move on each axis separately so shelves act as obstacles.
            candidate = self.rect.move(int(dx), 0)
            if not collision.collides(candidate):
                self.rect = candidate

            candidate = self.rect.move(0, int(dy))
            if not collision.collides(candidate):
                self.rect = candidate

        if self.rect.colliderect(player.rect):
            if self.attack_timer <= 0.0:
                player.library_immunity = max(
                    0,
                    player.library_immunity - self.damage
                )
                self.attack_timer = self.attack_interval

    def draw(self, surface, camera):
        r = self.rect.move(-camera.x, -camera.y)
        color = (245, 235, 225) if self.hit_flash > 0 else self.body_color

        # Shadow
        pygame.draw.ellipse(
            surface,
            (8, 8, 10),
            (r.x - 4, r.bottom - 4, r.width + 8, 13)
        )

        # Body
        pygame.draw.rect(
            surface,
            self.shirt_color,
            (r.x + 5, r.y + 22, r.width - 10, r.height - 22),
            border_radius=7
        )

        # Head
        pygame.draw.circle(
            surface,
            color,
            (r.centerx, r.y + 15),
            13 if self.kind == "student" else 17
        )

        # Hair
        pygame.draw.rect(
            surface,
            (38, 30, 30),
            (r.centerx - 12, r.y + 3, 24, 7),
            border_radius=3
        )

        # Eyes
        eye_y = r.y + 15
        pygame.draw.circle(surface, (225, 55, 55), (r.centerx - 5, eye_y), 2)
        pygame.draw.circle(surface, (225, 55, 55), (r.centerx + 5, eye_y), 2)

        # Faculty marker: larger silhouette + red badge.
        if self.kind == "faculty":
            pygame.draw.rect(
                surface,
                (210, 175, 65),
                (r.centerx - 10, r.y + 29, 20, 5),
                border_radius=2
            )

        # Health bar
        bar_w = r.width + 10
        bar_x = r.centerx - bar_w // 2
        bar_y = r.y - 10
        pygame.draw.rect(
            surface,
            (25, 25, 25),
            (bar_x, bar_y, bar_w, 5)
        )
        health_w = int(
            bar_w * max(0, self.health) / self.max_health
        )
        pygame.draw.rect(
            surface,
            (205, 65, 65),
            (bar_x, bar_y, health_w, 5)
        )


class LibraryChapter:
    """
    Single-stage Library survival encounter.

    25 total enemies:
      - 18 Student Zombies: 1 bullet to kill
      - 7 Faculty Zombies: 10 bullets to kill, larger and faster
    """
    def __init__(self):
        self.width = LIBRARY_WIDTH
        self.height = LIBRARY_HEIGHT

        self.rack_rects = []
        self.table_rects = []
        self.chair_rects = []
        self.obstacles = []

        self._build_layout()
        self.collision = LibraryCollision(
            self.width,
            self.height,
            self.obstacles
        )
        self.camera = Camera(
            WIDTH,
            HEIGHT,
            self.width,
            self.height
        )

        self.zombies = []
        self.bullets = []

        self.spawn_queue = []
        self.spawned = 0
        self.kills = 0
        self.spawn_timer = 0.0
        self.spawn_interval = 0.75

        self.ammo = LIBRARY_MAGAZINE_SIZE
        self.reloading = False
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0

        self.started = False
        self.combat_complete = False
        self.player_dead = False

        self.cinematic_state = "COMBAT"
        self.rack_timer = 0.0
        self.door_timer = 0.0
        self.hidden_door_revealed = False
        self.rack_fallen = False

        self.story_active = False
        self.story_index = 0
        self.story_complete = False

        self.spawn_points = [
            (115, 165),
            (450, 145),
            (830, 150),
            (1220, 155),
            (1570, 180),
            (1600, 480),
            (1500, 850),
            (1120, 920),
            (720, 900),
            (260, 850),
            (120, 560),
        ]

        self.story_dialogue = [
            ("Faculty", "Thank you for rescuing us."),
            ("Faculty", "Our Principal is in the Main Block."),
            ("Faculty", "He is surrounded by so many zombies."),
            ("Faculty", "How are you going to help him?"),
            ("Hero", "I will."),
            ("Hero", "Mam, you have to bring these survivors out of the campus."),
            ("Hero", "I will bring the Principal.")
        ]

    def _build_layout(self):
        # Outer wall racks: the Library should immediately read as a library.
        wall_racks = [
            pygame.Rect(70, 120, 360, 46),
            pygame.Rect(500, 120, 360, 46),
            pygame.Rect(930, 120, 360, 46),
            pygame.Rect(1360, 120, 360, 46),

            pygame.Rect(70, 930, 360, 46),
            pygame.Rect(500, 930, 360, 46),
            pygame.Rect(930, 930, 360, 46),
            pygame.Rect(1360, 930, 360, 46),

            pygame.Rect(70, 220, 42, 290),
            pygame.Rect(70, 580, 42, 290),
            pygame.Rect(1688, 220, 42, 290),
            pygame.Rect(1688, 580, 42, 290),
        ]

        self.rack_rects.extend(wall_racks)

        # Interior shelves create aisles and make the combat area feel dense.
        interior_racks = [
            pygame.Rect(270, 300, 300, 42),
            pygame.Rect(270, 680, 300, 42),
            pygame.Rect(1230, 300, 300, 42),
            pygame.Rect(1230, 680, 300, 42),
            pygame.Rect(700, 255, 42, 250),
            pygame.Rect(1058, 255, 42, 250),
            pygame.Rect(700, 595, 42, 250),
            pygame.Rect(1058, 595, 42, 250),
        ]

        self.rack_rects.extend(interior_racks)

        self.table_rects = [
            pygame.Rect(560, 410, 230, 80),
            pygame.Rect(1010, 410, 230, 80),
            pygame.Rect(560, 760, 230, 80),
            pygame.Rect(1010, 760, 230, 80),
        ]

        self.chair_rects = [
            pygame.Rect(525, 430, 28, 40),
            pygame.Rect(795, 430, 28, 40),
            pygame.Rect(975, 430, 28, 40),
            pygame.Rect(1245, 430, 28, 40),
            pygame.Rect(525, 780, 28, 40),
            pygame.Rect(795, 780, 28, 40),
            pygame.Rect(975, 780, 28, 40),
            pygame.Rect(1245, 780, 28, 40),
        ]

        self.obstacles = self.rack_rects + self.table_rects

    def reset(self):
        self.zombies.clear()
        self.bullets.clear()

        self.spawn_queue = (
            ["student"] * LIBRARY_STUDENT_ZOMBIES
            + ["faculty"] * LIBRARY_FACULTY_ZOMBIES
        )
        random.shuffle(self.spawn_queue)

        self.spawned = 0
        self.kills = 0
        self.spawn_timer = 0.0

        self.ammo = LIBRARY_MAGAZINE_SIZE
        self.reloading = False
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0

        self.started = True
        self.combat_complete = False
        self.player_dead = False

        self.cinematic_state = "COMBAT"
        self.rack_timer = 0.0
        self.door_timer = 0.0
        self.hidden_door_revealed = False
        self.rack_fallen = False

        self.story_active = False
        self.story_index = 0
        self.story_complete = False

    def start(self):
        self.reset()

    def start_reload(self):
        if (
            self.started
            and not self.combat_complete
            and not self.reloading
            and self.ammo < LIBRARY_MAGAZINE_SIZE
        ):
            self.reloading = True
            self.reload_timer = LIBRARY_RELOAD_TIME

    def shoot(self, player, world_mouse_x, world_mouse_y):
        if (
            not self.started
            or self.combat_complete
            or self.player_dead
            or self.reloading
            or self.fire_cooldown > 0
        ):
            return

        if self.ammo <= 0:
            self.start_reload()
            return

        self.bullets.append(
            LibraryBullet(
                player.rect.centerx,
                player.rect.centery,
                world_mouse_x,
                world_mouse_y
            )
        )

        self.ammo -= 1
        self.fire_cooldown = 0.11

        if self.ammo == 0:
            self.start_reload()

    def _find_spawn_position(self, kind):
        # Keep new enemies away from the hero spawn point.
        candidates = self.spawn_points[:]
        random.shuffle(candidates)

        for x, y in candidates:
            rect = pygame.Rect(
                int(x),
                int(y),
                54 if kind == "faculty" else 40,
                70 if kind == "faculty" else 52
            )
            if not self.collision.collides(rect):
                return x, y

        return self.width // 2, 150

    def _spawn_one(self):
        if self.spawned >= len(self.spawn_queue):
            return

        kind = self.spawn_queue[self.spawned]
        x, y = self._find_spawn_position(kind)
        self.zombies.append(
            LibraryZombie(kind, x, y)
        )
        self.spawned += 1

    def update(self, player, dt):
        if not self.started:
            return

        self.fire_cooldown = max(
            0.0,
            self.fire_cooldown - dt
        )

        if self.player_dead:
            return

        # ------------------------------
        # COMBAT
        # ------------------------------
        if not self.combat_complete:
            if self.reloading:
                self.reload_timer -= dt
                if self.reload_timer <= 0:
                    self.reload_timer = 0.0
                    self.reloading = False
                    self.ammo = LIBRARY_MAGAZINE_SIZE

            self.spawn_timer -= dt

            # First group appears immediately; then enemies arrive gradually.
            if self.spawned == 0:
                for _ in range(min(3, len(self.spawn_queue))):
                    self._spawn_one()
                self.spawn_timer = self.spawn_interval

            elif (
                self.spawned < LIBRARY_TOTAL_ZOMBIES
                and self.spawn_timer <= 0
            ):
                self._spawn_one()
                self.spawn_timer = self.spawn_interval

            for bullet in self.bullets:
                bullet.update(dt, self.collision)

                if not bullet.alive:
                    continue

                for zombie in self.zombies:
                    if not zombie.alive:
                        continue

                    if zombie.rect.collidepoint(
                        int(bullet.pos.x),
                        int(bullet.pos.y)
                    ):
                        zombie.health -= bullet.damage
                        zombie.hit_flash = 0.08
                        bullet.alive = False

                        if zombie.health <= 0:
                            zombie.alive = False
                            self.kills += 1
                        break

            self.bullets = [
                bullet for bullet in self.bullets
                if bullet.alive
            ]

            for zombie in self.zombies:
                zombie.update(
                    player,
                    dt,
                    self.collision
                )

            self.zombies = [
                zombie for zombie in self.zombies
                if zombie.alive
            ]

            if (
                self.kills >= LIBRARY_TOTAL_ZOMBIES
                and self.spawned >= LIBRARY_TOTAL_ZOMBIES
                and not self.zombies
            ):
                self.combat_complete = True
                self.cinematic_state = "RACK_FALL"
                self.rack_timer = 0.0
                self.bullets.clear()
                self.reloading = False
                self.reload_timer = 0.0

        # ------------------------------
        # POST-COMBAT CINEMATIC
        # ------------------------------
        elif self.cinematic_state == "RACK_FALL":
            self.rack_timer += dt

            if self.rack_timer >= LIBRARY_FALL_DURATION:
                self.rack_fallen = True
                self.hidden_door_revealed = True
                self.cinematic_state = "DOOR_OBSERVE"
                self.door_timer = 0.0

        elif self.cinematic_state == "DOOR_OBSERVE":
            self.door_timer += dt

            if self.door_timer >= LIBRARY_DOOR_OBSERVE_DURATION:
                self.cinematic_state = "STORY"
                self.story_active = True
                self.story_index = 0

        elif self.cinematic_state == "STORY":
            pass

    def advance_story(self):
        if not self.story_active:
            return

        self.story_index += 1

        if self.story_index >= len(self.story_dialogue):
            self.story_active = False
            self.story_complete = True
            self.cinematic_state = "COMPLETE"

    def focus_camera_on(self, world_x, world_y):
        # Cinematic camera helper: center the requested world point while
        # respecting the camera's world limits.
        max_x = max(0, self.width - WIDTH)
        max_y = max(0, self.height - HEIGHT)

        self.camera.x = max(
            0,
            min(float(world_x) - WIDTH / 2, max_x)
        )
        self.camera.y = max(
            0,
            min(float(world_y) - HEIGHT / 2, max_y)
        )

    def focus_camera_on_door(self):
        door = self.door_rect()
        self.focus_camera_on(door.centerx, door.centery)

    def focus_camera_on_story(self):
        self.focus_camera_on(650, 700)

    def door_rect(self):
        return pygame.Rect(
            860,
            120,
            90,
            18
        )

    def fallen_rack_rect(self):
        return pygame.Rect(
            705,
            105,
            390,
            48
        )

    def draw(self, surface, camera):
        # Library background.
        surface.fill((25, 24, 27))

        # Subtle floor grid.
        grid = 50
        for x in range(0, self.width, grid):
            sx = x - camera.x
            pygame.draw.line(
                surface,
                (34, 34, 38),
                (sx, 90 - camera.y),
                (sx, self.height - camera.y),
                1
            )

        for y in range(100, self.height, grid):
            sy = y - camera.y
            pygame.draw.line(
                surface,
                (34, 34, 38),
                (45 - camera.x, sy),
                (self.width - 45 - camera.x, sy),
                1
            )

        # Outer walls.
        wall = pygame.Rect(
            35 - camera.x,
            65 - camera.y,
            self.width - 70,
            self.height - 85
        )
        pygame.draw.rect(
            surface,
            (10, 13, 15),
            wall,
            8
        )

        # Emergency lighting.
        for x in (180, 650, 1120, 1590):
            pygame.draw.rect(
                surface,
                (100, 75, 42),
                (x - camera.x, 82 - camera.y, 100, 7),
                border_radius=3
            )
            pygame.draw.circle(
                surface,
                (190, 145, 72),
                (x + 50 - camera.x, 86 - camera.y),
                6
            )

        # Long central path highlight.
        path = pygame.Rect(
            775 - camera.x,
            165 - camera.y,
            250,
            720
        )
        pygame.draw.rect(
            surface,
            (29, 29, 32),
            path
        )

        # Wall and interior book racks.
        for rack in self.rack_rects:
            r = rack.move(-camera.x, -camera.y)

            pygame.draw.rect(
                surface,
                (62, 45, 34),
                r,
                border_radius=4
            )
            pygame.draw.rect(
                surface,
                (105, 77, 52),
                r,
                2,
                border_radius=4
            )

            # Books.
            if rack.width > rack.height:
                book_w = 14
                x = r.x + 8
                while x < r.right - 10:
                    h = 22 + ((x // 7) % 18)
                    pygame.draw.rect(
                        surface,
                        (
                            72 + int(x) % 50,
                            55 + int(x) % 40,
                            42 + int(x) % 35
                        ),
                        (
                            x,
                            r.centery - h // 2,
                            book_w,
                            h
                        )
                    )
                    x += 18
            else:
                book_h = 13
                y = r.y + 8
                while y < r.bottom - 10:
                    w = 23 + ((y // 9) % 20)
                    pygame.draw.rect(
                        surface,
                        (
                            65 + int(y) % 50,
                            50 + int(y) % 35,
                            40 + int(y) % 30
                        ),
                        (
                            r.centerx - w // 2,
                            y,
                            w,
                            book_h
                        )
                    )
                    y += 18

        # Tables.
        for table in self.table_rects:
            r = table.move(-camera.x, -camera.y)
            pygame.draw.rect(
                surface,
                (70, 54, 43),
                r,
                border_radius=5
            )
            pygame.draw.rect(
                surface,
                (108, 82, 58),
                r,
                2,
                border_radius=5
            )

        # Chairs.
        for chair in self.chair_rects:
            r = chair.move(-camera.x, -camera.y)
            pygame.draw.rect(
                surface,
                (55, 57, 62),
                r,
                border_radius=4
            )

        # Fallen books and papers.
        for x, y in (
            (210, 190), (380, 520), (590, 220), (1210, 560),
            (1450, 400), (1520, 760), (890, 875), (430, 875)
        ):
            pygame.draw.rect(
                surface,
                (150, 132, 98),
                (x - camera.x, y - camera.y, 17, 11)
            )
            pygame.draw.rect(
                surface,
                (185, 178, 156),
                (x + 5 - camera.x, y + 9 - camera.y, 19, 12)
            )

        # Hidden door.
        if self.hidden_door_revealed:
            door = self.door_rect().move(
                -camera.x,
                -camera.y
            )

            pygame.draw.rect(
                surface,
                (4, 5, 7),
                door
            )
            pygame.draw.rect(
                surface,
                (155, 128, 68),
                door,
                3
            )

            pygame.draw.circle(
                surface,
                (210, 180, 80),
                (door.right - 13, door.centery),
                3
            )

        # Falling/fallen rack cinematic.
        if self.cinematic_state == "RACK_FALL":
            progress = min(
                1.0,
                self.rack_timer / LIBRARY_FALL_DURATION
            )

            rack = self.fallen_rack_rect().move(
                -camera.x,
                -camera.y
            )

            # Simple staged fall: shrink/shift downward.
            offset_y = int(210 * progress * progress)
            angle_shift = int(80 * progress)

            rack = rack.move(
                angle_shift,
                offset_y
            )

            pygame.draw.rect(
                surface,
                (70, 50, 36),
                rack,
                border_radius=4
            )
            pygame.draw.rect(
                surface,
                (130, 92, 58),
                rack,
                3,
                border_radius=4
            )

            for i in range(18):
                bx = rack.x + 8 + i * 20
                pygame.draw.rect(
                    surface,
                    (120 + (i * 7) % 70, 90, 65),
                    (bx, rack.y + 9, 12, 27)
                )

        elif self.rack_fallen:
            rack = self.fallen_rack_rect().move(
                -camera.x,
                -camera.y
            )
            rack = rack.move(80, 210)

            pygame.draw.rect(
                surface,
                (65, 47, 35),
                rack,
                border_radius=4
            )
            pygame.draw.rect(
                surface,
                (120, 85, 55),
                rack,
                3,
                border_radius=4
            )

            for i in range(18):
                bx = rack.x + 8 + i * 20
                pygame.draw.rect(
                    surface,
                    (130 + (i * 5) % 55, 92, 65),
                    (bx, rack.y + 9, 12, 27)
                )

        # Area title.
        title_font = pygame.font.Font(None, 30)
        title = title_font.render(
            "CENTRAL LIBRARY  //  MAIN READING HALL",
            True,
            (205, 198, 177)
        )
        surface.blit(
            title,
            (WIDTH // 2 - title.get_width() // 2, 105)
        )


def draw_library_hud(surface, chapter):
    panel = pygame.Rect(28, 28, 535, 112)

    pygame.draw.rect(
        surface,
        (6, 10, 13),
        panel,
        border_radius=13
    )
    pygame.draw.rect(
        surface,
        (91, 103, 92),
        panel,
        2,
        border_radius=13
    )

    label_font = pygame.font.Font(None, 19)
    title_font = pygame.font.Font(None, 31)
    value_font = pygame.font.Font(None, 27)

    label = label_font.render(
        "LIBRARY SURVIVAL",
        True,
        (178, 184, 181)
    )
    title = title_font.render(
        "KILL ALL 25 INFECTED",
        True,
        (242, 238, 225)
    )

    progress = value_font.render(
        f"DEFEATED  {chapter.kills:02d}/25",
        True,
        (110, 230, 125)
    )

    ammo = value_font.render(
        f"AMMO  {chapter.ammo:02d}/{LIBRARY_MAGAZINE_SIZE}",
        True,
        (245, 201, 55)
    )

    surface.blit(label, (panel.x + 18, panel.y + 11))
    surface.blit(title, (panel.x + 18, panel.y + 38))
    surface.blit(progress, (panel.x + 18, panel.y + 76))
    surface.blit(ammo, (panel.x + 265, panel.y + 76))

    if chapter.reloading:
        reload_font = pygame.font.Font(None, 22)
        reload_text = reload_font.render(
            f"RELOADING  {max(0.0, chapter.reload_timer):.1f}s",
            True,
            (245, 170, 70)
        )
        surface.blit(
            reload_text,
            (panel.right - reload_text.get_width() - 18, panel.y + 13)
        )


def draw_library_objective(surface):
    box = pygame.Rect(
        (WIDTH - 650) // 2,
        24,
        650,
        90
    )

    pygame.draw.rect(
        surface,
        (6, 10, 14),
        box,
        border_radius=13
    )
    pygame.draw.rect(
        surface,
        (225, 183, 58),
        box,
        2,
        border_radius=13
    )

    label_font = pygame.font.Font(None, 18)
    text_font = pygame.font.Font(None, 30)

    label = label_font.render(
        "NEW OBJECTIVE",
        True,
        (225, 183, 58)
    )
    objective = text_font.render(
        "SAVE THE FACULTY IN THE LIBRARY",
        True,
        (242, 243, 238)
    )

    surface.blit(
        label,
        (box.x + 20, box.y + 12)
    )
    surface.blit(
        objective,
        (box.x + 20, box.y + 42)
    )


def draw_library_dialogue(surface, chapter):
    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 135))
    surface.blit(overlay, (0, 0))

    box = pygame.Rect(
        105,
        HEIGHT - 205,
        WIDTH - 210,
        165
    )

    pygame.draw.rect(
        surface,
        (10, 14, 17),
        box,
        border_radius=10
    )
    pygame.draw.rect(
        surface,
        (110, 230, 125),
        box,
        2,
        border_radius=10
    )

    speaker, line = chapter.story_dialogue[
        chapter.story_index
    ]

    speaker_font = pygame.font.Font(None, 30)
    line_font = pygame.font.Font(None, 25)
    hint_font = pygame.font.Font(None, 20)

    speaker_surface = speaker_font.render(
        speaker,
        True,
        (110, 230, 125)
    )
    surface.blit(
        speaker_surface,
        (box.x + 22, box.y + 16)
    )

    words = line.split()
    wrapped = []
    current = ""

    for word in words:
        candidate = (current + " " + word).strip()
        if line_font.size(candidate)[0] > box.width - 44:
            if current:
                wrapped.append(current)
            current = word
        else:
            current = candidate

    if current:
        wrapped.append(current)

    for index, wrapped_line in enumerate(wrapped):
        line_surface = line_font.render(
            wrapped_line,
            True,
            (240, 240, 235)
        )
        surface.blit(
            line_surface,
            (box.x + 22, box.y + 58 + index * 30)
        )

    hint = hint_font.render(
        "Press E to continue",
        True,
        (170, 180, 180)
    )
    surface.blit(
        hint,
        (
            box.right - hint.get_width() - 22,
            box.bottom - 28
        )
    )


pygame.init()


# =========================================================
# WINDOW
# =========================================================

WIDTH = 1280
HEIGHT = 720
FPS = 60

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Campus Outbreak"
)

# Native Windows handle used by VLC to render the final shot
# directly inside the existing Pygame window.
pygame_window_handle = pygame.display.get_wm_info().get("window")

clock = pygame.time.Clock()


# =========================================================
# CAMPUS
# =========================================================

campus = CampusMap()

collision = CollisionSystem(
    campus
)

player = Player(
    campus.main_gate.centerx,
    campus.main_gate.top - 100
)

campus_camera = Camera(
    WIDTH,
    HEIGHT,
    campus.width,
    campus.height
)


# =========================================================
# AI BLOCK
# =========================================================

ai_block = AIBlock()

ai_camera = Camera(
    WIDTH,
    HEIGHT,
    ai_block.width,
    ai_block.height
)


# =========================================================
# INTERACTION
# =========================================================

ai_interaction = AIBlockInteraction(
    campus
)

# Keep the scene transition pending until the AI entry cinematic finishes.
ai_entry_pending = False


# =========================================================
# TRANSITION
# =========================================================

transition = SceneTransition(
    WIDTH,
    HEIGHT,
    duration=0.75
)


# =========================================================
# SCENE STATE
# =========================================================

scene = "GAME_INTRO"

# =========================================================
# GAME START INTRO VIDEO
# =========================================================
# The supplied intro video is shown before the existing BUS opening.
# First frame is displayed at launch; a mouse click starts playback.
GAME_INTRO_VIDEO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "intro",
    "campus_outbreak_intro.mp4"
)

GAME_INTRO_FIRST_FRAME_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "intro",
    "intro_first_frame.png"
)

game_intro_video = None
game_intro_first_frame = None
game_intro_error = None

try:
    if os.path.isfile(GAME_INTRO_FIRST_FRAME_PATH):
        game_intro_first_frame = pygame.image.load(
            GAME_INTRO_FIRST_FRAME_PATH
        ).convert()
        game_intro_first_frame = pygame.transform.smoothscale(
            game_intro_first_frame,
            (WIDTH, HEIGHT)
        )
    else:
        game_intro_error = (
            "Intro first frame not found: "
            + GAME_INTRO_FIRST_FRAME_PATH
        )
except (pygame.error, OSError) as exc:
    game_intro_error = f"Could not load intro first frame: {exc}"


def start_game_intro_video():
    """Start the supplied intro MP4 with its embedded audio."""
    global game_intro_video
    global game_intro_error

    game_intro_error = None

    if not os.path.isfile(GAME_INTRO_VIDEO_PATH):
        game_intro_error = (
            "Intro video not found: " + GAME_INTRO_VIDEO_PATH
        )
        return False

    if vlc is None:
        game_intro_error = (
            "python-vlc is not installed. Run: "
            "python -m pip install python-vlc"
        )
        return False

    if game_intro_video is not None:
        game_intro_video.stop()

    game_intro_video = FinalShotVideo(
        GAME_INTRO_VIDEO_PATH,
        WIDTH,
        HEIGHT,
        pygame_window_handle
    )

    if not game_intro_video.start():
        game_intro_error = game_intro_video.error
        return False

    return True


# =========================================================
# OPENING CINEMATIC
# =========================================================

intro_timer = 0.0

INTRO_BUS_DURATION = 4.0
INTRO_EXIT_DURATION = 2.0
INTRO_REVEAL_DURATION = 2.5



# Opening story states:
# NAME_INPUT_HERO
# NAME_INPUT_FRIEND
# INTRO_DIALOGUE

# Bus starts outside the entrance and drives toward the gate.
bus_width = 190
bus_height = 62

bus_x = campus.main_gate.centerx - 650
bus_y = campus.main_gate.top - 78

bus_target_x = campus.main_gate.centerx - 120

hero_intro_x = float(campus.main_gate.centerx)
hero_intro_y = float(campus.main_gate.top - 100)

gun_picked = False
# Keep the weapon inside the playable campus bounds and just beyond
# the Main Gate so the opening objective can always be completed.
gun_rect = pygame.Rect(
    campus.main_gate.centerx + 95,
    campus.main_gate.bottom + 35,
    24,
    14
)

tutorial_stage = 0

intro_dialogue_active = False
intro_dialogue_index = 0

intro_dialogue = [
    ("HERO", "Something is wrong..."),
    ("HERO", "This college has been infected by zombies."),
    ("HERO", "My friends are still somewhere inside."),
    ("HERO", "I have to save my friends.")
]
objective_active = False
story_objective_active = False

# Valid states:
#
# INTRO_BUS
# INTRO_EXIT
# INTRO_REVEAL
# CAMPUS
# TRANSITION_TO_AI
# AI_BLOCK
# TRANSITION_TO_CAMPUS
# CAMPUS_RETURN
# TRANSITION_TO_MECHANICAL
# MECHANICAL_BLOCK
# TRANSITION_TO_LIBRARY_TRAVEL
# TRANSITION_FROM_LIBRARY
# TRANSITION_TO_MAIN_BLOCK
# MAIN_BLOCK
# RESEARCH_LIBRARY
# RESEARCH_ELEVATOR
# RESEARCH_DEPARTMENT
# BEST_FRIEND_REVEAL
# TRANSITION_TO_BEST_FRIEND_REVEAL
# TRANSITION_TO_FINAL_BOSS
# FINAL_BOSS_INTRO
# FINAL_BOSS
# FINAL_ENDING
# SURVIVORS_ESCAPE
# FINAL_TITLE
# LIBRARY


# =========================================================
# AI INTRO
# =========================================================

ai_intro_timer = 0.0
AI_INTRO_DURATION = 2.5

# =========================================================
# AI COMBAT
# =========================================================

combat = AICombat(
    Zombie,
    Bullet
)

combat_ui = CombatUI()


# =========================================================
# VIVEKA MAM / RESCUE OBJECTIVE
# =========================================================

# Viveka is placed inside the AI Block control room.
viveka = NPC(
    "Viveka Mam",
    1335,
    485,
    (80, 140, 220)
)

viveka_dialogue = [
    (
        "Viveka Mam",
        "You're alive... I thought everyone was gone."
    ),
    (
        "Hero",
        "What happened here, Mam?"
    ),
    (
        "Viveka Mam",
        "The infected students attacked everyone."
    ),
    (
        "Viveka Mam",
        "The infection is spreading across the campus."
    ),
    (
        "Hero",
        "We need to find out what caused this."
    ),
    (
        "Viveka Mam",
        "Then we have to move. The Mechanical Block may need help."
    )
]

dialogue_active = False
dialogue_index = 0
rescue_complete = False
viveka_spawned = False

# Viveka's campus copy appears only after she has been rescued.
viveka_campus = NPC(
    "Viveka Mam",
    player.rect.x - 60,
    player.rect.y + 15,
    (80, 140, 220)
)

viveka_following = False
viveka_follow_speed = 125

# =========================================================
# MECHANICAL BLOCK
# =========================================================

mechanical_block = MechanicalBlock(
    WIDTH,
    HEIGHT
)

mechanical_camera = Camera(
    WIDTH,
    HEIGHT,
    mechanical_block.width,
    mechanical_block.height
)

mechanical_combat = MechanicalCombat(
    mechanical_block
)

mechanical_ui = MechanicalCombatUI()

# =========================================================
# MECHANICAL COMBAT SETTINGS
# =========================================================
# Mechanical Block uses its own ammunition and immunity system.
# Keep these values here so main.py controls the chapter rules.
MECHANICAL_MAGAZINE_SIZE = 50
MECHANICAL_MAX_IMMUNITY = 100
MECHANICAL_RESPAWN_INVULNERABILITY = 1.25

# Player does not normally need this attribute, but StudentZombie
# checks for it before applying Mechanical Block damage.
player.mechanical_immunity = MECHANICAL_MAX_IMMUNITY
player.library_immunity = LIBRARY_MAX_IMMUNITY

mechanical_player_dead = False
mechanical_death_message_timer = 0.0
mechanical_respawn_invulnerability = 0.0


def configure_mechanical_combat():
    """Apply the Mechanical Block ammo/immunity rules."""
    global mechanical_player_dead
    global mechanical_death_message_timer
    global mechanical_respawn_invulnerability

    mechanical_combat.magazine_size = MECHANICAL_MAGAZINE_SIZE
    mechanical_combat.ammo = MECHANICAL_MAGAZINE_SIZE
    mechanical_combat.immunity = MECHANICAL_MAX_IMMUNITY
    mechanical_combat.max_immunity = MECHANICAL_MAX_IMMUNITY

    player.mechanical_immunity = MECHANICAL_MAX_IMMUNITY

    mechanical_player_dead = False
    mechanical_death_message_timer = 0.0
    mechanical_respawn_invulnerability = 0.0


configure_mechanical_combat()


class MechanicalCollision:
    'Collision wrapper for the Mechanical Block arena.'

    def __init__(self, block):
        self.block = block

    def collides(self, rect):
        if not self.block.player_bounds.contains(rect):
            return True

        return any(
            rect.colliderect(obstacle)
            for obstacle in self.block.get_collision_rects()
        )


mechanical_collision = MechanicalCollision(
    mechanical_block
)

# The Mechanical Block entrance is just outside its left side.
MECH_ENTRANCE_ZONE = pygame.Rect(
    campus.mech_block.left - 120,
    campus.mech_block.centery - 75,
    120,
    150
)

mechanical_intro = [
    (
        "Hero",
        "Mam, you see if any students are alive or not."
    ),
    (
        "Hero",
        "I will handle the zombies if they attack us."
    )
]

mechanical_intro_active = False
mechanical_intro_index = 0

mechanical_students_dialogue = [
    (
        "Student",
        "Thank you for saving us."
    ),
    (
        "Student",
        "There are some faculty members in the Library."
    ),
    (
        "Viveka Mam",
        "Let's go and save them."
    ),
    (
        "Hero",
        "I'll save them. You don't worry."
    )
]

mechanical_students_dialogue_active = False
mechanical_students_dialogue_index = 0

mechanical_combat_started = False
mechanical_checkpoint = False
mechanical_objective_active = False



# =========================================================
# LIBRARY STATE
# =========================================================

library_chapter = LibraryChapter()

library_objective_active = False
library_transition_started = False
library_campus_entrance = None
library_player_dead = False
library_death_timer = 0.0
library_survivors_visible = False
library_main_block_objective_active = False

# Research Department progression. This begins only after the Principal is rescued.
research_return_objective_active = False
research_library_transition = False
research_elevator_timer = 0.0
research_elevator_started = False
research_department_complete = False


def resolve_library_campus_entrance():
    """
    Use a Library entrance from CampusMap if one exists.
    Otherwise create a safe, visible fallback location on the campus.
    """
    candidates = (
        "library_entrance",
        "library_gate",
        "library_rect",
        "library"
    )

    for name in candidates:
        value = getattr(campus, name, None)

        if isinstance(value, pygame.Rect):
            return value.copy()

        rect = getattr(value, "rect", None)
        if isinstance(rect, pygame.Rect):
            return rect.copy()

    # Fallback: a dedicated entrance marker on the far side of campus.
    # This does not alter CampusMap or its existing collision geometry.
    x = max(180, campus.width - 420)
    y = max(180, min(campus.height - 220, campus.height // 2))
    return pygame.Rect(x, y, 180, 150)


library_campus_entrance = resolve_library_campus_entrance()

class ResearchDepartmentCollision:
    """Collision adapter for the Research Department."""

    def __init__(self, department):
        self.department = department

    def collides(self, rect):
        # Keep the player inside the research department.
        if rect.left < 45:
            return True

        if rect.right > self.department.width - 45:
            return True

        if rect.top < 45:
            return True

        if rect.bottom > self.department.height - 45:
            return True

        # Use the Research Department's existing obstacles.
        obstacles = getattr(self.department, "obstacles", [])

        return any(
            rect.colliderect(obstacle)
            for obstacle in obstacles
        )


research_department = ResearchDepartment(
    Camera,
    WIDTH,
    HEIGHT
)

# ResearchDepartment.collision is a read-only property that returns
# its obstacle list. Player.update() needs an object exposing
# collides(rect), so keep the adapter separate instead of assigning
# to the read-only property.
research_department_player_collision = ResearchDepartmentCollision(
    research_department
)


# =========================================================
# FINAL STORY: BEST FRIEND / FINAL BOSS
# =========================================================

class FinalBattleCollision:
    """Simple collision adapter for the final-battle arena."""

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def collides(self, rect):
        return (
            rect.left < 55
            or rect.top < 55
            or rect.right > self.width - 55
            or rect.bottom > self.height - 55
        )


class FinalBossBullet:
    """Projectile used only by the final boss chapter."""

    def __init__(self, x, y, target_x, target_y, speed=720):
        self.position = pygame.Vector2(x, y)
        direction = pygame.Vector2(target_x - x, target_y - y)

        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction.normalize_ip()

        self.velocity = direction * speed
        self.radius = 6
        self.life = 1.5

    def update(self, dt):
        self.position += self.velocity * dt
        self.life -= dt

    def alive(self):
        return self.life > 0

    def draw(self, screen, camera):
        x = int(self.position.x - camera.x)
        y = int(self.position.y - camera.y)

        pygame.draw.circle(
            screen,
            (210, 70, 55),
            (x, y),
            self.radius
        )


class FinalBoss:
    """
    Best friend final boss.

    Three phases:
        Phase 1: infected but controlled
        Phase 2: faster and more aggressive
        Phase 3: extremely aggressive
    """

    def __init__(self, x, y):
        self.rect = pygame.Rect(int(x), int(y), 62, 76)
        self.position = pygame.Vector2(x, y)

        self.max_health = 90
        self.health = self.max_health

        self.phase = 1
        self.speed = 78.0

        self.attack_damage = 10
        self.attack_delay = 0.85
        self.attack_timer = 0.8

        self.animation = 0.0
        self.alive = True

        self.bullets = []
        self.shoot_timer = 1.2

    def update(self, player, dt, arena_width, arena_height):
        if not self.alive:
            return

        self.animation += dt
        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.shoot_timer = max(0.0, self.shoot_timer - dt)

        if self.health <= 30:
            self.phase = 3
            self.speed = 150.0
            self.attack_damage = 16
            self.attack_delay = 0.48
        elif self.health <= 60:
            self.phase = 2
            self.speed = 112.0
            self.attack_damage = 12
            self.attack_delay = 0.65
        else:
            self.phase = 1
            self.speed = 78.0
            self.attack_damage = 10
            self.attack_delay = 0.85

        target = pygame.Vector2(
            player.rect.centerx,
            player.rect.centery
        )

        direction = target - self.position
        distance = direction.length()

        if distance > 75:
            direction.normalize_ip()

            self.position.x += direction.x * self.speed * dt
            self.position.y += direction.y * self.speed * dt

            self.position.x = max(
                70,
                min(arena_width - 70, self.position.x)
            )
            self.position.y = max(
                70,
                min(arena_height - 70, self.position.y)
            )

            self.rect.center = (
                round(self.position.x),
                round(self.position.y)
            )

        elif self.attack_timer <= 0:
            if hasattr(player, "final_immunity"):
                player.final_immunity = max(
                    0,
                    player.final_immunity - self.attack_damage
                )

            self.attack_timer = self.attack_delay

        # Ranged attack becomes available in later phases.
        if self.phase >= 2 and self.shoot_timer <= 0:
            self.bullets.append(
                FinalBossBullet(
                    self.rect.centerx,
                    self.rect.centery,
                    target.x,
                    target.y,
                    430 if self.phase == 2 else 520
                )
            )

            self.shoot_timer = 1.8 if self.phase == 2 else 1.05

        for bullet in self.bullets:
            bullet.update(dt)

            if (
                bullet.alive()
                and bullet.position.distance_to(
                    pygame.Vector2(player.rect.center)
                ) < 25
            ):
                if hasattr(player, "final_immunity"):
                    player.final_immunity = max(
                        0,
                        player.final_immunity - (
                            8 if self.phase == 2 else 12
                        )
                    )
                bullet.life = 0

        self.bullets = [
            bullet for bullet in self.bullets
            if bullet.alive()
        ]

    def take_damage(self, damage=1):
        if not self.alive:
            return

        self.health = max(0, self.health - damage)

        if self.health <= 0:
            self.alive = False

    def draw(self, screen, camera):
        if not self.alive:
            return

        x = int(self.rect.centerx - camera.x)
        y = int(self.rect.centery - camera.y)

        bob = -3 if int(self.animation * 6) % 2 else 0

        # Shadow
        pygame.draw.ellipse(
            screen,
            (8, 8, 9),
            (x - 34, y + 30, 68, 18)
        )

        # Body
        body_color = (
            (82, 72, 72) if self.phase == 1
            else (104, 58, 58) if self.phase == 2
            else (132, 42, 42)
        )

        pygame.draw.rect(
            screen,
            body_color,
            (x - 27, y - 5 + bob, 54, 60),
            border_radius=12
        )

        # Head
        pygame.draw.circle(
            screen,
            (148, 100, 82),
            (x, y - 25 + bob),
            23
        )

        # Hair
        pygame.draw.rect(
            screen,
            (35, 30, 29),
            (x - 19, y - 47 + bob, 38, 10),
            border_radius=5
        )

        # Eyes
        eye_color = (
            (190, 45, 45) if self.phase >= 2
            else (120, 35, 35)
        )

        pygame.draw.circle(
            screen,
            eye_color,
            (x - 8, y - 27 + bob),
            4
        )
        pygame.draw.circle(
            screen,
            eye_color,
            (x + 8, y - 27 + bob),
            4
        )

        # Phase indicator / health bar
        bar_w = 110
        bar_h = 10
        bar_x = x - bar_w // 2
        bar_y = y - 82

        pygame.draw.rect(
            screen,
            (20, 20, 22),
            (bar_x, bar_y, bar_w, bar_h),
            border_radius=4
        )

        fill = int(
            bar_w * (self.health / self.max_health)
        )

        pygame.draw.rect(
            screen,
            (205, 55, 50),
            (bar_x, bar_y, fill, bar_h),
            border_radius=4
        )

        for bullet in self.bullets:
            bullet.draw(screen, camera)


class FinalBattleDialogue:
    def __init__(self):
        self.lines = [
            ("Hero", "Is there a cure?"),
            ("Doctor", "No... there is no cure."),
            ("Hero", "What the fuck? Then why did you guys lie to me?"),
            ("Hero", "Tell me... you guys are responsible for this, right?"),
            ("Doctor", "Yes..."),
            ("Doctor", "During our experiment, we released a type of gas into the campus atmosphere."),
            ("Doctor", "We didn't realize it would cause consequences like this."),
            ("Hero", "You guys are responsible for this shit!"),
            ("Doctor", "There is one more person you need to see."),
            ("Hero", "Who?"),
            ("Doctor", "Your best friend."),
            ("Doctor", "He was exposed during the experiment."),
            ("Hero", "No..."),
        ]
        self.index = 0
        self.active = True

    def advance(self):
        self.index += 1

        if self.index >= len(self.lines):
            self.active = False


final_battle_collision = FinalBattleCollision(
    1800,
    1100
)

final_battle_camera = Camera(
    WIDTH,
    HEIGHT,
    1800,
    1100
)

final_boss = FinalBoss(
    1350,
    550
)

final_battle_dialogue = FinalBattleDialogue()

final_battle_bullets = []
final_battle_ammo = 50
FINAL_BATTLE_MAGAZINE = 50
FINAL_BATTLE_RELOAD_TIME = 1.0
final_battle_reloading = False
final_battle_reload_timer = 0.0

player.final_immunity = 100

best_friend_intro_timer = 0.0
best_friend_intro_duration = 3.5

# =========================================================
# FINAL SHOT / ENDING CINEMATIC
# =========================================================
# Put the supplied video here:
#     ending/final_shot.mp4
#
# The final shot is intentionally separated from the boss fight:
# the player must explicitly click SHOOT before the video starts.
FINAL_SHOT_VIDEO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ending",
    "final_shot.mp4"
)

final_shot_button = pygame.Rect(
    WIDTH // 2 - 145,
    HEIGHT // 2 + 85,
    290,
    72
)

final_ending_timer = 0.0
final_ending_finished = False
final_ending_fade_alpha = 0

FINAL_ENDING_WALK_DURATION = 3.8
FINAL_ENDING_HOLD_DURATION = 7.0
FINAL_ENDING_TOTAL_DURATION = (
    FINAL_ENDING_WALK_DURATION + FINAL_ENDING_HOLD_DURATION
)
FINAL_ENDING_FADE_START = FINAL_ENDING_TOTAL_DURATION - 2.8

final_shot_video = None
final_shot_video_error = False
final_shot_video_done = False

# Start the VLC cinematic one frame after the SHOOT click.  This lets
# Pygame finish processing the click and present the transition frame
# before VLC takes ownership of the video output.  It prevents the
# cinematic from appearing only after a mouse/cursor movement.
final_shot_start_pending = False
final_shot_start_delay = 0.08

# =========================================================
# FINAL GAME ENDING VIDEO
# =========================================================
# This is a separate video from final_shot.mp4.
# final_shot.mp4 plays immediately after the best friend is defeated.
# game_ending.mp4 plays only after the survivor "one last look" sequence
# has completely faded to black, with a 1-second black hold first.
GAME_ENDING_VIDEO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ending",
    "game_ending.mp4"
)

game_ending_video = None
game_ending_video_error = None
game_ending_start_pending = False
game_ending_start_delay = 1.0


class FinalShotVideo:
    """Embedded VLC/libVLC player for the final-shot MP4.

    VLC plays the MP4 video and its original embedded audio together.
    The VLC video output is embedded directly into the existing Pygame
    window on Windows, so no separate WAV file is required.
    """

    def __init__(self, path, width, height, window_handle):
        self.path = path
        self.width = width
        self.height = height
        self.window_handle = window_handle

        self.instance = None
        self.player = None
        self.media = None
        self.finished = False
        self.started = False
        self.error = None

    @staticmethod
    def _prepare_vlc():
        """Prepare libVLC for normal Python runs and PyInstaller --onefile."""
        # PyInstaller --onefile extracts bundled files into _MEIPASS.
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = os.path.abspath(sys._MEIPASS)
            plugin_dir = os.path.join(base_dir, "plugins")

            if hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(base_dir)
                except OSError:
                    pass

            old_path = os.environ.get("PATH", "")
            path_parts = old_path.split(os.pathsep) if old_path else []
            if base_dir.lower() not in [part.lower() for part in path_parts]:
                os.environ["PATH"] = base_dir + os.pathsep + old_path

            if os.path.isdir(plugin_dir):
                os.environ["VLC_PLUGIN_PATH"] = plugin_dir

            return base_dir

        # Normal development mode: use the installed desktop VLC.
        candidates = [
            os.path.join(
                os.environ.get("PROGRAMFILES", r"C:\Program Files"),
                "VideoLAN", "VLC"
            ),
            os.path.join(
                os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
                "VideoLAN", "VLC"
            ),
        ]

        for path in candidates:
            if not os.path.isdir(path):
                continue

            if hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(path)
                except OSError:
                    pass

            old_path = os.environ.get("PATH", "")
            path_parts = old_path.split(os.pathsep) if old_path else []
            if path.lower() not in [part.lower() for part in path_parts]:
                os.environ["PATH"] = path + os.pathsep + old_path

            plugin_dir = os.path.join(path, "plugins")
            if os.path.isdir(plugin_dir):
                os.environ["VLC_PLUGIN_PATH"] = plugin_dir

            return path

        return None

    def _refresh_embedded_window(self):
        """Force Windows to repaint the Pygame/VLC host window immediately."""
        if not sys.platform.startswith("win") or not self.window_handle:
            return

        try:
            user32 = ctypes.windll.user32
            hwnd = int(self.window_handle)

            # Invalidate + update the host and all child/embedded video
            # surfaces.  This removes the need for a mouse movement to
            # trigger the first VLC repaint.
            user32.InvalidateRect(hwnd, None, True)
            user32.UpdateWindow(hwnd)

            # Give VLC/Windows one immediate message-pump opportunity.
            user32.RedrawWindow(
                hwnd,
                None,
                None,
                0x0001 | 0x0080 | 0x0100
            )
        except Exception:
            # Repainting is only an optimization; video playback itself
            # must remain independent of this Windows-specific call.
            pass

    def start(self):
        self.stop()
        self.finished = False
        self.started = False
        self.error = None

        if not os.path.isfile(self.path):
            self.error = f"Video not found: {self.path}"
            return False

        if vlc is None:
            self.error = (
                "python-vlc is not installed. Run: "
                "python -m pip install python-vlc"
            )
            return False

        self._prepare_vlc()

        try:
            vlc_args = [
                "--quiet",
                "--no-video-title-show",
                "--no-snapshot-preview",
            ]

            # Explicitly point VLC at the bundled plugin directory.
            plugin_dir = os.environ.get("VLC_PLUGIN_PATH")
            if plugin_dir and os.path.isdir(plugin_dir):
                vlc_args.append("--plugin-path=" + plugin_dir)

            self.instance = vlc.Instance(*vlc_args)

            if self.instance is None:
                self.error = (
                    "VLC/libVLC could not initialize. "
                    "Install the desktop VLC application."
                )
                return False

            self.player = self.instance.media_player_new()
            if self.player is None:
                self.error = "VLC media player could not be created."
                self.stop()
                return False

            self.media = self.instance.media_new(self.path)
            if self.media is None:
                self.error = f"VLC could not load video: {self.path}"
                self.stop()
                return False

            self.player.set_media(self.media)

            if not sys.platform.startswith("win"):
                self.error = "Embedded VLC playback is configured for Windows."
                self.stop()
                return False

            if not self.window_handle:
                self.error = "Could not obtain the Pygame window handle."
                self.stop()
                return False

            # Render VLC directly into the existing Pygame window.
            self.player.set_hwnd(self.window_handle)

            # Use the MP4's own embedded audio stream.
            try:
                self.player.audio_set_mute(False)
                self.player.audio_set_volume(100)
            except Exception:
                pass

            result = self.player.play()
            if result == -1:
                self.error = f"VLC could not start video: {self.path}"
                self.stop()
                return False

            self.started = True

            # VLC has now been attached to the Pygame window.  Explicitly
            # request a repaint so the first frame is visible immediately,
            # without requiring the user to move/click the mouse.
            self._refresh_embedded_window()

            print("FINAL SHOT VIDEO + EMBEDDED AUDIO STARTED")
            return True

        except Exception as exc:
            self.error = f"VLC playback error: {exc}"
            self.stop()
            return False

    def update(self, dt):
        if not self.started or self.finished or self.player is None:
            return

        try:
            state = self.player.get_state()
            if state in (vlc.State.Ended, vlc.State.Error, vlc.State.Stopped):
                self.finished = True
        except Exception as exc:
            self.error = f"VLC state error: {exc}"
            self.finished = True

    def draw(self, screen):
        # VLC owns the video rendering while this scene is active.
        # Do not blit a Pygame frame over the VLC output.
        return

    def stop(self):
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass
            try:
                self.player.release()
            except Exception:
                pass

        if self.media is not None:
            try:
                self.media.release()
            except Exception:
                pass

        if self.instance is not None:
            try:
                self.instance.release()
            except Exception:
                pass

        self.player = None
        self.media = None
        self.instance = None
        self.started = False


class EndingCharacter:
    """Simple cinematic survivor used only by the final campus ending."""

    def __init__(self, name, role, start_x, start_y, target_x, target_y, shirt):
        self.name = name
        self.role = role
        self.start = pygame.Vector2(start_x, start_y)
        self.target = pygame.Vector2(target_x, target_y)
        self.position = self.start.copy()
        self.shirt = shirt

    def update(self, progress):
        progress = max(0.0, min(1.0, progress))
        # Smooth cinematic movement.
        smooth = progress * progress * (3.0 - 2.0 * progress)
        self.position = self.start.lerp(self.target, smooth)

    def draw(self, screen, camera, selected=False):
        x = int(self.position.x - camera.x)
        y = int(self.position.y - camera.y)

        # Shadow
        pygame.draw.ellipse(
            screen,
            (18, 20, 20),
            (x - 18, y + 26, 36, 10)
        )

        # Body
        pygame.draw.rect(
            screen,
            self.shirt,
            (x - 12, y - 4, 24, 30),
            border_radius=5
        )

        # Head
        pygame.draw.circle(
            screen,
            (194, 151, 116),
            (x, y - 16),
            11
        )

        # Hair
        pygame.draw.rect(
            screen,
            (42, 34, 31),
            (x - 9, y - 27, 18, 6),
            border_radius=3
        )

        # Legs
        pygame.draw.rect(
            screen,
            (42, 45, 49),
            (x - 9, y + 24, 7, 15),
            border_radius=2
        )
        pygame.draw.rect(
            screen,
            (42, 45, 49),
            (x + 2, y + 24, 7, 15),
            border_radius=2
        )

        if selected:
            pygame.draw.circle(
                screen,
                (225, 183, 58),
                (x, y - 42),
                3
            )


def build_final_ending_group():
    """Create the hero and the complete survivor group outside the gate."""
    gate = campus.main_gate

    center_x = gate.centerx
    inside_y = gate.bottom - 42
    outside_y = gate.bottom + 105

    # Compact formation so every survivor fits in the final cinematic frame.
    positions = [
        ("Hero", "hero", center_x, inside_y, center_x, outside_y, (55, 105, 155)),
        ("Viveka Mam", "faculty", center_x - 75, inside_y + 5, center_x - 75, outside_y + 5, (70, 125, 205)),
        ("Principal Sir", "faculty", center_x + 75, inside_y + 5, center_x + 75, outside_y + 5, (70, 75, 90)),
        ("Faculty 1", "faculty", center_x - 150, inside_y + 15, center_x - 150, outside_y + 15, (88, 82, 72)),
        ("Faculty 2", "faculty", center_x + 150, inside_y + 15, center_x + 150, outside_y + 15, (92, 76, 70)),
        ("Faculty 3", "faculty", center_x - 225, inside_y + 25, center_x - 225, outside_y + 25, (78, 91, 76)),
        ("Doctor 1", "doctor", center_x + 225, inside_y + 25, center_x + 225, outside_y + 25, (205, 205, 195)),
        ("Doctor 2", "doctor", center_x - 285, inside_y + 38, center_x - 285, outside_y + 38, (185, 195, 205)),
        ("Student 1", "student", center_x + 285, inside_y + 38, center_x + 285, outside_y + 38, (54, 103, 130)),
        ("Student 2", "student", center_x - 345, inside_y + 52, center_x - 345, outside_y + 52, (112, 76, 60)),
        ("Student 3", "student", center_x + 345, inside_y + 52, center_x + 345, outside_y + 52, (72, 102, 70)),
        ("Student 4", "student", center_x, inside_y + 72, center_x, outside_y + 72, (105, 82, 120)),
    ]

    return [
        EndingCharacter(
            name,
            role,
            sx,
            sy,
            tx,
            ty,
            shirt
        )
        for name, role, sx, sy, tx, ty, shirt in positions
    ]


final_ending_group = build_final_ending_group()
final_ending_camera = Camera(
    WIDTH,
    HEIGHT,
    campus.width,
    campus.height
)

# The camera is deliberately kept behind the survivors so the college,
# gate, and the entire group remain visible during the final shot.
FINAL_ENDING_CAMERA_X = max(
    0,
    min(
        campus.main_gate.centerx - WIDTH // 2,
        campus.width - WIDTH
    )
)
FINAL_ENDING_CAMERA_START_Y = 930
FINAL_ENDING_CAMERA_END_Y = 1035
final_ending_camera.x = FINAL_ENDING_CAMERA_X
final_ending_camera.y = FINAL_ENDING_CAMERA_START_Y


def reset_library_level():
    """Reset only the Library level. AI and Mechanical progress are untouched."""
    global library_player_dead
    global library_death_timer
    global library_survivors_visible

    library_chapter.reset()

    player.library_immunity = LIBRARY_MAX_IMMUNITY
    library_player_dead = False
    library_death_timer = 0.0
    library_survivors_visible = False

    set_player_position(
        library_chapter.width // 2 - 20,
        library_chapter.height - 150
    )

    player.direction = "up"
    player.walking = False


def draw_library_survivors(surface):
    # Viveka
    pygame.draw.ellipse(
        surface,
        (8, 8, 10),
        (510, 690, 48, 12)
    )
    pygame.draw.rect(
        surface,
        (70, 125, 205),
        (516, 660, 36, 35),
        border_radius=7
    )
    pygame.draw.circle(
        surface,
        (230, 190, 155),
        (534, 653),
        13
    )
    pygame.draw.rect(
        surface,
        (55, 42, 38),
        (522, 641, 24, 7),
        border_radius=3
    )

    # Three rescued faculty survivors.
    survivor_positions = [
        (610, 660),
        (675, 710),
        (620, 760)
    ]

    for x, y in survivor_positions:
        pygame.draw.ellipse(
            surface,
            (8, 8, 10),
            (x - 5, y + 40, 50, 12)
        )
        pygame.draw.rect(
            surface,
            (75, 80, 88),
            (x, y + 15, 40, 38),
            border_radius=7
        )
        pygame.draw.circle(
            surface,
            (225, 185, 150),
            (x + 20, y + 8),
            15
        )
        pygame.draw.rect(
            surface,
            (45, 38, 35),
            (x + 5, y - 6, 30, 9),
            border_radius=3
        )


def draw_library_story_scene(surface, camera):
    # Keep the story characters in the visible central area.
    draw_library_survivors(surface)

    label_font = pygame.font.Font(None, 22)
    label = label_font.render(
        "Viveka Mam  •  Faculty Survivors",
        True,
        (225, 225, 215)
    )
    surface.blit(
        label,
        (495 - camera.x, 625 - camera.y)
    )



def update_viveka_follow(dt):
    'Keep Viveka following the hero on the campus exterior.'
    if not viveka_following:
        return

    target = pygame.Vector2(
        player.rect.centerx - 60,
        player.rect.centery + 18
    )

    current = pygame.Vector2(
        viveka_campus.rect.center
    )

    delta = target - current

    if delta.length_squared() > 45 ** 2:
        delta.normalize_ip()
        current += delta * viveka_follow_speed * dt

    viveka_campus.rect.center = (
        int(current.x),
        int(current.y)
    )


def set_player_position(x, y):
    'Set both Player coordinates and its collision rectangle.'
    player.x = float(x)
    player.y = float(y)
    player.rect.topleft = (
        int(player.x),
        int(player.y)
    )


def reset_mechanical_scene():
    'Create a fresh Mechanical Block combat instance.'
    global mechanical_combat
    global mechanical_intro_active
    global mechanical_intro_index
    global mechanical_students_dialogue_active
    global mechanical_students_dialogue_index
    global mechanical_combat_started
    global mechanical_checkpoint
    global mechanical_player_dead
    global mechanical_death_message_timer
    global mechanical_respawn_invulnerability

    mechanical_combat = MechanicalCombat(
        mechanical_block
    )
    configure_mechanical_combat()

    mechanical_intro_active = True
    mechanical_intro_index = 0

    mechanical_students_dialogue_active = False
    mechanical_students_dialogue_index = 0

    mechanical_combat_started = False
    mechanical_checkpoint = False

    set_player_position(
        mechanical_block.entry_point[0],
        mechanical_block.entry_point[1]
    )

    player.direction = "right"
    player.walking = False

    viveka_campus.rect.center = (
        player.rect.centerx - 75,
        player.rect.centery + 20
    )


def start_mechanical_combat():
    'Start the Mechanical Block three-stage combat.'
    global mechanical_intro_active
    global mechanical_combat_started

    mechanical_intro_active = False
    mechanical_combat_started = True

    mechanical_combat.start()

    print("MECHANICAL BLOCK COMBAT STARTED")


def finish_mechanical_students_dialogue():
    global mechanical_students_dialogue_active
    global mechanical_students_dialogue_index
    global mechanical_checkpoint
    global mechanical_objective_active
    global library_objective_active
    global story_objective_active
    global objective_active

    mechanical_students_dialogue_active = False
    mechanical_students_dialogue_index = 0
    mechanical_checkpoint = True

    # The Mechanical Block chapter is finished.
    mechanical_objective_active = False

    # IMPORTANT: disable the old opening/AI objective.
    # Otherwise the old "GO TO THE AI BLOCK FOR THE HOD" card
    # remains visible together with the new Library objective.
    story_objective_active = False
    objective_active = False

    # Activate only the next story objective.
    library_objective_active = True

    transition.start_in()
    globals()["scene"] = "TRANSITION_TO_LIBRARY_TRAVEL"

    print("MECHANICAL BLOCK SECURED")
    print("STUDENTS RESCUED")
    print("NEXT OBJECTIVE: SAVE THE FACULTY IN THE LIBRARY")


def set_intro_camera():
    """Keep the opening cinematic framed on the entrance gate."""
    target_x = campus.main_gate.centerx - WIDTH // 2
    target_y = campus.main_gate.centery - HEIGHT // 2

    max_x = max(0, campus.width - WIDTH)
    max_y = max(0, campus.height - HEIGHT)

    campus_camera.x = max(
        0,
        min(target_x, max_x)
    )

    campus_camera.y = max(
        0,
        min(target_y, max_y)
    )


# =========================================================
# MAIN BLOCK — SUSPENSE / PRINCIPAL RESCUE
# =========================================================

MAIN_BLOCK_WIDTH = 1500
MAIN_BLOCK_HEIGHT = 920
MAIN_BLOCK_IMMUNITY = 100

class MainBlockCollision:
    def __init__(self, block):
        self.block = block

    def collides(self, rect):
        if not self.block.bounds.contains(rect):
            return True
        return any(rect.colliderect(obstacle) for obstacle in self.block.obstacles)


class MainBlock:
    """Non-combat suspense area for the Principal chapter."""

    def __init__(self):
        self.width = MAIN_BLOCK_WIDTH
        self.height = MAIN_BLOCK_HEIGHT
        self.entry_point = (110, 760)
        self.bounds = pygame.Rect(45, 45, self.width - 90, self.height - 90)

        # Corridors / offices / reception furniture.
        self.obstacles = [
            pygame.Rect(300, 190, 260, 42),
            pygame.Rect(650, 190, 250, 42),
            pygame.Rect(1000, 190, 250, 42),
            pygame.Rect(300, 480, 260, 42),
            pygame.Rect(650, 480, 250, 42),
            pygame.Rect(1000, 480, 250, 42),
            pygame.Rect(300, 710, 300, 38),
            pygame.Rect(900, 710, 300, 38),
        ]

        self.computer_rect = pygame.Rect(260, 270, 100, 70)
        self.document_rect = pygame.Rect(545, 285, 100, 70)
        self.phone_rect = pygame.Rect(835, 280, 90, 70)
        self.shadow_zone = pygame.Rect(1030, 350, 220, 190)
        self.office_door = pygame.Rect(1240, 570, 150, 18)
        self.principal_pos = (1315, 650)

        # Suspense props.
        self.broken_lights = [
            (220, 115), (520, 115), (820, 115),
            (1120, 115), (1390, 115)
        ]
        self.windows = [
            pygame.Rect(150, 80, 90, 30),
            pygame.Rect(470, 80, 90, 30),
            pygame.Rect(790, 80, 90, 30),
            pygame.Rect(1110, 80, 90, 30)
        ]

    def get_collision_rects(self):
        return self.obstacles

    def draw(self, screen, camera, stage, light_flicker=False, principal_visible=False):
        ox = int(camera.x)
        oy = int(camera.y)
        screen.fill((15, 17, 19))

        floor = pygame.Rect(
            45 - ox, 45 - oy,
            self.width - 90, self.height - 90
        )
        pygame.draw.rect(screen, (31, 32, 34), floor)

        # Long corridor tiles.
        for x in range(70, self.width - 45, 65):
            pygame.draw.line(
                screen, (42, 43, 45),
                (x - ox, 55 - oy),
                (x - ox, self.height - 55 - oy), 1
            )
        for y in range(60, self.height - 45, 65):
            pygame.draw.line(
                screen, (42, 43, 45),
                (50 - ox, y - oy),
                (self.width - 50 - ox, y - oy), 1
            )

        # Dark walls.
        walls = [
            pygame.Rect(45, 45, self.width - 90, 42),
            pygame.Rect(45, self.height - 45, self.width - 90, 42),
            pygame.Rect(45, 45, 42, self.height - 90),
            pygame.Rect(self.width - 87, 45, 42, self.height - 90)
        ]
        for wall in walls:
            pygame.draw.rect(screen, (9, 11, 13), wall.move(-ox, -oy))

        # Windows / emergency glow.
        for index, window in enumerate(self.windows):
            r = window.move(-ox, -oy)
            pygame.draw.rect(screen, (17, 24, 29), r, border_radius=4)
            pygame.draw.rect(screen, (64, 70, 73), r, 2, border_radius=4)
            if index % 2 == 0:
                pygame.draw.rect(screen, (75, 45, 38), r.inflate(-14, -10), border_radius=3)

        # Office furniture / barriers.
        for obstacle in self.obstacles:
            r = obstacle.move(-ox, -oy)
            pygame.draw.rect(screen, (49, 43, 39), r, border_radius=5)
            pygame.draw.rect(screen, (72, 60, 50), r.inflate(-7, -7), border_radius=3)

        # Computer.
        r = self.computer_rect.move(-ox, -oy)
        pygame.draw.rect(screen, (24, 25, 27), r, border_radius=6)
        pygame.draw.rect(screen, (70, 76, 80), r, 2, border_radius=6)
        pygame.draw.rect(screen, (24, 45, 48), (r.x + 12, r.y + 10, 76, 43), border_radius=3)
        if stage >= 1:
            pygame.draw.rect(screen, (125, 48, 43), (r.x + 20, r.y + 18, 60, 4))
            pygame.draw.rect(screen, (165, 75, 62), (r.x + 20, r.y + 29, 45, 3))

        # Document.
        r = self.document_rect.move(-ox, -oy)
        pygame.draw.rect(screen, (205, 198, 175), r, border_radius=3)
        pygame.draw.line(screen, (80, 75, 68), (r.x + 12, r.y + 18), (r.right - 12, r.y + 18), 2)
        pygame.draw.line(screen, (80, 75, 68), (r.x + 12, r.y + 32), (r.right - 25, r.y + 32), 2)
        pygame.draw.line(screen, (80, 75, 68), (r.x + 12, r.y + 46), (r.right - 18, r.y + 46), 2)

        # Phone.
        r = self.phone_rect.move(-ox, -oy)
        pygame.draw.rect(screen, (23, 24, 26), r, border_radius=8)
        pygame.draw.rect(screen, (75, 78, 80), r, 2, border_radius=8)
        pygame.draw.circle(screen, (180, 54, 46), r.center, 9)
        if stage >= 3:
            pygame.draw.circle(screen, (235, 70, 55), r.center, 12, 2)

        # Principal's office door.
        door = self.office_door.move(-ox, -oy)
        pygame.draw.rect(screen, (20, 20, 21), door, border_radius=4)
        pygame.draw.rect(screen, (111, 86, 58), door, 2, border_radius=4)
        label_font = pygame.font.Font(None, 22)
        label = label_font.render("PRINCIPAL", True, (225, 205, 165))
        screen.blit(label, label.get_rect(center=(door.centerx, door.y - 14)))

        # Flickering ceiling lights.
        for i, (x, y) in enumerate(self.broken_lights):
            active = (i + int(pygame.time.get_ticks() / 160)) % 7 not in (0, 1)
            if light_flicker and i == 2:
                active = not active
            pygame.draw.rect(
                screen,
                (72, 74, 74) if active else (28, 29, 30),
                (x - 30 - ox, y - oy, 60, 7),
                border_radius=3
            )

        # Emergency red light near the office.
        pygame.draw.circle(
            screen, (130, 43, 38),
            (1190 - ox, 540 - oy), 8
        )

        # Principal after the office is opened.
        if principal_visible:
            x, y = self.principal_pos
            x -= ox
            y -= oy
            pygame.draw.ellipse(screen, (7, 8, 9), (x - 22, y + 34, 48, 12))
            pygame.draw.rect(screen, (62, 68, 76), (x - 18, y - 2, 36, 42), border_radius=7)
            pygame.draw.circle(screen, (180, 125, 92), (x, y - 13), 15)
            pygame.draw.rect(screen, (42, 40, 39), (x - 14, y - 27, 28, 9), border_radius=4)
            pygame.draw.rect(screen, (70, 45, 42), (x - 3, y + 4, 6, 19))

        # Dark vignette.
        vignette = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 55))
        screen.blit(vignette, (0, 0))


main_block = MainBlock()
main_block_camera = Camera(
    WIDTH,
    HEIGHT,
    main_block.width,
    main_block.height
)
main_block_collision = MainBlockCollision(main_block)

MAIN_BLOCK_ENTRANCE_ZONE = pygame.Rect(
    campus.main_block.left - 110,
    campus.main_block.centery - 85,
    110,
    170
)

main_block_stage = 0
main_block_cinematic_timer = 0.0
main_block_dialogue_index = 0
main_block_dialogue_active = False
main_block_principal_rescued = False
main_block_complete = False
main_block_research_objective_active = False
main_block_phone_done = False
main_block_shadow_seen = False
main_block_lights_seen = False

main_block_dialogue = [
    ("Principal", "You came... I thought nobody would reach me."),
    ("Hero", "Sir, what happened here?"),
    ("Principal", "This outbreak is connected to something hidden beneath the campus."),
    ("Principal", "The strange door in the Library... it leads to a secret Research Department."),
    ("Hero", "Then we have to find out what happened there."),
]


def draw_main_block_dialogue(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 125))
    surface.blit(overlay, (0, 0))

    box = pygame.Rect(100, HEIGHT - 210, WIDTH - 200, 170)
    pygame.draw.rect(surface, (7, 11, 15), box, border_radius=14)
    pygame.draw.rect(surface, (205, 173, 74), box, 2, border_radius=14)

    speaker, line = main_block_dialogue[main_block_dialogue_index]
    speaker_font = pygame.font.Font(None, 30)
    line_font = pygame.font.Font(None, 25)
    hint_font = pygame.font.Font(None, 20)

    surface.blit(
        speaker_font.render(speaker, True, (225, 183, 58)),
        (box.x + 24, box.y + 20)
    )

    words = line.split()
    lines = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if line_font.size(candidate)[0] > box.width - 48:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)

    for i, text in enumerate(lines):
        surface.blit(
            line_font.render(text, True, (240, 240, 235)),
            (box.x + 24, box.y + 62 + i * 30)
        )

    surface.blit(
        hint_font.render("E  CONTINUE", True, (150, 158, 160)),
        (box.right - 125, box.bottom - 30)
    )

# =========================================================
# MAIN LOOP
# =========================================================

running = True

while running:

    dt = clock.tick(FPS) / 1000.0

    # =====================================================
    # EVENTS
    # =====================================================

    events = pygame.event.get()

    for event in events:

        if event.type == pygame.QUIT:
            running = False

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and scene == "GAME_INTRO"
        ):
        # Start immediately from 0:00. VLC supplies the embedded audio.
            if start_game_intro_video():
                scene = "GAME_INTRO_VIDEO"
            else:
                scene = "GAME_INTRO"

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            # =================================================
            # RELOAD
            # =================================================

            if (
                event.key == pygame.K_r
                and not transition.active
                and scene == "MECHANICAL_BLOCK"
                and not mechanical_intro_active
                and not mechanical_students_dialogue_active
            ):
                mechanical_combat.start_reload()

            if (
                event.key == pygame.K_r
                and not transition.active
                and scene == "LIBRARY"
                and library_chapter.started
                and not library_chapter.story_active
                and not library_player_dead
            ):
                library_chapter.start_reload()

            # =================================================
            # VIVEKA MAM INTERACTION
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "AI_BLOCK"
                and combat.combat_complete
                and not transition.active
            ):

                if (
                    not dialogue_active
                    and not rescue_complete
                    and player.near(viveka.rect)
                ):
                    dialogue_active = True
                    dialogue_index = 0

                elif dialogue_active:

                    dialogue_index += 1

                    if dialogue_index >= len(viveka_dialogue):
                        dialogue_active = False
                        rescue_complete = True
                        viveka_spawned = False

                        viveka_following = True
                        mechanical_objective_active = True
                        objective_active = False

                        transition.start_in()
                        scene = "TRANSITION_TO_CAMPUS"

                        print("VIVEKA MAM RESCUED")
                        print("NEXT OBJECTIVE: GO TO THE MECHANICAL BLOCK")

            # =================================================
            # MECHANICAL BLOCK INTERACTION
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "CAMPUS"
                and rescue_complete
                and mechanical_objective_active
                and not transition.active
            ):

                if player.near(MECH_ENTRANCE_ZONE):
                    transition.start_in()
                    scene = "TRANSITION_TO_MECHANICAL"

                    print("ENTERING MECHANICAL BLOCK")


            # =================================================
            # LIBRARY ENTRANCE
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "CAMPUS"
                and (library_objective_active or research_return_objective_active)
                and not transition.active
            ):
                if player.near(library_campus_entrance):
                    transition.start_in()
                    if research_return_objective_active:
                        scene = "TRANSITION_TO_RESEARCH_LIBRARY"
                        print("RETURNING TO LIBRARY FOR HIDDEN DOOR")
                    else:
                        scene = "TRANSITION_TO_LIBRARY"
                        print("ENTERING LIBRARY")

            # =================================================
            # MAIN BLOCK ENTRANCE
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "CAMPUS"
                and library_main_block_objective_active
                and not transition.active
                and player.near(MAIN_BLOCK_ENTRANCE_ZONE)
            ):
                transition.start_in()
                scene = "TRANSITION_TO_MAIN_BLOCK"
                print("ENTERING MAIN BLOCK")

            # =================================================
            # MAIN BLOCK INTERACTIONS
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "MAIN_BLOCK"
                and not transition.active
                and not main_block_dialogue_active
            ):
                if main_block_stage == 0 and player.near(main_block.computer_rect):
                    main_block_stage = 1
                    main_block_cinematic_timer = 0.0
                    play_mainblock_sound(os.path.join("ui", "computer_glitch.wav"), 0.65)
                    play_mainblock_sound(os.path.join("environment", "electrical_spark.wav"), 0.40)
                    print("BIOLOGICAL CONTAINMENT FAILED")

                elif main_block_stage == 1 and player.near(main_block.document_rect):
                    main_block_stage = 2
                    play_mainblock_sound(os.path.join("environment", "electrical_spark.wav"), 0.22)
                    print("DOCUMENT DISCOVERED: PROJECT STATUS / RESEARCH DEPARTMENT")

                elif main_block_stage == 2 and player.near(main_block.phone_rect):
                    main_block_stage = 3
                    main_block_cinematic_timer = 0.0
                    main_block_phone_done = True
                    play_mainblock_sound(os.path.join("environment", "old_phone_ring.wav"), 0.70)
                    print("PHONE MESSAGE: HELP... MAIN OFFICE...")

                elif main_block_stage >= 4 and player.near(main_block.office_door):
                    main_block_stage = 5
                    main_block_dialogue_active = True
                    main_block_dialogue_index = 0
                    player.walking = False
                    play_mainblock_sound(os.path.join("environment", "door_slam.wav"), 0.75)
                    print("PRINCIPAL FOUND")

            if (
                event.key == pygame.K_e
                and scene == "MAIN_BLOCK"
                and main_block_dialogue_active
                and not transition.active
            ):
                main_block_dialogue_index += 1
                if main_block_dialogue_index >= len(main_block_dialogue):
                    main_block_dialogue_active = False
                    main_block_principal_rescued = True
                    main_block_complete = True
                    main_block_research_objective_active = True
                    library_main_block_objective_active = False
                    research_return_objective_active = True
                    stop_mainblock_ambient()

                    # The final E press that closes the Principal's dialogue
                    # must also leave the Main Block immediately. The player
                    # no longer needs to walk to the exit and press E again.
                    transition.start_in()
                    scene = "TRANSITION_MAIN_TO_CAMPUS"

                    print("PRINCIPAL RESCUED")
                    print("MAIN BLOCK CHAPTER COMPLETE")
                    print("LEAVING MAIN BLOCK")
                    print("OBJECTIVE: RETURN TO THE LIBRARY")

            # =================================================
            # RETURNED LIBRARY / HIDDEN DOOR
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "RESEARCH_LIBRARY"
                and not transition.active
            ):
                hidden_door = library_chapter.door_rect()
                if player.near(hidden_door):
                    transition.start_in()
                    scene = "TRANSITION_TO_RESEARCH_ELEVATOR"
                    print("HIDDEN DOOR OPENED")
                    print("ENTERING RESEARCH ELEVATOR")

            # =================================================
            # LIBRARY STORY DIALOGUE
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "LIBRARY"
                and library_chapter.story_active
                and not transition.active
            ):
                library_chapter.advance_story()

                if library_chapter.story_complete:
                    library_objective_active = False
                    library_main_block_objective_active = True

                    # Return to the campus after the final Library dialogue.
                    transition.start_in()
                    scene = "TRANSITION_FROM_LIBRARY"

                    print("LIBRARY CHAPTER COMPLETE")
                    print("NEXT OBJECTIVE: GO TO THE MAIN BLOCK")

            # =================================================
            # LIBRARY RETRY
            # =================================================

            if (
                event.key == pygame.K_RETURN
                and scene == "LIBRARY"
                and library_player_dead
                and not transition.active
            ):
                reset_library_level()
                print("LIBRARY RETRY")
                print("OBJECTIVE: KILL ALL 25 INFECTED")

            # =================================================
            # RESEARCH DEPARTMENT RELOAD
            # =================================================

            if (
                event.key == pygame.K_r
                and scene == "RESEARCH_DEPARTMENT"
                and not transition.active
                and not research_department.dialogue_active
                and not research_department.player_dead
            ):
                research_department.start_reload()

            # =================================================
            # RESEARCH DEPARTMENT INTERACTION / DIALOGUE
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "RESEARCH_DEPARTMENT"
                and not transition.active
                and not research_department.player_dead
            ):
                if research_department.dialogue_active:
                    research_department.advance_dialogue()
                else:
                    research_department.interact_doctor(player)
                    if research_department.complete:
                        research_department_complete = True
                        player.final_immunity = 100
                        final_boss = FinalBoss(1350, 550)
                        final_battle_dialogue = FinalBattleDialogue()
                        best_friend_intro_timer = 0.0
                        transition.start_in()
                        scene = "TRANSITION_TO_BEST_FRIEND_REVEAL"
                        print("RESEARCH TEAM RESCUED")
                        print("NO CURE REVEAL STARTING")

            # =================================================
            # BEST FRIEND REVELATION
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "BEST_FRIEND_REVEAL"
                and not transition.active
                and final_battle_dialogue.active
            ):
                final_battle_dialogue.advance()

                if not final_battle_dialogue.active:
                    transition.start_in()
                    scene = "TRANSITION_TO_FINAL_BOSS"
                    print("BEST FRIEND REVEALED")
                    print("FINAL BATTLE STARTING")

                continue

            # =================================================
            # FINAL BOSS RELOAD
            # =================================================

            if (
                event.key == pygame.K_r
                and scene == "FINAL_BOSS"
                and not transition.active
                and not final_battle_reloading
            ):
                if final_battle_ammo < FINAL_BATTLE_MAGAZINE:
                    final_battle_reloading = True
                    final_battle_reload_timer = 0.0

                continue

            # =================================================
            # FINAL SHOT VIDEO ERROR / RETURN
            # =================================================

            if (
                event.key == pygame.K_RETURN
                and scene == "FINAL_SHOT_VIDEO"
                and final_shot_video is not None
                and final_shot_video.error
            ):
                final_shot_video.stop()
                final_shot_video = None
                final_shot_start_pending = False
                final_shot_start_delay = 0.0
                scene = "FINAL_SHOT_PROMPT"
                continue

            # =================================================
            # FINAL SHOT BUTTON / VIDEO START
            # =================================================
            # The final cinematic starts ONLY from the on-screen
            # SHOOT button. ENTER is intentionally not used here.

            # =================================================
            # RESEARCH DEPARTMENT RETRY
            # =================================================

            if (
                event.key == pygame.K_RETURN
                and scene == "RESEARCH_DEPARTMENT"
                and research_department.player_dead
                and not transition.active
            ):
                research_department.reset(player)
                print("RESEARCH DEPARTMENT RETRY")
                print("OBJECTIVE: KILL THE INFECTED DOCTOR")

            # =================================================
            # MECHANICAL GAME OVER / RETRY
            # =================================================

            if (
                event.key == pygame.K_RETURN
                and scene == "MECHANICAL_BLOCK"
                and mechanical_player_dead
                and not transition.active
            ):
                reset_mechanical_scene()

                print("MECHANICAL BLOCK RETRY")
                print("STAGE 1 STARTED")

            # =================================================
            # MECHANICAL INTRO / STAGE PROGRESSION
            # =================================================

            if (
                event.key == pygame.K_e
                and scene == "MECHANICAL_BLOCK"
                and not transition.active
                and not mechanical_player_dead
            ):

                if mechanical_intro_active:

                    mechanical_intro_index += 1

                    if (
                        mechanical_intro_index
                        >= len(mechanical_intro)
                    ):
                        start_mechanical_combat()

                elif (
                    mechanical_combat_started
                    and mechanical_combat.stage_complete
                    and not mechanical_combat.chapter_complete
                    and not mechanical_students_dialogue_active
                ):

                    mechanical_combat.next_stage()

                    print(
                        f"MECHANICAL STAGE "
                        f"{mechanical_combat.stage} STARTED"
                    )

                elif (
                    mechanical_combat.chapter_complete
                    and mechanical_students_dialogue_active
                ):

                    mechanical_students_dialogue_index += 1

                    if (
                        mechanical_students_dialogue_index
                        >= len(mechanical_students_dialogue)
                    ):
                        finish_mechanical_students_dialogue()

        # =================================================
        # FINAL SHOT BUTTON CLICK
        # =================================================

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and scene == "FINAL_SHOT_PROMPT"
        ):
            if final_shot_button.collidepoint(event.pos):
                # Do not initialize VLC inside the mouse event itself.
                # Queue it for the next update cycle so Pygame can finish
                # handling the click and present the transition cleanly.
                final_shot_video = FinalShotVideo(
                    FINAL_SHOT_VIDEO_PATH,
                    WIDTH,
                    HEIGHT,
                    pygame_window_handle
                )

                final_shot_start_pending = True
                final_shot_start_delay = 0.08
                scene = "FINAL_SHOT_VIDEO"
                print("FINAL SHOT VIDEO QUEUED")

        # =================================================
        # AI BLOCK SHOOTING
        # =================================================

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and scene == "AI_BLOCK"
            and not transition.active
            and ai_intro_timer >= AI_INTRO_DURATION
            and not dialogue_active
            and not rescue_complete
        ):
            world_mouse_x = (
                event.pos[0] + ai_camera.x
            )

            world_mouse_y = (
                event.pos[1] + ai_camera.y
            )

            combat.shoot(
                player,
                world_mouse_x,
                world_mouse_y
            )


        # =================================================
        # LIBRARY SHOOTING
        # =================================================

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and scene == "LIBRARY"
            and not transition.active
            and library_chapter.started
            and not library_chapter.story_active
            and not library_player_dead
            and library_chapter.cinematic_state == "COMBAT"
        ):
            world_mouse_x = (
                event.pos[0] + library_chapter.camera.x
            )
            world_mouse_y = (
                event.pos[1] + library_chapter.camera.y
            )

            library_chapter.shoot(
                player,
                world_mouse_x,
                world_mouse_y
            )

        # =================================================
        # RESEARCH DEPARTMENT SHOOTING
        # =================================================

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and scene == "RESEARCH_DEPARTMENT"
            and not transition.active
            and not research_department.dialogue_active
            and not research_department.player_dead
            and not research_department.complete
        ):
            world_mouse_x = event.pos[0] + research_department.camera.x
            world_mouse_y = event.pos[1] + research_department.camera.y
            research_department.shoot(
                player,
                world_mouse_x,
                world_mouse_y
            )

        # =================================================
        # FINAL BOSS SHOOTING
        # =================================================

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and scene == "FINAL_BOSS"
            and not transition.active
            and not final_battle_reloading
            and final_battle_ammo > 0
        ):
            world_mouse_x = (
                event.pos[0] + final_battle_camera.x
            )
            world_mouse_y = (
                event.pos[1] + final_battle_camera.y
            )

            bullet = Bullet(
                player.rect.centerx,
                player.rect.centery,
                world_mouse_x,
                world_mouse_y
            )

            final_battle_bullets.append(bullet)
            final_battle_ammo -= 1

        # =================================================
        # MECHANICAL SHOOTING
        # =================================================

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and scene == "MECHANICAL_BLOCK"
            and not transition.active
            and mechanical_combat_started
            and not mechanical_intro_active
            and not mechanical_students_dialogue_active
            and not mechanical_combat.chapter_complete
        ):
            world_mouse_x = (
                event.pos[0] + mechanical_camera.x
            )

            world_mouse_y = (
                event.pos[1] + mechanical_camera.y
            )

            mechanical_combat.shoot(
                player,
                world_mouse_x,
                world_mouse_y
            )


    # =====================================================
    # GAME START INTRO VIDEO
    # =====================================================

    if scene == "GAME_INTRO":
        # First frame remains visible and the game is not started yet.
        pass

    elif scene == "GAME_INTRO_VIDEO":
        if game_intro_video is None:
            if not start_game_intro_video():
                scene = "GAME_INTRO"
        elif game_intro_video.error:
            game_intro_error = game_intro_video.error
        elif game_intro_video.started:
            game_intro_video.update(dt)
            if game_intro_video.finished:
                game_intro_video.stop()
                game_intro_video = None
                game_intro_error = None
                # Start the existing game opening exactly where it used to start.
                scene = "INTRO_BUS"
                intro_timer = 0.0

    # =====================================================
    # OPENING INTRO
    # =====================================================

    if scene == "INTRO_BUS":

        intro_timer += dt

        # Bus approaches the entrance.
        progress = min(
            intro_timer / INTRO_BUS_DURATION,
            1.0
        )

        # Smooth ease-out.
        eased = 1.0 - (1.0 - progress) ** 3

        bus_x = (
            campus.main_gate.centerx - 650
            + (
                bus_target_x
                - (campus.main_gate.centerx - 650)
            ) * eased
        )

        # Hero remains hidden inside the bus.
        player.x = bus_x + 105
        player.y = bus_y + 20
        player.rect.topleft = (
            int(player.x),
            int(player.y)
        )

        set_intro_camera()

        if intro_timer >= INTRO_BUS_DURATION:
            intro_timer = 0.0
            scene = "INTRO_EXIT"


    elif scene == "INTRO_EXIT":

        intro_timer += dt

        # Bus has stopped. Hero walks out of the bus toward
        # the entrance position.
        progress = min(
            intro_timer / INTRO_EXIT_DURATION,
            1.0
        )

        start_x = bus_target_x + 105
        start_y = bus_y + 20

        player.x = start_x + (
            hero_intro_x - start_x
        ) * progress

        player.y = start_y + (
            hero_intro_y - start_y
        ) * progress

        player.rect.topleft = (
            int(player.x),
            int(player.y)
        )

        player.direction = "down"
        player.walking = True

        set_intro_camera()

        if intro_timer >= INTRO_EXIT_DURATION:
            intro_timer = 0.0
            player.walking = False
            scene = "INTRO_REVEAL"


    elif scene == "INTRO_REVEAL":

        intro_timer += dt

        player.x = hero_intro_x
        player.y = hero_intro_y

        player.rect.topleft = (
            int(player.x),
            int(player.y)
        )

        player.walking = False
        player.direction = "down"

        # The bus pulls away after dropping the hero.
        leave_progress = min(
            intro_timer / INTRO_REVEAL_DURATION,
            1.0
        )

        bus_x = (
            bus_target_x
            + leave_progress * 700
        )

        set_intro_camera()

        if intro_timer >= INTRO_REVEAL_DURATION:
            intro_timer = 0.0
            bus_x = bus_target_x + 700
            intro_dialogue_index = 0
            intro_dialogue_active = True
            scene = "INTRO_DIALOGUE"


    # =====================================================
    # CINEMATIC STORY DIALOGUE
    # =====================================================

    elif scene == "INTRO_DIALOGUE":

        set_intro_camera()

        player.walking = False
        player.direction = "down"

        for event in events:

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_e
            ):

                intro_dialogue_index += 1

                if intro_dialogue_index >= len(intro_dialogue):
                    intro_dialogue_active = False
                    objective_active = False
                    story_objective_active = True
                    tutorial_stage = 0
                    scene = "CAMPUS"

        # No movement during cinematic dialogue.

    # =====================================================
    # CAMPUS
    # =====================================================

    elif scene == "CAMPUS":
        transition.update(dt)

        if not transition.active:

            if not ai_interaction.entering:
                player.update(
                    dt,
                    campus.width,
                    campus.height,
                    collision
                )

            # -------------------------------------------------
            # GUN PICKUP
            # -------------------------------------------------

            if (
                not gun_picked
                and player.rect.colliderect(
                    gun_rect.inflate(55, 55)
                )
            ):
                for event in events:

                    if (
                        event.type == pygame.KEYDOWN
                        and event.key == pygame.K_e
                    ):
                        gun_picked = True
                        tutorial_stage = 1
                        objective_active = True
                        story_objective_active = False

                        print("GUN PICKED UP")
                        print(
                            "OBJECTIVE: GO TO THE AI BLOCK FOR THE HOD"
                        )

            # -------------------------------------------------
            # AI BLOCK ENTRANCE
            # -------------------------------------------------

            entered_ai = False

            if not rescue_complete:
                entered_ai = ai_interaction.update(
                    player,
                    events,
                    dt
                )
            else:
                ai_interaction.active = False

            # Let the AI entry cinematic finish before changing scenes.
            if entered_ai:
                ai_entry_pending = True

            campus_camera.update(
                player
            )

            if (
                ai_entry_pending
                and not ai_interaction.entering
                and not transition.active
            ):
                ai_entry_pending = False
                transition.start_in()
                scene = "TRANSITION_TO_AI"

                ai_interaction.active = False

    # =====================================================
    # TRANSITION TO AI
    # =====================================================

    elif scene == "TRANSITION_TO_AI":

        transition.update(dt)

        if (
            not transition.active
            and transition.mode == "IN"
        ):

            set_player_position(
                ai_block.entry_point[0],
                ai_block.entry_point[1]
            )

            player.direction = "right"
            player.walking = False

            ai_camera.update(player)

            ai_intro_timer = 0.0

            scene = "AI_BLOCK"

            ai_entry_pending = False
            transition.start_out()

    # =====================================================
    # AI BLOCK
    # =====================================================

    elif scene == "AI_BLOCK":

        transition.update(dt)

        if not transition.active:

            player.update(
                dt,
                ai_block.width,
                ai_block.height,
                None
            )

            ai_camera.update(player)

            if not rescue_complete:

                ai_intro_timer += dt

                if (
                    ai_intro_timer >= AI_INTRO_DURATION
                    and not combat.wave_started
                ):
                    combat.start()

                combat.update(
                    player,
                    dt,
                    ai_block.player_bounds
                )

                if (
                    combat.combat_complete
                    and not viveka_spawned
                ):

                    viveka.x = min(
                        player.x + 170,
                        ai_block.width
                        - viveka.width
                        - 40
                    )

                    viveka.y = min(
                        max(player.y, 100),
                        ai_block.height
                        - viveka.height
                        - 40
                    )

                    viveka.rect.topleft = (
                        int(viveka.x),
                        int(viveka.y)
                    )

                    viveka_spawned = True

    # =====================================================
    # RETURN TO CAMPUS
    # =====================================================

    elif scene == "TRANSITION_TO_CAMPUS":

        transition.update(dt)

        if (
            not transition.active
            and transition.mode == "IN"
        ):

            return_x = (
                campus.ai_entrance.left
                - player.width
                - 25
            )

            return_y = (
                campus.ai_entrance.centery
                - player.height // 2
            )

            set_player_position(
                return_x,
                return_y
            )

            player.direction = "up"
            player.walking = False

            viveka_campus.rect.center = (
                player.rect.centerx - 75,
                player.rect.centery + 20
            )

            campus_camera.update(player)

            scene = "CAMPUS_RETURN"

            transition.start_out()

    # =====================================================
    # CAMPUS RETURN
    # =====================================================

    elif scene == "CAMPUS_RETURN":

        transition.update(dt)

        if not transition.active:

            update_viveka_follow(dt)
            campus_camera.update(player)

            scene = "CAMPUS"


    # =====================================================
    # TRANSITION TO LIBRARY TRAVEL
    # =====================================================

    elif scene == "TRANSITION_TO_LIBRARY_TRAVEL":

        transition.update(dt)

        if (
            not transition.active
            and transition.mode == "IN"
        ):
            # Return to the campus at the outside of the Mechanical Block.
            return_x = (
                campus.mech_block.left
                - player.width
                - 25
            )
            return_y = (
                campus.mech_block.centery
                - player.height // 2
            )

            set_player_position(
                return_x,
                return_y
            )

            player.direction = "right"
            player.walking = False

            campus_camera.update(player)

            scene = "CAMPUS"

            transition.start_out()

            print("MECHANICAL BLOCK EXIT")
            print("OBJECTIVE: SAVE THE FACULTY IN THE LIBRARY")

    # =====================================================
    # TRANSITION TO LIBRARY
    # =====================================================

    elif scene == "TRANSITION_TO_LIBRARY":

        transition.update(dt)

        if (
            not transition.active
            and transition.mode == "IN"
        ):
            reset_library_level()

            # The Library has its own camera and interior map.
            library_chapter.camera.update(player)

            scene = "LIBRARY"

            transition.start_out()

            print("LIBRARY LEVEL STARTED")
            print("OBJECTIVE: KILL ALL 25 INFECTED")

    # =====================================================
    # LIBRARY
    # =====================================================

    elif scene == "LIBRARY":

        transition.update(dt)

        if not transition.active:

            # Player movement is enabled only during combat.
            # Freeze the Hero during both post-combat cinematics.
            if (
                not library_player_dead
                and library_chapter.cinematic_state == "COMBAT"
            ):
                player.update(
                    dt,
                    library_chapter.width,
                    library_chapter.height,
                    library_chapter.collision
                )

            if library_chapter.cinematic_state == "DOOR_OBSERVE":
                library_chapter.focus_camera_on_door()
            elif library_chapter.cinematic_state == "STORY":
                library_chapter.focus_camera_on_story()
            else:
                library_chapter.camera.update(player)

            if (
                library_chapter.started
                and not library_player_dead
            ):
                player.library_immunity = max(
                    0,
                    getattr(
                        player,
                        "library_immunity",
                        LIBRARY_MAX_IMMUNITY
                    )
                )

                library_chapter.update(
                    player,
                    dt
                )

                # Hero death immediately resets the single Library level.
                if player.library_immunity <= 0:
                    library_player_dead = True
                    library_death_timer = 0.0
                    library_chapter.player_dead = True
                    library_chapter.bullets.clear()
                    library_chapter.zombies.clear()
                    print("HERO DEFEATED - LIBRARY LEVEL FAILED")
                    print("PRESS ENTER TO RETRY LIBRARY")

            # Story characters appear only after the 4-second door observation.
            if library_chapter.story_active:
                library_survivors_visible = True

    # =====================================================
    # LEAVE MAIN BLOCK -> CAMPUS
    # =====================================================

    elif scene == "TRANSITION_MAIN_TO_CAMPUS":
        transition.update(dt)

        if not transition.active and transition.mode == "IN":
            set_player_position(
                campus.main_block.right + 40,
                campus.main_block.centery - player.height // 2
            )
            player.direction = "left"
            player.walking = False
            campus_camera.update(player)
            scene = "CAMPUS"
            transition.start_out()
            print("MAIN BLOCK EXIT")
            print("OBJECTIVE: RETURN TO THE LIBRARY")

    # =====================================================
    # TRANSITION TO MAIN BLOCK
    # =====================================================

    elif scene == "TRANSITION_TO_MAIN_BLOCK":
        transition.update(dt)

        if (
            not transition.active
            and transition.mode == "IN"
        ):
            set_player_position(
                main_block.entry_point[0],
                main_block.entry_point[1]
            )
            player.direction = "up"
            player.walking = False
            main_block_stage = 0
            main_block_cinematic_timer = 0.0
            main_block_dialogue_active = False
            main_block_principal_rescued = False
            main_block_complete = False
            main_block_research_objective_active = False
            main_block_phone_done = False
            main_block_shadow_seen = False
            main_block_lights_seen = False
            main_block_camera.update(player)
            scene = "MAIN_BLOCK"
            transition.start_out()
            start_mainblock_ambient()
            print("MAIN BLOCK ENTERED")
            print("OBJECTIVE: FIND THE PRINCIPAL")

    # =====================================================
    # MAIN BLOCK — SUSPENSE EXPLORATION
    # =====================================================

    elif scene == "MAIN_BLOCK":
        transition.update(dt)

        if not transition.active:
            if main_block_dialogue_active:
                player.walking = False
            elif not (main_block_stage == 1 and main_block_cinematic_timer < 3.0):
                player.update(
                    dt,
                    main_block.width,
                    main_block.height,
                    main_block_collision
                )

            if main_block_stage == 1:
                main_block_cinematic_timer += dt
                if main_block_cinematic_timer >= 3.0:
                    main_block_cinematic_timer = 3.0

            # First approach: the entrance corridor feels wrong before
            # the player finds any combat.
            if (
                main_block_stage == 0
                and player.rect.centerx > 170
                and not main_block_lights_seen
            ):
                main_block_lights_seen = True
                main_block_cinematic_timer = 0.0
                play_mainblock_sound(os.path.join("environment", "light_flicker.wav"), 0.60)
                play_mainblock_sound(os.path.join("environment", "electrical_spark.wav"), 0.25)
                print("MAIN BLOCK LIGHTS FLICKER")

            # After the phone message, show the unexplained corridor shadow.
            if main_block_stage == 3:
                main_block_cinematic_timer += dt
                player.walking = False
                if main_block_cinematic_timer >= 2.5:
                    main_block_stage = 4
                    main_block_shadow_seen = True
                    main_block_cinematic_timer = 0.0
                    player.walking = True
                    play_mainblock_sound(os.path.join("environment", "door_slam.wav"), 0.72)
                    print("UNKNOWN SHADOW SEEN")

            main_block_camera.update(player)

    # =====================================================
    # RETURN FROM LIBRARY TO CAMPUS
    # =====================================================

    elif scene == "TRANSITION_FROM_LIBRARY":

        transition.update(dt)

        if (
            not transition.active
            and transition.mode == "IN"
        ):
            return_x = (
                campus.library.left
                - player.width
                - 25
            )
            return_y = (
                campus.library.centery
                - player.height // 2
            )

            set_player_position(
                return_x,
                return_y
            )

            player.direction = "right"
            player.walking = False

            campus_camera.update(player)

            scene = "CAMPUS"

            transition.start_out()

            print("RETURNED TO CAMPUS")
            print("OBJECTIVE: GO TO THE MAIN BLOCK")

    # =====================================================
    # RETURN TO LIBRARY FOR HIDDEN DOOR
    # =====================================================

    elif scene == "TRANSITION_TO_RESEARCH_LIBRARY":
        transition.update(dt)

        if not transition.active and transition.mode == "IN":
            library_chapter.reset()
            library_chapter.rack_fallen = True
            library_chapter.hidden_door_revealed = True
            library_chapter.combat_complete = True
            library_chapter.story_complete = True
            library_chapter.cinematic_state = "COMPLETE"
            library_chapter.started = True
            set_player_position(
                library_chapter.door_rect().centerx - player.width // 2,
                library_chapter.door_rect().bottom + 120
            )
            player.direction = "up"
            player.walking = False
            library_chapter.camera.update(player)
            scene = "RESEARCH_LIBRARY"
            transition.start_out()
            print("LIBRARY RETURNED")
            print("OBJECTIVE: ENTER THE HIDDEN DOOR")

    # =====================================================
    # RETURNED LIBRARY / HIDDEN DOOR
    # =====================================================

    elif scene == "RESEARCH_LIBRARY":
        transition.update(dt)

        if not transition.active:
            player.update(
                dt,
                library_chapter.width,
                library_chapter.height,
                library_chapter.collision
            )
            library_chapter.camera.update(player)

    # =====================================================
    # HIDDEN DOOR -> ELEVATOR
    # =====================================================

    elif scene == "TRANSITION_TO_RESEARCH_ELEVATOR":
        transition.update(dt)

        if not transition.active and transition.mode == "IN":
            research_elevator_timer = 0.0
            research_elevator_started = True
            scene = "RESEARCH_ELEVATOR"
            transition.start_out()
            print("RESEARCH ELEVATOR STARTED")

    # =====================================================
    # RESEARCH ELEVATOR CINEMATIC
    # =====================================================

    elif scene == "RESEARCH_ELEVATOR":
        transition.update(dt)
        if not transition.active:
            research_elevator_timer += dt
            if research_elevator_timer >= 4.8:
                transition.start_in()
                scene = "TRANSITION_TO_RESEARCH_DEPARTMENT"

    # =====================================================
    # ELEVATOR -> RESEARCH DEPARTMENT
    # =====================================================

    elif scene == "TRANSITION_TO_RESEARCH_DEPARTMENT":
        transition.update(dt)

        if not transition.active and transition.mode == "IN":
            research_department.reset(player)
            set_player_position(
                research_department.entry_point[0],
                research_department.entry_point[1]
            )
            research_department.camera.update(player)
            scene = "RESEARCH_DEPARTMENT"
            transition.start_out()
            print("RESEARCH DEPARTMENT ENTERED")
            print("OBJECTIVE: KILL THE INFECTED DOCTOR")

    # =====================================================
    # RESEARCH DEPARTMENT
    # =====================================================

    elif scene == "RESEARCH_DEPARTMENT":
        transition.update(dt)

        if not transition.active:
            if not research_department.dialogue_active and not research_department.player_dead and not research_department.complete:
                player.update(
                    dt,
                    research_department.width,
                    research_department.height,
                    research_department_player_collision
                )

            player.research_immunity = max(
                0,
                getattr(player, "research_immunity", 100)
            )
            research_department.immunity = player.research_immunity
            research_department.update(player, dt)
            research_department.camera.update(player)

            if player.research_immunity <= 0 and not research_department.player_dead:
                research_department.player_dead = True
                research_department.bullets.clear()
                research_department.doctor_zombie = None
                player.walking = False
                print("HERO DEFEATED - RESEARCH LEVEL FAILED")
                print("PRESS ENTER TO RETRY RESEARCH DEPARTMENT")

    # =====================================================
    # TRANSITION TO BEST FRIEND REVEAL
    # =====================================================

    elif scene == "TRANSITION_TO_BEST_FRIEND_REVEAL":
        transition.update(dt)

        if (
            not transition.active
            and transition.mode == "IN"
        ):
            final_battle_dialogue = FinalBattleDialogue()
            scene = "BEST_FRIEND_REVEAL"
            transition.start_out()
            print("BEST FRIEND REVELATION")

    # =====================================================
    # BEST FRIEND REVEAL
    # =====================================================

    elif scene == "BEST_FRIEND_REVEAL":
        transition.update(dt)

        if not transition.active:
            final_battle_dialogue.active = True

    # =====================================================
    # TRANSITION TO FINAL BOSS
    # =====================================================

    elif scene == "TRANSITION_TO_FINAL_BOSS":
        transition.update(dt)

        if (
            not transition.active
            and transition.mode == "IN"
        ):
            final_boss = FinalBoss(1350, 550)
            final_battle_ammo = FINAL_BATTLE_MAGAZINE
            final_battle_reloading = False
            final_battle_reload_timer = 0.0
            player.final_immunity = 100
            set_player_position(550, 550)
            final_battle_camera.update(player)
            best_friend_intro_timer = 0.0
            scene = "FINAL_BOSS_INTRO"
            transition.start_out()
            print("FINAL BOSS INTRO")

    # =====================================================
    # FINAL BOSS INTRO
    # =====================================================

    elif scene == "FINAL_BOSS_INTRO":
        transition.update(dt)

        if not transition.active:
            best_friend_intro_timer += dt

            if best_friend_intro_timer >= best_friend_intro_duration:
                scene = "FINAL_BOSS"
                print("FINAL BATTLE: BEST FRIEND")

    # =====================================================
    # FINAL BOSS
    # =====================================================

    elif scene == "FINAL_BOSS":
        transition.update(dt)

        if not transition.active:
            if final_battle_reloading:
                final_battle_reload_timer += dt

                if final_battle_reload_timer >= FINAL_BATTLE_RELOAD_TIME:
                    final_battle_reloading = False
                    final_battle_reload_timer = 0.0
                    final_battle_ammo = FINAL_BATTLE_MAGAZINE

            if not final_battle_reloading:
                player.update(
                    dt,
                    1800,
                    1100,
                    final_battle_collision
                )

            player.final_immunity = max(
                0,
                getattr(player, "final_immunity", 100)
            )

            final_boss.update(
                player,
                dt,
                1800,
                1100
            )

            # Player bullets hit the final boss.
            for bullet in final_battle_bullets:
                bullet.update(dt)

                if (
                    bullet.alive()
                    and final_boss.alive
                ):
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

                    if bullet_rect.colliderect(
                        final_boss.rect
                    ):
                        final_boss.take_damage(1)
                        bullet.life = 0

            final_battle_bullets = [
                bullet
                for bullet in final_battle_bullets
                if bullet.alive()
            ]

            final_battle_camera.update(player)

            if player.final_immunity <= 0:
                player.final_immunity = 0
                final_battle_bullets.clear()
                player.walking = False
                final_boss = FinalBoss(1350, 550)
                final_battle_ammo = FINAL_BATTLE_MAGAZINE
                final_battle_reloading = False
                final_battle_reload_timer = 0.0
                set_player_position(550, 550)
                player.final_immunity = 100
                print("FINAL BATTLE RETRY")

            elif not final_boss.alive:
                # Do not end the game immediately. The player must explicitly
                # perform the final shot of the infected best friend.
                final_battle_bullets.clear()
                final_battle_reloading = False
                final_battle_reload_timer = 0.0
                player.walking = False
                scene = "FINAL_SHOT_PROMPT"
                print("BEST FRIEND DEFEATED")
                print("FINAL SHOT REQUIRED")

    # =====================================================
    # FINAL SHOT PROMPT
    # =====================================================

    elif scene == "FINAL_SHOT_PROMPT":
        # Freeze gameplay completely while the player decides to perform
        # the final shot.
        player.walking = False

    # =====================================================
    # FINAL SHOT VIDEO
    # =====================================================

    elif scene == "FINAL_SHOT_VIDEO":
        if final_shot_video is None:
            final_shot_video = FinalShotVideo(
                FINAL_SHOT_VIDEO_PATH,
                WIDTH,
                HEIGHT,
                pygame_window_handle
            )
            final_shot_start_pending = True
            final_shot_start_delay = 0.08

        # Start VLC slightly after the click.  The short delay is intentional:
        # it gives Windows/Pygame time to repaint the window before VLC starts
        # rendering into it.  This fixes the "video appears only after moving
        # the cursor" behavior.
        if final_shot_start_pending:
            final_shot_start_delay -= dt

            if final_shot_start_delay <= 0.0:
                final_shot_start_pending = False

                if final_shot_video.start():
                    print("FINAL SHOT VIDEO STARTED")
                else:
                    print(
                        "FINAL SHOT VIDEO ERROR:",
                        final_shot_video.error
                    )

        if final_shot_video.error:
            # Keep the error panel stable. ENTER can return to the
            # SHOOT prompt using the existing event handler.
            pass
        elif final_shot_video.started:
            final_shot_video.update(dt)

            if final_shot_video.finished:
                # Release VLC completely before Pygame renders the next scene.
                # Windows can otherwise briefly leave the VLC surface visible
                # as a blank/white rectangle.
                final_shot_video.stop()
                final_shot_video = None
                final_shot_start_pending = False
                final_shot_start_delay = 0.0
                final_shot_video_done = True

                # Force one clean black Pygame frame after VLC releases the
                # window, preventing a white/blank VLC surface between scenes.
                screen.fill((0, 0, 0))
                pygame.display.flip()
                pygame.event.pump()

                # Continue into the already-built survivor/campus ending.
                final_ending_timer = 0.0
                final_ending_finished = False
                final_ending_fade_alpha = 0
                final_ending_group = build_final_ending_group()
                final_ending_camera.x = FINAL_ENDING_CAMERA_X
                final_ending_camera.y = FINAL_ENDING_CAMERA_START_Y
                scene = "FINAL_ENDING"

                print("FINAL SHOT VIDEO + AUDIO COMPLETE")
                print("SURVIVORS MOVING TO MAIN GATE")

    # =====================================================
    # FINAL CAMPUS ENDING
    # =====================================================

    elif scene == "FINAL_ENDING":
        final_ending_timer += dt

        walk_progress = min(
            1.0,
            final_ending_timer / FINAL_ENDING_WALK_DURATION
        )

        for character in final_ending_group:
            character.update(walk_progress)

        # Slowly move the camera toward the final outside-the-gate framing.
        camera_progress = min(1.0, final_ending_timer / 4.5)
        final_ending_camera.y = (
            FINAL_ENDING_CAMERA_START_Y
            + (
                FINAL_ENDING_CAMERA_END_Y
                - FINAL_ENDING_CAMERA_START_Y
            ) * camera_progress
        )

        if final_ending_timer >= FINAL_ENDING_FADE_START:
            fade_progress = (
                final_ending_timer - FINAL_ENDING_FADE_START
            ) / (
                FINAL_ENDING_TOTAL_DURATION
                - FINAL_ENDING_FADE_START
            )
            final_ending_fade_alpha = int(
                max(0.0, min(1.0, fade_progress)) * 255
            )

        if final_ending_timer >= FINAL_ENDING_TOTAL_DURATION:
            final_ending_fade_alpha = 255
            final_ending_finished = True

            # The "one last look" is now complete and the screen is
            # completely black. Hold that black frame for one second,
            # then start the separate final game-ending video.
            game_ending_video = None
            game_ending_video_error = None
            game_ending_start_pending = True
            game_ending_start_delay = 1.0
            scene = "GAME_ENDING_VIDEO"

            print("ONE LAST LOOK COMPLETE")
            print("GAME ENDING VIDEO QUEUED")

    # =====================================================
    # FINAL GAME ENDING VIDEO
    # =====================================================

    elif scene == "GAME_ENDING_VIDEO":
        # Keep the Pygame surface black until the video takes over.
        screen.fill((0, 0, 0))

        if game_ending_video is None and game_ending_start_pending:
            game_ending_start_delay -= dt

            if game_ending_start_delay <= 0.0:
                game_ending_start_pending = False

                game_ending_video = FinalShotVideo(
                    GAME_ENDING_VIDEO_PATH,
                    WIDTH,
                    HEIGHT,
                    pygame_window_handle
                )

                if game_ending_video.start():
                    print("GAME ENDING VIDEO STARTED")
                else:
                    game_ending_video_error = game_ending_video.error
                    print(
                        "GAME ENDING VIDEO ERROR:",
                        game_ending_video_error
                    )

        if game_ending_video is not None:
            if game_ending_video.error:
                game_ending_video_error = game_ending_video.error
            elif game_ending_video.started:
                game_ending_video.update(dt)

                if game_ending_video.finished:
                    game_ending_video.stop()
                    game_ending_video = None
                    game_ending_start_pending = False
                    game_ending_start_delay = 0.0

                    # Leave the game on a clean black final frame.
                    screen.fill((0, 0, 0))
                    pygame.display.flip()
                    pygame.event.pump()

                    scene = "FINAL_TITLE"
                    print("GAME ENDING VIDEO COMPLETE")
                    print("CAMPUS OUTBREAK - GAME COMPLETE")

    # =====================================================
    # LEGACY FINAL TITLE
    # =====================================================
    # Kept as a valid state for compatibility with older saves/tools, but
    # the new ending no longer transitions to the text-only title.
    elif scene == "FINAL_TITLE":
        pass

    # =====================================================
    # TRANSITION TO MECHANICAL BLOCK
    # =====================================================

    elif scene == "TRANSITION_TO_MECHANICAL":

        transition.update(dt)

        if (
            not transition.active
            and transition.mode == "IN"
        ):

            reset_mechanical_scene()

            scene = "MECHANICAL_BLOCK"

            transition.start_out()

    # =====================================================
    # MECHANICAL BLOCK
    # =====================================================

    elif scene == "MECHANICAL_BLOCK":

        transition.update(dt)

        if not transition.active:

            if (
                not mechanical_intro_active
                and not mechanical_students_dialogue_active
                and not mechanical_combat.chapter_complete
            ):
                player.update(
                    dt,
                    mechanical_block.width,
                    mechanical_block.height,
                    mechanical_collision
                )

            mechanical_camera.update(player)

            if (
                not mechanical_combat.chapter_complete
                and not mechanical_intro_active
            ):
                target = pygame.Vector2(
                    player.rect.centerx - 70,
                    player.rect.centery + 20
                )

                current = pygame.Vector2(
                    viveka_campus.rect.center
                )

                delta = target - current

                if delta.length_squared() > 40 ** 2:
                    delta.normalize_ip()
                    current += (
                        delta * viveka_follow_speed * dt
                    )

                viveka_campus.rect.center = (
                    int(current.x),
                    int(current.y)
                )

            if mechanical_combat_started:

                # Respawn protection prevents a zombie already standing
                # beside the player from consuming another life instantly.
                mechanical_respawn_invulnerability = max(
                    0.0,
                    mechanical_respawn_invulnerability - dt
                )

                if not mechanical_player_dead:
                    mechanical_combat.update(
                        player,
                        dt
                    )

                    # StudentZombie writes damage into this attribute.
                    # Keep the combat object's immunity synchronized.
                    mechanical_combat.immunity = max(
                        0,
                        player.mechanical_immunity
                    )

                    # -------------------------------------------------
                    # HERO DEATH / RESPAWN
                    # -------------------------------------------------
                    if (
                        mechanical_combat.immunity <= 0
                        and mechanical_respawn_invulnerability <= 0
                    ):
                        result = mechanical_combat.handle_death()

                        if result == "RESPAWN":
                            # Restart the current stage with fresh zombies,
                            # 100 immunity and 50 bullets.
                            mechanical_combat.set_stage(
                                mechanical_combat.stage
                            )
                            configure_mechanical_combat()

                            set_player_position(
                                mechanical_block.entry_point[0],
                                mechanical_block.entry_point[1]
                            )

                            player.direction = "right"
                            player.walking = False

                            mechanical_respawn_invulnerability = (
                                MECHANICAL_RESPAWN_INVULNERABILITY
                            )
                            mechanical_death_message_timer = 2.0

                            print(
                                "HERO DEFEATED - RESPAWNING"
                            )
                            print(
                                f"RESPAWNS LEFT: "
                                f"{mechanical_combat.respawns_left}/3"
                            )

                        else:
                            # No respawns remain. Stop the combat and show
                            # a real game-over screen instead of silently
                            # continuing with zero immunity.
                            mechanical_player_dead = True
                            mechanical_death_message_timer = 0.0
                            mechanical_combat.immunity = 0
                            mechanical_combat.bullets.clear()
                            mechanical_combat.zombies.clear()

                            print(
                                "HERO DEFEATED - NO RESPAWNS LEFT"
                            )
                            print(
                                "PRESS ENTER TO RETRY MECHANICAL BLOCK"
                            )

                if not mechanical_player_dead:
                    mechanical_combat.update_rescued_students(
                        player,
                        dt
                    )

                    if (
                        mechanical_combat.chapter_complete
                        and not mechanical_students_dialogue_active
                        and not mechanical_checkpoint
                    ):
                        mechanical_students_dialogue_active = True
                        mechanical_students_dialogue_index = 0

                        print(
                            "ALL MECHANICAL BLOCK STAGES COMPLETE"
                        )
                        print(
                            "STUDENTS RESCUED - PRESS E"
                        )

    # =====================================================
    # DRAW
    # =====================================================

    screen.fill(
        (8, 10, 12)
    )


    # =====================================================
    # CAMPUS DRAW
    # =====================================================

    if (
        scene in (
            "INTRO_BUS",
            "INTRO_EXIT",
            "INTRO_REVEAL",
            "INTRO_DIALOGUE",
            "CAMPUS",
            "TRANSITION_TO_AI",
            "CAMPUS_RETURN",
            "TRANSITION_TO_LIBRARY_TRAVEL",
            "TRANSITION_FROM_LIBRARY"
        )
    ):

        campus.draw(
            screen,
            campus_camera
        )

        # -----------------------------------------------------
        # DARK NIGHT-TIME CAMPUS
        # -----------------------------------------------------

        dark_overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        dark_overlay.fill(
            (5, 9, 18, 105)
        )

        screen.blit(
            dark_overlay,
            (0, 0)
        )

        # -----------------------------------------------------
        # BUS - OPENING CINEMATIC
        # -----------------------------------------------------

        if scene in (
            "INTRO_BUS",
            "INTRO_EXIT",
            "INTRO_REVEAL"
        ):

            bus_screen_x = (
                int(bus_x - campus_camera.x)
            )

            bus_screen_y = (
                int(bus_y - campus_camera.y)
            )

            # Shadow
            pygame.draw.ellipse(
                screen,
                (5, 7, 10),
                (
                    bus_screen_x - 5,
                    bus_screen_y + bus_height - 5,
                    bus_width + 10,
                    18
                )
            )

            # Bus body
            pygame.draw.rect(
                screen,
                (35, 47, 58),
                (
                    bus_screen_x,
                    bus_screen_y,
                    bus_width,
                    bus_height
                ),
                border_radius=8
            )

            # Bus lower strip
            pygame.draw.rect(
                screen,
                (185, 55, 48),
                (
                    bus_screen_x,
                    bus_screen_y + 43,
                    bus_width,
                    12
                ),
                border_radius=3
            )

            # Windows
            for i in range(5):
                window = pygame.Rect(
                    bus_screen_x + 14 + i * 32,
                    bus_screen_y + 10,
                    25,
                    22
                )

                pygame.draw.rect(
                    screen,
                    (15, 25, 35),
                    window,
                    border_radius=3
                )

                pygame.draw.rect(
                    screen,
                    (75, 105, 120),
                    window,
                    1,
                    border_radius=3
                )

            # Wheels
            pygame.draw.circle(
                screen,
                (12, 14, 17),
                (
                    bus_screen_x + 38,
                    bus_screen_y + bus_height
                ),
                13
            )

            pygame.draw.circle(
                screen,
                (12, 14, 17),
                (
                    bus_screen_x + bus_width - 38,
                    bus_screen_y + bus_height
                ),
                13
            )

            # Headlights
            pygame.draw.rect(
                screen,
                (240, 210, 125),
                (
                    bus_screen_x + bus_width - 8,
                    bus_screen_y + 17,
                    7,
                    12
                ),
                border_radius=2
            )

        # The hero is hidden while he is still inside the bus.
        if scene != "INTRO_BUS":
            player.draw(
                screen,
                campus_camera
            )

        if (
            viveka_following
            and scene in ("CAMPUS", "CAMPUS_RETURN")
        ):
            update_viveka_follow(dt)

            viveka_campus.draw(
                screen,
                campus_camera
            )

        # -----------------------------------------------------
        # GUN ON THE GROUND
        # -----------------------------------------------------

        if (
            scene == "CAMPUS"
            and not gun_picked
        ):

            gx = int(
                gun_rect.x - campus_camera.x
            )

            gy = int(
                gun_rect.y - campus_camera.y
            )

            pygame.draw.ellipse(
                screen,
                (20, 22, 25),
                (
                    gx - 4,
                    gy + 8,
                    34,
                    10
                )
            )

            pygame.draw.rect(
                screen,
                (45, 47, 50),
                (
                    gx,
                    gy,
                    20,
                    7
                ),
                border_radius=2
            )

            pygame.draw.rect(
                screen,
                (80, 82, 85),
                (
                    gx + 15,
                    gy - 2,
                    9,
                    6
                ),
                border_radius=2
            )

            pygame.draw.rect(
                screen,
                (55, 38, 28),
                (
                    gx + 5,
                    gy + 5,
                    7,
                    10
                ),
                border_radius=2
            )

        if scene == "CAMPUS":

            if not rescue_complete:
                ai_interaction.draw(
                    screen
                )

            # -------------------------------------------------
            # MECHANICAL BLOCK ENTRANCE PROMPT
            # -------------------------------------------------

            if (
                rescue_complete
                and mechanical_objective_active
                and player.near(MECH_ENTRANCE_ZONE)
            ):

                prompt_font = pygame.font.Font(
                    None,
                    28
                )

                prompt = prompt_font.render(
                    "[E]  ENTER MECHANICAL BLOCK",
                    True,
                    (245, 201, 55)
                )

                shadow = prompt_font.render(
                    "[E]  ENTER MECHANICAL BLOCK",
                    True,
                    (10, 10, 10)
                )

                prompt_rect = prompt.get_rect(
                    center=(
                        MECH_ENTRANCE_ZONE.centerx
                        - campus_camera.x,
                        MECH_ENTRANCE_ZONE.top
                        - campus_camera.y
                        - 20
                    )
                )

                screen.blit(
                    shadow,
                    prompt_rect.move(2, 2)
                )

                screen.blit(
                    prompt,
                    prompt_rect
                )


            # -------------------------------------------------
            # LIBRARY OBJECTIVE / ENTRANCE
            # -------------------------------------------------

            if library_objective_active:
                # Objective card.
                objective_width = 650
                objective_height = 104

                objective_box = pygame.Rect(
                    (WIDTH - objective_width) // 2,
                    28,
                    objective_width,
                    objective_height
                )

                pygame.draw.rect(
                    screen,
                    (6, 10, 14),
                    objective_box,
                    border_radius=14
                )

                pygame.draw.rect(
                    screen,
                    (225, 183, 58),
                    objective_box,
                    2,
                    border_radius=14
                )

                objective_label_font = pygame.font.Font(None, 18)
                objective_text_font = pygame.font.Font(None, 28)
                objective_reason_font = pygame.font.Font(None, 21)

                objective_label = objective_label_font.render(
                    "NEW OBJECTIVE",
                    True,
                    (225, 183, 58)
                )

                objective_text = objective_text_font.render(
                    "SAVE THE FACULTY IN THE LIBRARY",
                    True,
                    (242, 243, 238)
                )

                objective_reason = objective_reason_font.render(
                    "Some faculty members are trapped inside.",
                    True,
                    (165, 174, 178)
                )

                screen.blit(
                    objective_label,
                    (
                        objective_box.x + 20,
                        objective_box.y + 12
                    )
                )

                screen.blit(
                    objective_text,
                    (
                        objective_box.x + 20,
                        objective_box.y + 39
                    )
                )

                screen.blit(
                    objective_reason,
                    (
                        objective_box.x + 20,
                        objective_box.y + 73
                    )
                )

                # Keep the real Library artwork visible.
                # The entrance rectangle is used only for interaction/collision;
                # do not draw it over the Library on the Campus.
                lr = library_campus_entrance

                if player.near(lr):
                    prompt_font = pygame.font.Font(None, 28)
                    prompt = prompt_font.render(
                        "[E]  ENTER LIBRARY",
                        True,
                        (245, 201, 55)
                    )
                    shadow = prompt_font.render(
                        "[E]  ENTER LIBRARY",
                        True,
                        (10, 10, 10)
                    )
                    prompt_rect = prompt.get_rect(
                        center=(
                            lr.centerx - campus_camera.x,
                            lr.bottom - campus_camera.y + 28
                        )
                    )
                    screen.blit(
                        shadow,
                        prompt_rect.move(2, 2)
                    )
                    screen.blit(
                        prompt,
                        prompt_rect
                    )

            if research_return_objective_active:
                objective_width = 620
                objective_height = 104
                objective_box = pygame.Rect(
                    (WIDTH - objective_width) // 2,
                    28,
                    objective_width,
                    objective_height
                )
                pygame.draw.rect(screen, (6, 10, 14), objective_box, border_radius=14)
                pygame.draw.rect(screen, (110, 190, 205), objective_box, 3, border_radius=14)
                label_font = pygame.font.Font(None, 18)
                objective_font = pygame.font.Font(None, 28)
                reason_font = pygame.font.Font(None, 21)
                screen.blit(label_font.render("NEW OBJECTIVE", True, (110, 190, 205)), (objective_box.x + 20, objective_box.y + 12))
                screen.blit(objective_font.render("RETURN TO THE LIBRARY", True, (242, 243, 238)), (objective_box.x + 20, objective_box.y + 39))
                screen.blit(reason_font.render("The Principal revealed a hidden research facility below it.", True, (165, 174, 178)), (objective_box.x + 20, objective_box.y + 73))

                # Use the Library entrance only as an invisible interaction zone.
                # Do not draw a rectangle over the actual Library artwork.
                lr = library_campus_entrance
                if player.near(lr):
                    pf = pygame.font.Font(None, 28)
                    ps = pf.render("[E]  RETURN TO LIBRARY", True, (245, 201, 55))
                    screen.blit(ps, ps.get_rect(center=(lr.centerx - campus_camera.x, lr.bottom - campus_camera.y + 28)))

            if library_main_block_objective_active:
                objective_width = 620
                objective_height = 104

                objective_box = pygame.Rect(
                    (WIDTH - objective_width) // 2,
                    28,
                    objective_width,
                    objective_height
                )

                pygame.draw.rect(
                    screen,
                    (6, 10, 14),
                    objective_box,
                    border_radius=14
                )

                pygame.draw.rect(
                    screen,
                    (225, 183, 58),
                    objective_box,
                    2,
                    border_radius=14
                )

                label_font = pygame.font.Font(None, 18)
                objective_font = pygame.font.Font(None, 28)
                reason_font = pygame.font.Font(None, 21)

                label = label_font.render(
                    "NEW OBJECTIVE",
                    True,
                    (225, 183, 58)
                )
                objective_text = objective_font.render(
                    "GO TO THE MAIN BLOCK",
                    True,
                    (242, 243, 238)
                )
                reason = reason_font.render(
                    "The Principal is surrounded by infected.",
                    True,
                    (165, 174, 178)
                )

                screen.blit(
                    label,
                    (
                        objective_box.x + 20,
                        objective_box.y + 12
                    )
                )
                screen.blit(
                    objective_text,
                    (
                        objective_box.x + 20,
                        objective_box.y + 39
                    )
                )
                screen.blit(
                    reason,
                    (
                        objective_box.x + 20,
                        objective_box.y + 73
                    )
                )

                # Main Block entrance interaction.
                if player.near(MAIN_BLOCK_ENTRANCE_ZONE):
                    prompt_font = pygame.font.Font(None, 28)
                    prompt = prompt_font.render(
                        "[E]  ENTER MAIN BLOCK",
                        True,
                        (245, 201, 55)
                    )
                    screen.blit(
                        prompt,
                        prompt.get_rect(
                            center=(
                                MAIN_BLOCK_ENTRANCE_ZONE.centerx - campus_camera.x,
                                MAIN_BLOCK_ENTRANCE_ZONE.top - campus_camera.y - 20
                            )
                        )
                    )

                # Visible destination marker for the next chapter.
                main_target = pygame.Rect(
                    campus.main_block.left - 55,
                    campus.main_block.centery - 70,
                    55,
                    140
                )

                pygame.draw.rect(
                    screen,
                    (70, 45, 25),
                    (
                        main_target.x - campus_camera.x,
                        main_target.y - campus_camera.y,
                        main_target.width,
                        main_target.height
                    ),
                    border_radius=8
                )

                pygame.draw.rect(
                    screen,
                    (225, 183, 58),
                    (
                        main_target.x - campus_camera.x,
                        main_target.y - campus_camera.y,
                        main_target.width,
                        main_target.height
                    ),
                    3,
                    border_radius=8
                )

                main_label_font = pygame.font.Font(None, 26)
                main_label = main_label_font.render(
                    "MAIN BLOCK",
                    True,
                    (245, 225, 170)
                )

                screen.blit(
                    main_label,
                    main_label.get_rect(
                        center=(
                            main_target.centerx - campus_camera.x,
                            main_target.top - campus_camera.y - 16
                        )
                    )
                )

            # -------------------------------------------------
            # GUN PICKUP PROMPT
            # -------------------------------------------------

            if (
                not gun_picked
                and player.rect.colliderect(
                    gun_rect.inflate(55, 55)
                )
            ):

                prompt_font = pygame.font.Font(
                    None,
                    28
                )

                prompt = prompt_font.render(
                    "[E]  PICK UP WEAPON",
                    True,
                    (245, 201, 55)
                )

                screen.blit(
                    prompt,
                    prompt.get_rect(
                        center=(
                            gun_rect.centerx
                            - campus_camera.x,
                            gun_rect.top
                            - campus_camera.y
                            - 25
                        )
                    )
                )

            # -------------------------------------------------
            # TUTORIAL AFTER GUN PICKUP
            # -------------------------------------------------

            # -------------------------------------------------
            # MAIN STORY OBJECTIVE
            # -------------------------------------------------

            # This appears immediately after the opening dialogue.
            # It tells a new player exactly where to go and why.
            if story_objective_active:

                objective_width = 610
                objective_height = 104

                objective_box = pygame.Rect(
                    (WIDTH - objective_width) // 2,
                    28,
                    objective_width,
                    objective_height
                )

                pygame.draw.rect(
                    screen,
                    (6, 10, 14),
                    objective_box,
                    border_radius=14
                )

                pygame.draw.rect(
                    screen,
                    (225, 183, 58),
                    objective_box,
                    2,
                    border_radius=14
                )

                label_font = pygame.font.Font(None, 18)
                objective_font = pygame.font.Font(None, 28)
                reason_font = pygame.font.Font(None, 21)

                label = label_font.render(
                    "NEW OBJECTIVE",
                    True,
                    (225, 183, 58)
                )

                objective_text = objective_font.render(
                    "GO TO THE AI BLOCK FOR THE HOD",
                    True,
                    (242, 243, 238)
                )

                reason = reason_font.render(
                    "Find her and help save your friends.",
                    True,
                    (165, 174, 178)
                )

                screen.blit(
                    label,
                    (
                        objective_box.x + 20,
                        objective_box.y + 12
                    )
                )

                screen.blit(
                    objective_text,
                    (
                        objective_box.x + 20,
                        objective_box.y + 39
                    )
                )

                screen.blit(
                    reason,
                    (
                        objective_box.x + 20,
                        objective_box.y + 73
                    )
                )

            if (
                gun_picked
                and objective_active
                and not mechanical_objective_active
            ):

                objective_width = 560
                objective_height = 88

                objective_box = pygame.Rect(
                    (WIDTH - objective_width) // 2,
                    28,
                    objective_width,
                    objective_height
                )

                pygame.draw.rect(
                    screen,
                    (7, 11, 14),
                    objective_box,
                    border_radius=11
                )

                pygame.draw.rect(
                    screen,
                    (225, 183, 58),
                    objective_box,
                    2,
                    border_radius=11
                )

                objective_label_font = pygame.font.Font(
                    None,
                    18
                )

                objective_text_font = pygame.font.Font(
                    None,
                    27
                )

                objective_label = objective_label_font.render(
                    "NEW OBJECTIVE",
                    True,
                    (225, 183, 58)
                )

                objective_text = objective_text_font.render(
                    "GO TO THE AI BLOCK FOR THE HOD",
                    True,
                    (240, 242, 238)
                )

                screen.blit(
                    objective_label,
                    (
                        objective_box.x + 20,
                        objective_box.y + 11
                    )
                )

                screen.blit(
                    objective_text,
                    (
                        objective_box.x + 20,
                        objective_box.y + 40
                    )
                )

            # -------------------------------------------------
            # MECHANICAL BLOCK OBJECTIVE
            # -------------------------------------------------

            if mechanical_objective_active:

                objective_width = 610
                objective_height = 104

                objective_box = pygame.Rect(
                    (WIDTH - objective_width) // 2,
                    28,
                    objective_width,
                    objective_height
                )

                pygame.draw.rect(
                    screen,
                    (6, 10, 14),
                    objective_box,
                    border_radius=14
                )

                pygame.draw.rect(
                    screen,
                    (225, 183, 58),
                    objective_box,
                    2,
                    border_radius=14
                )

                label_font = pygame.font.Font(None, 18)
                objective_font = pygame.font.Font(None, 28)
                reason_font = pygame.font.Font(None, 21)

                label = label_font.render(
                    "NEW OBJECTIVE",
                    True,
                    (225, 183, 58)
                )

                objective_text = objective_font.render(
                    "GO TO THE MECHANICAL BLOCK",
                    True,
                    (242, 243, 238)
                )

                reason = reason_font.render(
                    "Viveka Mam is following you. Save the students.",
                    True,
                    (165, 174, 178)
                )

                screen.blit(
                    label,
                    (
                        objective_box.x + 20,
                        objective_box.y + 12
                    )
                )

                screen.blit(
                    objective_text,
                    (
                        objective_box.x + 20,
                        objective_box.y + 39
                    )
                )

                screen.blit(
                    reason,
                    (
                        objective_box.x + 20,
                        objective_box.y + 73
                    )
                )

            if gun_picked:

                tutorial_box = pygame.Rect(
                    24,
                    HEIGHT - 108,
                    455,
                    78
                )

                pygame.draw.rect(
                    screen,
                    (8, 12, 17),
                    tutorial_box,
                    border_radius=9
                )

                pygame.draw.rect(
                    screen,
                    (245, 201, 55),
                    tutorial_box,
                    2,
                    border_radius=9
                )

                tutorial_font = pygame.font.Font(
                    None,
                    24
                )

                small_font = pygame.font.Font(
                    None,
                    20
                )

                if tutorial_stage == 1:

                    title = tutorial_font.render(
                        "MOVEMENT",
                        True,
                        (245, 201, 55)
                    )

                    instruction = small_font.render(
                        "WASD / ARROW KEYS  —  MOVE",
                        True,
                        (235, 235, 230)
                    )

                else:

                    title = tutorial_font.render(
                        "SURVIVAL CONTROLS",
                        True,
                        (245, 201, 55)
                    )

                    instruction = small_font.render(
                        "WASD / ARROWS — MOVE   •   LMB — AIM / FIRE",
                        True,
                        (235, 235, 230)
                    )

                screen.blit(
                    title,
                    (
                        tutorial_box.x + 18,
                        tutorial_box.y + 12
                    )
                )

                screen.blit(
                    instruction,
                    (
                        tutorial_box.x + 18,
                        tutorial_box.y + 43
                    )
                )


    # =====================================================
    # AI BLOCK DRAW
    # =====================================================

    elif scene == "AI_BLOCK":

        # IMPORTANT:
        # The campus is NOT drawn here.
        # Only the AI Block is rendered.
        ai_block.draw(
            screen,
            ai_camera
        )

        combat.draw(
            screen,
            ai_camera
        )

        player.draw(
            screen,
            ai_camera
        )

        combat_ui.draw(
            screen,
            combat
        )

        # =================================================
        # VIVEKA MAM
        # =================================================

        if combat.combat_complete:

            viveka.draw(
                screen,
                ai_camera
            )

            # Interaction prompt.
            if (
                player.near(viveka.rect)
                and not dialogue_active
                and not rescue_complete
            ):

                prompt_font = pygame.font.Font(
                    None,
                    28
                )

                prompt = prompt_font.render(
                    "[E]  TALK TO VIVEKA MAM",
                    True,
                    (245, 201, 55)
                )

                prompt_shadow = prompt_font.render(
                    "[E]  TALK TO VIVEKA MAM",
                    True,
                    (10, 10, 10)
                )

                px = (
                    viveka.rect.centerx
                    - ai_camera.x
                )

                py = (
                    viveka.rect.top
                    - ai_camera.y
                    - 25
                )

                prompt_rect = prompt.get_rect(
                    center=(px, py)
                )

                screen.blit(
                    prompt_shadow,
                    prompt_rect.move(2, 2)
                )

                screen.blit(
                    prompt,
                    prompt_rect
                )


        # =================================================
        # VIVEKA DIALOGUE
        # =================================================

        if dialogue_active:

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 125)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            box = pygame.Rect(
                110,
                HEIGHT - 205,
                WIDTH - 220,
                165
            )

            pygame.draw.rect(
                screen,
                (10, 14, 17),
                box,
                border_radius=10
            )

            pygame.draw.rect(
                screen,
                (245, 201, 55),
                box,
                2,
                border_radius=10
            )

            speaker, line = viveka_dialogue[
                dialogue_index
            ]

            speaker_font = pygame.font.Font(
                None,
                30
            )

            line_font = pygame.font.Font(
                None,
                25
            )

            hint_font = pygame.font.Font(
                None,
                20
            )

            speaker_surface = speaker_font.render(
                speaker,
                True,
                (245, 201, 55)
            )

            screen.blit(
                speaker_surface,
                (
                    box.x + 22,
                    box.y + 16
                )
            )

            # Basic text wrapping.
            words = line.split()
            wrapped = []
            current_line = ""

            for word in words:

                candidate = (
                    current_line + " " + word
                ).strip()

                if (
                    line_font.size(candidate)[0]
                    > box.width - 44
                ):
                    wrapped.append(current_line)
                    current_line = word
                else:
                    current_line = candidate

            if current_line:
                wrapped.append(current_line)

            for index, wrapped_line in enumerate(wrapped):

                line_surface = line_font.render(
                    wrapped_line,
                    True,
                    (240, 240, 235)
                )

                screen.blit(
                    line_surface,
                    (
                        box.x + 22,
                        box.y + 58 + index * 30
                    )
                )

            hint = hint_font.render(
                "Press E to continue",
                True,
                (170, 180, 180)
            )

            screen.blit(
                hint,
                (
                    box.right - hint.get_width() - 22,
                    box.bottom - 28
                )
            )


        # =================================================
        # RESCUE COMPLETE
        # =================================================

        if rescue_complete:

            panel = pygame.Rect(
                315,
                250,
                650,
                195
            )

            pygame.draw.rect(
                screen,
                (8, 13, 16),
                panel,
                border_radius=10
            )

            pygame.draw.rect(
                screen,
                (110, 230, 125),
                panel,
                3,
                border_radius=10
            )

            title_font = pygame.font.Font(
                None,
                46
            )

            body_font = pygame.font.Font(
                None,
                24
            )

            title = title_font.render(
                "VIVEKA MAM RESCUED",
                True,
                (110, 230, 125)
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(
                        panel.centerx,
                        panel.y + 58
                    )
                )
            )

            body = body_font.render(
                "The Mechanical Block may need help.",
                True,
                (240, 240, 235)
            )

            screen.blit(
                body,
                body.get_rect(
                    center=(
                        panel.centerx,
                        panel.y + 112
                    )
                )
            )

            next_objective = body_font.render(
                "NEXT OBJECTIVE  •  CHECK MECHANICAL BLOCK",
                True,
                (245, 201, 55)
            )

            screen.blit(
                next_objective,
                next_objective.get_rect(
                    center=(
                        panel.centerx,
                        panel.y + 153
                    )
                )
            )


        # Mission intro card.
        if ai_intro_timer < AI_INTRO_DURATION:

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 120)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            box = pygame.Rect(
                185,
                215,
                910,
                285
            )

            pygame.draw.rect(
                screen,
                (10, 13, 16),
                box,
                border_radius=10
            )

            pygame.draw.rect(
                screen,
                (245, 201, 55),
                box,
                3,
                border_radius=10
            )

            title_font = pygame.font.Font(
                None,
                48
            )

            body_font = pygame.font.Font(
                None,
                27
            )

            hint_font = pygame.font.Font(
                None,
                22
            )

            title = title_font.render(
                "AI BLOCK",
                True,
                (245, 201, 55)
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(WIDTH // 2, 270)
                )
            )

            mission = body_font.render(
                "MISSION: SECURE THE AI BLOCK",
                True,
                (245, 245, 235)
            )

            screen.blit(
                mission,
                mission.get_rect(
                    center=(WIDTH // 2, 330)
                )
            )

            objective = body_font.render(
                "Investigate the infected area.",
                True,
                (220, 220, 215)
            )

            screen.blit(
                objective,
                objective.get_rect(
                    center=(WIDTH // 2, 375)
                )
            )

            hint = hint_font.render(
                "Prepare yourself...",
                True,
                (170, 180, 180)
            )

            screen.blit(
                hint,
                hint.get_rect(
                    center=(WIDTH // 2, 440)
                )
            )



    # =====================================================
    # LIBRARY DRAW
    # =====================================================

    elif scene == "LIBRARY":

        library_chapter.draw(
            screen,
            library_chapter.camera
        )

        # Zombies and bullets are rendered only during combat.
        for zombie in library_chapter.zombies:
            zombie.draw(
                screen,
                library_chapter.camera
            )

        for bullet in library_chapter.bullets:
            bullet.draw(
                screen,
                library_chapter.camera
            )

        player.draw(
            screen,
            library_chapter.camera
        )

        # Story characters appear only after the hidden-door observation.
        if library_survivors_visible:
            draw_library_story_scene(
                screen,
                library_chapter.camera
            )

        # Viveka has moved away to search for the faculty. The player
        # remains alone in the combat hall.
        if (
            library_chapter.cinematic_state == "COMBAT"
            and library_chapter.kills == 0
        ):
            search_font = pygame.font.Font(None, 24)
            search_text = search_font.render(
                "VIVEKA MAM IS SEARCHING FOR THE FACULTY...",
                True,
                (190, 200, 198)
            )
            screen.blit(
                search_text,
                search_text.get_rect(
                    center=(WIDTH // 2, HEIGHT - 78)
                )
            )

        if library_chapter.cinematic_state == "COMBAT":
            draw_library_hud(
                screen,
                library_chapter
            )

        # Door observation cinematic.
        if library_chapter.cinematic_state == "DOOR_OBSERVE":

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 70))
            screen.blit(overlay, (0, 0))

            door = library_chapter.door_rect()
            door_screen = door.move(
                -library_chapter.camera.x,
                -library_chapter.camera.y
            )

            focus = pygame.Rect(
                door_screen.x - 70,
                door_screen.y - 70,
                door_screen.width + 140,
                door_screen.height + 140
            )

            pygame.draw.rect(
                screen,
                (220, 190, 90),
                focus,
                2,
                border_radius=8
            )

            observe_font = pygame.font.Font(None, 29)
            remaining = max(
                0.0,
                LIBRARY_DOOR_OBSERVE_DURATION
                - library_chapter.door_timer
            )

            observe_text = observe_font.render(
                f"Something is hidden here...  {remaining:.1f}s",
                True,
                (235, 225, 195)
            )

            screen.blit(
                observe_text,
                observe_text.get_rect(
                    center=(WIDTH // 2, HEIGHT - 85)
                )
            )

        # Rack fall cinematic.
        if library_chapter.cinematic_state == "RACK_FALL":
            cinematic_font = pygame.font.Font(None, 34)

            if library_chapter.rack_timer < 0.45:
                text_value = "..."
            elif library_chapter.rack_timer < 1.0:
                text_value = "THE BOOK RACK IS MOVING..."
            else:
                text_value = "CRASH!"

            cinematic_text = cinematic_font.render(
                text_value,
                True,
                (240, 230, 205)
            )

            screen.blit(
                cinematic_text,
                cinematic_text.get_rect(
                    center=(WIDTH // 2, HEIGHT - 90)
                )
            )

        # Four-second observation has completed; story dialogue begins.
        if library_chapter.story_active:
            draw_library_dialogue(
                screen,
                library_chapter
            )

        # Library failure/retry screen.
        if library_player_dead:

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            box = pygame.Rect(
                300,
                210,
                680,
                290
            )

            pygame.draw.rect(
                screen,
                (7, 10, 13),
                box,
                border_radius=14
            )
            pygame.draw.rect(
                screen,
                (225, 75, 60),
                box,
                3,
                border_radius=14
            )

            title_font = pygame.font.Font(None, 50)
            body_font = pygame.font.Font(None, 26)
            hint_font = pygame.font.Font(None, 22)

            title = title_font.render(
                "HERO DOWN",
                True,
                (235, 80, 65)
            )
            body = body_font.render(
                "The infected overwhelmed you in the Library.",
                True,
                (240, 240, 235)
            )
            hint = hint_font.render(
                "PRESS ENTER  •  RESTART LIBRARY LEVEL",
                True,
                (245, 201, 55)
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(box.centerx, box.y + 72)
                )
            )
            screen.blit(
                body,
                body.get_rect(
                    center=(box.centerx, box.y + 135)
                )
            )
            screen.blit(
                hint,
                hint.get_rect(
                    center=(box.centerx, box.y + 205)
                )
            )

        # Chapter completion after final dialogue.
        if (
            library_chapter.story_complete
            and library_main_block_objective_active
        ):
            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 90))
            screen.blit(overlay, (0, 0))

            panel = pygame.Rect(
                280,
                235,
                720,
                230
            )

            pygame.draw.rect(
                screen,
                (8, 13, 16),
                panel,
                border_radius=12
            )
            pygame.draw.rect(
                screen,
                (110, 230, 125),
                panel,
                3,
                border_radius=12
            )

            title_font = pygame.font.Font(None, 48)
            body_font = pygame.font.Font(None, 25)

            title = title_font.render(
                "LIBRARY SECURED",
                True,
                (110, 230, 125)
            )
            body = body_font.render(
                "The faculty survivors have been found.",
                True,
                (240, 240, 235)
            )
            next_text = body_font.render(
                "NEXT OBJECTIVE  •  GO TO THE MAIN BLOCK",
                True,
                (245, 201, 55)
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(panel.centerx, panel.y + 62)
                )
            )
            screen.blit(
                body,
                body.get_rect(
                    center=(panel.centerx, panel.y + 125)
                )
            )
            screen.blit(
                next_text,
                next_text.get_rect(
                    center=(panel.centerx, panel.y + 175)
                )
            )

    # =====================================================
    # MAIN BLOCK DRAW
    # =====================================================

    elif scene == "MAIN_BLOCK":
        light_flicker = main_block_lights_seen and main_block_stage <= 2

        main_block.draw(
            screen,
            main_block_camera,
            main_block_stage,
            light_flicker=light_flicker,
            principal_visible=(main_block_principal_rescued or main_block_dialogue_active)
        )

        player.draw(
            screen,
            main_block_camera
        )

        # Small objective/status card.
        panel = pygame.Rect(24, 24, 405, 112)
        pygame.draw.rect(screen, (7, 10, 13), panel, border_radius=12)
        pygame.draw.rect(screen, (135, 115, 80), panel, 2, border_radius=12)

        small = pygame.font.Font(None, 18)
        title = pygame.font.Font(None, 28)
        body = pygame.font.Font(None, 21)

        screen.blit(
            small.render("MAIN BLOCK  //  INVESTIGATION", True, (190, 184, 166)),
            (panel.x + 16, panel.y + 12)
        )

        if main_block_research_objective_active:
            objective_text = "RESEARCH DEPARTMENT REVEALED"
        elif main_block_complete:
            objective_text = "PRINCIPAL RESCUED"
        elif main_block_stage >= 5:
            objective_text = "TALK TO THE PRINCIPAL"
        elif main_block_stage == 4:
            objective_text = "FIND THE PRINCIPAL'S OFFICE"
        elif main_block_stage == 3:
            objective_text = "FOLLOW THE SOUND"
        elif main_block_stage == 2:
            objective_text = "ANSWER THE PHONE"
        elif main_block_stage == 1:
            objective_text = "EXAMINE THE DAMAGED DOCUMENT"
        else:
            objective_text = "INVESTIGATE THE MAIN BLOCK"

        screen.blit(
            title.render(objective_text, True, (239, 225, 190)),
            (panel.x + 16, panel.y + 42)
        )

        screen.blit(
            body.render(
                "No infected detected. Something is wrong here.",
                True,
                (155, 164, 166)
            ),
            (panel.x + 16, panel.y + 76)
        )

        # Interaction prompts.
        if not main_block_dialogue_active and not main_block_complete:
            target = None
            prompt_text = ""

            if main_block_stage == 0 and player.near(main_block.computer_rect):
                target = main_block.computer_rect
                prompt_text = "[E]  CHECK COMPUTER"
            elif main_block_stage == 1 and player.near(main_block.document_rect):
                target = main_block.document_rect
                prompt_text = "[E]  EXAMINE DOCUMENT"
            elif main_block_stage == 2 and player.near(main_block.phone_rect):
                target = main_block.phone_rect
                prompt_text = "[E]  ANSWER PHONE"
            elif main_block_stage >= 4 and player.near(main_block.office_door):
                target = main_block.office_door
                prompt_text = "[E]  OPEN PRINCIPAL'S OFFICE"

            if target is not None:
                prompt_font = pygame.font.Font(None, 27)
                prompt = prompt_font.render(
                    prompt_text,
                    True,
                    (245, 201, 55)
                )
                screen.blit(
                    prompt,
                    prompt.get_rect(
                        center=(
                            target.centerx - main_block_camera.x,
                            target.top - main_block_camera.y - 28
                        )
                    )
                )

        # Computer alert cinematic.
        if main_block_stage == 1 and main_block_cinematic_timer < 3.0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 90))
            screen.blit(overlay, (0, 0))

            alert_box = pygame.Rect(280, 185, 720, 300)
            pygame.draw.rect(screen, (7, 11, 14), alert_box, border_radius=12)
            pygame.draw.rect(screen, (175, 58, 52), alert_box, 2, border_radius=12)

            f1 = pygame.font.Font(None, 40)
            f2 = pygame.font.Font(None, 27)
            f3 = pygame.font.Font(None, 23)

            screen.blit(f1.render("SYSTEM ALERT", True, (225, 75, 64)), (alert_box.x + 28, alert_box.y + 30))
            screen.blit(f2.render("BIOLOGICAL CONTAINMENT: FAILED", True, (238, 238, 230)), (alert_box.x + 28, alert_box.y + 95))
            screen.blit(f2.render("RESEARCH FACILITY: LOCKDOWN", True, (238, 238, 230)), (alert_box.x + 28, alert_box.y + 135))
            screen.blit(f2.render("STATUS: UNAUTHORIZED ACCESS", True, (238, 238, 230)), (alert_box.x + 28, alert_box.y + 175))
            screen.blit(f3.render("The monitor suddenly goes dark.", True, (155, 164, 166)), (alert_box.x + 28, alert_box.y + 225))

        # Phone cinematic.
        if main_block_stage == 3:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            screen.blit(overlay, (0, 0))
            f1 = pygame.font.Font(None, 42)
            f2 = pygame.font.Font(None, 28)
            screen.blit(
                f1.render("RING...", True, (235, 220, 190)),
                f1.render("RING...", True, (235, 220, 190)).get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35))
            )
            screen.blit(
                f2.render('"Help..."', True, (238, 238, 230)),
                f2.render('"Help..."', True, (238, 238, 230)).get_rect(center=(WIDTH // 2, HEIGHT // 2 + 15))
            )
            screen.blit(
                f2.render('"Main... office..."', True, (185, 190, 190)),
                f2.render('"Main... office..."', True, (185, 190, 190)).get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55))
            )

        # One-second shadow glimpse.
        if main_block_shadow_seen and main_block_stage == 4:
            shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 75))
            screen.blit(shadow, (0, 0))
            sf = pygame.font.Font(None, 24)
            screen.blit(
                sf.render("...something moved down the corridor.", True, (175, 180, 180)),
                (WIDTH // 2 - 190, HEIGHT - 105)
            )

        if main_block_dialogue_active:
            draw_main_block_dialogue(screen)

        if main_block_research_objective_active:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 95))
            screen.blit(overlay, (0, 0))
            panel2 = pygame.Rect(270, 230, 740, 250)
            pygame.draw.rect(screen, (7, 11, 15), panel2, border_radius=14)
            pygame.draw.rect(screen, (110, 230, 125), panel2, 3, border_radius=14)
            f1 = pygame.font.Font(None, 48)
            f2 = pygame.font.Font(None, 25)
            screen.blit(f1.render("PRINCIPAL RESCUED", True, (110, 230, 125)), f1.render("PRINCIPAL RESCUED", True, (110, 230, 125)).get_rect(center=(panel2.centerx, panel2.y + 65)))
            screen.blit(f2.render("The strange Library door leads to a secret Research Department.", True, (240, 240, 235)), f2.render("The strange Library door leads to a secret Research Department.", True, (240, 240, 235)).get_rect(center=(panel2.centerx, panel2.y + 125)))
            screen.blit(f2.render("NEXT OBJECTIVE  •  RETURN TO THE LIBRARY", True, (245, 201, 55)), f2.render("NEXT OBJECTIVE  •  RETURN TO THE LIBRARY", True, (245, 201, 55)).get_rect(center=(panel2.centerx, panel2.y + 185)))

        if main_block_complete:
            pf = pygame.font.Font(None, 27)
            prompt = pf.render("[E]  LEAVE MAIN BLOCK", True, (245, 201, 55))
            screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT - 78)))

    # =====================================================
    # RESEARCH LIBRARY DRAW
    # =====================================================

    elif scene == "RESEARCH_LIBRARY":
        library_chapter.draw(screen, library_chapter.camera)
        player.draw(screen, library_chapter.camera)

        door = library_chapter.door_rect().move(-library_chapter.camera.x, -library_chapter.camera.y)
        pygame.draw.rect(screen, (22, 18, 20), door, border_radius=4)
        pygame.draw.rect(screen, (120, 92, 55), door, 3, border_radius=4)
        f = pygame.font.Font(None, 24)
        screen.blit(f.render("HIDDEN RESEARCH ENTRANCE", True, (215, 190, 130)), (door.x - 50, door.y - 32))
        if player.near(library_chapter.door_rect()):
            prompt = f.render("[E]  ENTER HIDDEN DOOR", True, (245, 201, 55))
            screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT - 72)))

    # =====================================================
    # RESEARCH ELEVATOR DRAW
    # =====================================================

    elif scene == "RESEARCH_ELEVATOR":
        research_department.draw_elevator(screen, research_elevator_timer)

    # =====================================================
    # RESEARCH DEPARTMENT DRAW
    # =====================================================

    elif scene == "RESEARCH_DEPARTMENT":
        research_department.draw(screen)
        player.draw(screen, research_department.camera)

        if research_department.combat_complete and not research_department.dialogue_active and not research_department.complete:
            f = pygame.font.Font(None, 26)
            prompt = f.render("[E]  RESCUE RESEARCH DOCTORS", True, (245, 201, 55))
            screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT - 72)))

        if research_department.player_dead:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            screen.blit(overlay, (0, 0))
            box = pygame.Rect(300, 210, 680, 280)
            pygame.draw.rect(screen, (7, 10, 13), box, border_radius=14)
            pygame.draw.rect(screen, (225, 75, 60), box, 3, border_radius=14)
            f1 = pygame.font.Font(None, 48)
            f2 = pygame.font.Font(None, 24)
            screen.blit(f1.render("HERO DOWN", True, (235, 80, 65)), f1.render("HERO DOWN", True, (235, 80, 65)).get_rect(center=(box.centerx, box.y + 70)))
            screen.blit(f2.render("The infected doctor overwhelmed you.", True, (240, 240, 235)), f2.render("The infected doctor overwhelmed you.", True, (240, 240, 235)).get_rect(center=(box.centerx, box.y + 135)))
            screen.blit(f2.render("PRESS ENTER TO RETRY", True, (245, 201, 55)), f2.render("PRESS ENTER TO RETRY", True, (245, 201, 55)).get_rect(center=(box.centerx, box.y + 215)))

        if research_department.dialogue_active:
            pass  # dialogue is drawn by ResearchDepartment.draw()

    # =====================================================
    # BEST FRIEND REVEAL DRAW
    # =====================================================

    elif scene == "BEST_FRIEND_REVEAL":
        screen.fill((8, 9, 12))

        title_font = pygame.font.Font(None, 48)
        text_font = pygame.font.Font(None, 28)
        hint_font = pygame.font.Font(None, 22)

        screen.blit(
            title_font.render(
                "THE TRUTH",
                True,
                (225, 183, 58)
            ),
            title_font.render(
                "THE TRUTH",
                True,
                (225, 183, 58)
            ).get_rect(
                center=(WIDTH // 2, 100)
            )
        )

        # Containment-room silhouette.
        pygame.draw.rect(
            screen,
            (20, 24, 30),
            (330, 165, 620, 330),
            border_radius=18
        )
        pygame.draw.rect(
            screen,
            (90, 100, 110),
            (330, 165, 620, 330),
            2,
            border_radius=18
        )

        pygame.draw.rect(
            screen,
            (55, 65, 72),
            (560, 230, 160, 210),
            border_radius=12
        )

        pygame.draw.circle(
            screen,
            (130, 90, 78),
            (640, 250),
            35
        )

        pygame.draw.rect(
            screen,
            (80, 55, 55),
            (600, 285, 80, 130),
            border_radius=15
        )

        speaker, line = final_battle_dialogue.lines[
            final_battle_dialogue.index
        ]

        box = pygame.Rect(
            120,
            HEIGHT - 190,
            WIDTH - 240,
            135
        )

        pygame.draw.rect(
            screen,
            (7, 10, 13),
            box,
            border_radius=14
        )

        pygame.draw.rect(
            screen,
            (205, 173, 74),
            box,
            2,
            border_radius=14
        )

        screen.blit(
            text_font.render(
                speaker,
                True,
                (225, 183, 58)
            ),
            (box.x + 22, box.y + 18)
        )

        screen.blit(
            text_font.render(
                line,
                True,
                (238, 240, 238)
            ),
            (box.x + 22, box.y + 58)
        )

        screen.blit(
            hint_font.render(
                "E  CONTINUE",
                True,
                (150, 155, 160)
            ),
            (box.right - 145, box.bottom - 28)
        )

    # =====================================================
    # FINAL BOSS INTRO DRAW
    # =====================================================

    elif scene == "FINAL_BOSS_INTRO":
        screen.fill((6, 7, 9))

        font = pygame.font.Font(None, 58)
        small = pygame.font.Font(None, 28)

        screen.blit(
            font.render(
                "YOUR BEST FRIEND",
                True,
                (205, 55, 55)
            ),
            font.render(
                "YOUR BEST FRIEND",
                True,
                (205, 55, 55)
            ).get_rect(
                center=(WIDTH // 2, HEIGHT // 2 - 35)
            )
        )

        screen.blit(
            small.render(
                "THE INFECTION HAS TAKEN CONTROL",
                True,
                (225, 225, 220)
            ),
            small.render(
                "THE INFECTION HAS TAKEN CONTROL",
                True,
                (225, 225, 220)
            ).get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 25)
            )
        )

    # =====================================================
    # FINAL BOSS DRAW
    # =====================================================

    elif scene == "FINAL_BOSS":
        screen.fill((12, 11, 13))

        # Laboratory-style floor.
        for x in range(0, WIDTH, 80):
            pygame.draw.line(
                screen,
                (30, 31, 35),
                (x, 0),
                (x, HEIGHT),
                1
            )

        for y in range(0, HEIGHT, 80):
            pygame.draw.line(
                screen,
                (30, 31, 35),
                (0, y),
                (WIDTH, y),
                1
            )

        final_boss.draw(
            screen,
            final_battle_camera
        )

        player.draw(
            screen,
            final_battle_camera
        )

        ui = pygame.font.Font(None, 28)
        small = pygame.font.Font(None, 22)

        phase_text = ui.render(
            f"FINAL BOSS  //  PHASE {final_boss.phase}",
            True,
            (225, 75, 65)
        )
        screen.blit(
            phase_text,
            (30, 25)
        )

        immunity_text = ui.render(
            f"IMMUNITY: {player.final_immunity}",
            True,
            (225, 225, 220)
        )
        screen.blit(
            immunity_text,
            (30, 60)
        )

        if final_battle_reloading:
            reload_text = ui.render(
                "RELOADING...",
                True,
                (225, 183, 58)
            )
            screen.blit(
                reload_text,
                (30, 100)
            )

        ammo_text = ui.render(
            f"AMMO: {final_battle_ammo}/50",
            True,
            (225, 225, 220)
        )
        screen.blit(
            ammo_text,
            (WIDTH - 190, 25)
        )

        screen.blit(
            small.render(
                "WASD / ARROWS  MOVE     LMB  FIRE     R  RELOAD",
                True,
                (170, 175, 180)
            ),
            (20, HEIGHT - 30)
        )

    # =====================================================
    # FINAL SHOT PROMPT DRAW
    # =====================================================

    elif scene == "FINAL_SHOT_PROMPT":
        screen.fill((5, 6, 8))

        # Show the defeated best friend in the final arena.
        final_boss.draw(screen, final_battle_camera)

        # Dark cinematic overlay.
        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 155))
        screen.blit(overlay, (0, 0))

        title_font = pygame.font.Font(None, 52)
        body_font = pygame.font.Font(None, 26)
        button_font = pygame.font.Font(None, 34)
        small_font = pygame.font.Font(None, 20)

        title = title_font.render(
            "THE FINAL SHOT",
            True,
            (225, 183, 58)
        )
        screen.blit(
            title,
            title.get_rect(
                center=(WIDTH // 2, 170)
            )
        )

        body = body_font.render(
            "Your best friend is still alive.",
            True,
            (238, 240, 238)
        )
        screen.blit(
            body,
            body.get_rect(
                center=(WIDTH // 2, 230)
            )
        )

        sub = body_font.render(
            "End his suffering.",
            True,
            (180, 185, 188)
        )
        screen.blit(
            sub,
            sub.get_rect(
                center=(WIDTH // 2, 265)
            )
        )

        # Professional button with hover state.
        hovered = final_shot_button.collidepoint(
            pygame.mouse.get_pos()
        )

        button_color = (
            (190, 55, 50)
            if hovered
            else (145, 43, 40)
        )

        pygame.draw.rect(
            screen,
            (0, 0, 0),
            final_shot_button.move(0, 6),
            border_radius=10
        )
        pygame.draw.rect(
            screen,
            button_color,
            final_shot_button,
            border_radius=10
        )
        pygame.draw.rect(
            screen,
            (235, 210, 170),
            final_shot_button,
            2,
            border_radius=10
        )

        button_text = button_font.render(
            "SHOOT",
            True,
            (250, 245, 235)
        )
        screen.blit(
            button_text,
            button_text.get_rect(
                center=final_shot_button.center
            )
        )

        hint = small_font.render(
            "Click SHOOT to play the final-shot cinematic",
            True,
            (155, 160, 165)
        )
        screen.blit(
            hint,
            hint.get_rect(
                center=(WIDTH // 2, HEIGHT - 48)
            )
        )

    # =====================================================
    # FINAL SHOT VIDEO DRAW
    # =====================================================

    elif scene == "FINAL_SHOT_VIDEO":
        if final_shot_video is not None:
            final_shot_video.draw(screen)

            if final_shot_video.error:
                overlay = pygame.Surface(
                    (WIDTH, HEIGHT),
                    pygame.SRCALPHA
                )
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))

                f1 = pygame.font.Font(None, 40)
                f2 = pygame.font.Font(None, 24)

                screen.blit(
                    f1.render(
                        "FINAL SHOT VIDEO NOT READY",
                        True,
                        (225, 183, 58)
                    ),
                    f1.render(
                        "FINAL SHOT VIDEO NOT READY",
                        True,
                        (225, 183, 58)
                    ).get_rect(
                        center=(WIDTH // 2, HEIGHT // 2 - 35)
                    )
                )

                screen.blit(
                    f2.render(
                        final_shot_video.error,
                        True,
                        (235, 235, 230)
                    ),
                    f2.render(
                        final_shot_video.error,
                        True,
                        (235, 235, 230)
                    ).get_rect(
                        center=(WIDTH // 2, HEIGHT // 2 + 15)
                    )
                )

                screen.blit(
                    f2.render(
                        "Add ending/final_shot.mp4 and click SHOOT again.",
                        True,
                        (170, 175, 180)
                    ),
                    f2.render(
                        "Add ending/final_shot.mp4 and click SHOOT again.",
                        True,
                        (170, 175, 180)
                    ).get_rect(
                        center=(WIDTH // 2, HEIGHT // 2 + 55)
                    )
                )

    # =====================================================
    # FINAL CAMPUS ENDING DRAW
    # =====================================================

    elif scene == "FINAL_ENDING":
        # The actual campus is shown behind the survivors.
        campus.draw(
            screen,
            final_ending_camera
        )

        # Dark cinematic grading.
        grade = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )
        grade.fill((8, 10, 12, 45))
        screen.blit(grade, (0, 0))

        # Survivors walk out through the Main Gate and then stop outside.
        for index, character in enumerate(final_ending_group):
            character.draw(
                screen,
                final_ending_camera,
                selected=(index == 0)
            )

        # Cinematic caption while the group settles outside the gate.
        if final_ending_timer < FINAL_ENDING_WALK_DURATION:
            caption = pygame.font.Font(None, 25).render(
                "THE SURVIVORS LEAVE THE CAMPUS",
                True,
                (235, 232, 220)
            )
            screen.blit(
                caption,
                caption.get_rect(
                    center=(WIDTH // 2, HEIGHT - 45)
                )
            )
        elif final_ending_timer < FINAL_ENDING_FADE_START:
            caption = pygame.font.Font(None, 25).render(
                "ONE LAST LOOK AT THE COLLEGE",
                True,
                (220, 220, 212)
            )
            screen.blit(
                caption,
                caption.get_rect(
                    center=(WIDTH // 2, HEIGHT - 45)
                )
            )

        # Final cinematic fade to black.
        if final_ending_fade_alpha > 0:
            fade = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )
            fade.fill(
                (0, 0, 0, final_ending_fade_alpha)
            )
            screen.blit(fade, (0, 0))

    # =====================================================
    # LEGACY FINAL TITLE DRAW
    # =====================================================

    elif scene == "FINAL_TITLE":
        screen.fill((0, 0, 0))

    # =====================================================
    # MECHANICAL BLOCK DRAW
    # =====================================================

    elif scene == "MECHANICAL_BLOCK":

        mechanical_block.draw(
            screen,
            mechanical_camera
        )

        mechanical_combat.draw(
            screen,
            mechanical_camera
        )

        player.draw(
            screen,
            mechanical_camera
        )

        if not mechanical_combat.chapter_complete:
            viveka_campus.draw(
                screen,
                mechanical_camera
            )

        mechanical_ui.draw(
            screen,
            mechanical_combat
        )

        # -------------------------------------------------
        # CORRECT MECHANICAL AMMO DISPLAY
        # -------------------------------------------------
        # mechanical_ui.py still contains the old visual text "/12".
        # Keep the existing UI module untouched and redraw only this
        # panel from main.py so the player sees the real 50-round magazine.
        ammo_panel = pygame.Rect(
            WIDTH - 245,
            HEIGHT - 100,
            225,
            80
        )

        pygame.draw.rect(
            screen,
            (7, 10, 13),
            ammo_panel,
            border_radius=10
        )

        pygame.draw.rect(
            screen,
            (105, 96, 76),
            ammo_panel,
            2,
            border_radius=10
        )

        ammo_font = pygame.font.Font(None, 40)
        ammo_text = ammo_font.render(
            f"{mechanical_combat.ammo:02d}/{MECHANICAL_MAGAZINE_SIZE}",
            True,
            (239, 222, 183)
        )

        screen.blit(
            ammo_text,
            (
                ammo_panel.x + 15,
                ammo_panel.y + 9
            )
        )

        reload_text = (
            f"RELOADING  {max(0, mechanical_combat.reload_timer):.1f}s"
            if mechanical_combat.reloading
            else "R  RELOAD"
        )

        reload_font = pygame.font.Font(None, 18)
        reload_surface = reload_font.render(
            reload_text,
            True,
            (225, 179, 72)
            if mechanical_combat.reloading
            else (160, 166, 163)
        )

        screen.blit(
            reload_surface,
            (
                ammo_panel.x + 15,
                ammo_panel.y + 51
            )
        )

        # -------------------------------------------------
        # RESPAWN MESSAGE
        # -------------------------------------------------
        if (
            not mechanical_player_dead
            and mechanical_death_message_timer > 0
        ):
            mechanical_death_message_timer = max(
                0.0,
                mechanical_death_message_timer - 1 / FPS
            )

            message_font = pygame.font.Font(None, 28)
            message = message_font.render(
                f"HERO DEFEATED  •  RESPAWNS LEFT "
                f"{mechanical_combat.respawns_left}/3",
                True,
                (245, 201, 55)
            )

            message_rect = message.get_rect(
                center=(WIDTH // 2, 145)
            )

            screen.blit(
                message,
                message_rect
            )

        # -------------------------------------------------
        # HERO GAME OVER
        # -------------------------------------------------
        if mechanical_player_dead:
            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill((0, 0, 0, 175))
            screen.blit(overlay, (0, 0))

            game_over_box = pygame.Rect(
                300,
                205,
                680,
                300
            )

            pygame.draw.rect(
                screen,
                (7, 10, 13),
                game_over_box,
                border_radius=14
            )

            pygame.draw.rect(
                screen,
                (225, 75, 60),
                game_over_box,
                3,
                border_radius=14
            )

            game_over_title_font = pygame.font.Font(
                None,
                48
            )

            game_over_body_font = pygame.font.Font(
                None,
                26
            )

            game_over_hint_font = pygame.font.Font(
                None,
                22
            )

            game_over_title = game_over_title_font.render(
                "HERO DOWN",
                True,
                (235, 80, 65)
            )

            game_over_body = game_over_body_font.render(
                "The infected students overwhelmed you.",
                True,
                (240, 240, 235)
            )

            game_over_stage = game_over_body_font.render(
                f"Mechanical Block  •  Stage "
                f"{mechanical_combat.stage}",
                True,
                (190, 195, 192)
            )

            game_over_hint = game_over_hint_font.render(
                "PRESS ENTER TO RETRY",
                True,
                (245, 201, 55)
            )

            screen.blit(
                game_over_title,
                game_over_title.get_rect(
                    center=(game_over_box.centerx, game_over_box.y + 65)
                )
            )

            screen.blit(
                game_over_body,
                game_over_body.get_rect(
                    center=(game_over_box.centerx, game_over_box.y + 130)
                )
            )

            screen.blit(
                game_over_stage,
                game_over_stage.get_rect(
                    center=(game_over_box.centerx, game_over_box.y + 170)
                )
            )

            screen.blit(
                game_over_hint,
                game_over_hint.get_rect(
                    center=(game_over_box.centerx, game_over_box.y + 235)
                )
            )

        # -------------------------------------------------
        # MECHANICAL INTRO DIALOGUE
        # -------------------------------------------------

        if mechanical_intro_active:

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 135)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            box = pygame.Rect(
                110,
                HEIGHT - 205,
                WIDTH - 220,
                165
            )

            pygame.draw.rect(
                screen,
                (10, 14, 17),
                box,
                border_radius=10
            )

            pygame.draw.rect(
                screen,
                (245, 201, 55),
                box,
                2,
                border_radius=10
            )

            speaker, line = mechanical_intro[
                mechanical_intro_index
            ]

            speaker_font = pygame.font.Font(
                None,
                30
            )

            line_font = pygame.font.Font(
                None,
                25
            )

            hint_font = pygame.font.Font(
                None,
                20
            )

            speaker_surface = speaker_font.render(
                speaker,
                True,
                (245, 201, 55)
            )

            screen.blit(
                speaker_surface,
                (
                    box.x + 22,
                    box.y + 16
                )
            )

            line_surface = line_font.render(
                line,
                True,
                (240, 240, 235)
            )

            screen.blit(
                line_surface,
                (
                    box.x + 22,
                    box.y + 58
                )
            )

            hint = hint_font.render(
                "Press E to continue",
                True,
                (170, 180, 180)
            )

            screen.blit(
                hint,
                (
                    box.right - hint.get_width() - 22,
                    box.bottom - 28
                )
            )

        # -------------------------------------------------
        # STAGE COMPLETE
        # -------------------------------------------------

        elif (
            mechanical_combat_started
            and mechanical_combat.stage_complete
            and not mechanical_combat.chapter_complete
        ):

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 105)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            panel = pygame.Rect(
                300,
                240,
                680,
                210
            )

            pygame.draw.rect(
                screen,
                (8, 13, 16),
                panel,
                border_radius=12
            )

            pygame.draw.rect(
                screen,
                (110, 230, 125),
                panel,
                3,
                border_radius=12
            )

            title_font = pygame.font.Font(
                None,
                44
            )

            body_font = pygame.font.Font(
                None,
                24
            )

            title = title_font.render(
                f"STAGE {mechanical_combat.stage} SECURED",
                True,
                (110, 230, 125)
            )

            body = body_font.render(
                "All infected students in this stage are defeated.",
                True,
                (240, 240, 235)
            )

            if mechanical_combat.stage < 3:
                next_text = (
                    f"PRESS E  •  START STAGE "
                    f"{mechanical_combat.stage + 1}"
                )
            else:
                next_text = (
                    "PRESS E  •  SECURE THE BLOCK"
                )

            next_surface = body_font.render(
                next_text,
                True,
                (245, 201, 55)
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(
                        panel.centerx,
                        panel.y + 55
                    )
                )
            )

            screen.blit(
                body,
                body.get_rect(
                    center=(
                        panel.centerx,
                        panel.y + 110
                    )
                )
            )

            screen.blit(
                next_surface,
                next_surface.get_rect(
                    center=(
                        panel.centerx,
                        panel.y + 160
                    )
                )
            )

        # -------------------------------------------------
        # FINAL RESCUED STUDENTS DIALOGUE
        # -------------------------------------------------

        if mechanical_students_dialogue_active:

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 125)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            box = pygame.Rect(
                110,
                HEIGHT - 205,
                WIDTH - 220,
                165
            )

            pygame.draw.rect(
                screen,
                (10, 14, 17),
                box,
                border_radius=10
            )

            pygame.draw.rect(
                screen,
                (110, 230, 125),
                box,
                2,
                border_radius=10
            )

            speaker, line = mechanical_students_dialogue[
                mechanical_students_dialogue_index
            ]

            speaker_font = pygame.font.Font(
                None,
                30
            )

            line_font = pygame.font.Font(
                None,
                25
            )

            hint_font = pygame.font.Font(
                None,
                20
            )

            speaker_surface = speaker_font.render(
                speaker,
                True,
                (110, 230, 125)
            )

            screen.blit(
                speaker_surface,
                (
                    box.x + 22,
                    box.y + 16
                )
            )

            line_surface = line_font.render(
                line,
                True,
                (240, 240, 235)
            )

            screen.blit(
                line_surface,
                (
                    box.x + 22,
                    box.y + 58
                )
            )

            hint = hint_font.render(
                "Press E to continue",
                True,
                (170, 180, 180)
            )

            screen.blit(
                hint,
                (
                    box.right - hint.get_width() - 22,
                    box.bottom - 28
                )
            )

        # -------------------------------------------------
        # MECHANICAL BLOCK COMPLETE
        # -------------------------------------------------

        if (
            mechanical_checkpoint
            and not mechanical_students_dialogue_active
        ):

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 100)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            panel = pygame.Rect(
                280,
                235,
                720,
                230
            )

            pygame.draw.rect(
                screen,
                (8, 13, 16),
                panel,
                border_radius=12
            )

            pygame.draw.rect(
                screen,
                (110, 230, 125),
                panel,
                3,
                border_radius=12
            )

            title_font = pygame.font.Font(
                None,
                48
            )

            body_font = pygame.font.Font(
                None,
                25
            )

            title = title_font.render(
                "MECHANICAL BLOCK SECURED",
                True,
                (110, 230, 125)
            )

            body = body_font.render(
                "All infected students have been defeated.",
                True,
                (240, 240, 235)
            )

            next_text = body_font.render(
                "STUDENTS RESCUED  •  NEXT: LIBRARY",
                True,
                (245, 201, 55)
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(
                        panel.centerx,
                        panel.y + 62
                    )
                )
            )

            screen.blit(
                body,
                body.get_rect(
                    center=(
                        panel.centerx,
                        panel.y + 125
                    )
                )
            )

            screen.blit(
                next_text,
                next_text.get_rect(
                    center=(
                        panel.centerx,
                        panel.y + 175
                    )
                )
            )

    # =====================================================
    # GAME START INTRO VIDEO DRAW
    # =====================================================

    if scene == "GAME_INTRO":
        if game_intro_first_frame is not None:
            screen.blit(game_intro_first_frame, (0, 0))
        else:
            screen.fill((0, 0, 0))

            f = pygame.font.Font(None, 28)
            msg = f.render(
                game_intro_error or "Intro frame unavailable.",
                True,
                (235, 235, 235)
            )
            screen.blit(
                msg,
                msg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            )

    elif scene == "GAME_INTRO_VIDEO":
        # VLC owns the Pygame window while the intro is playing.
        if game_intro_video is not None:
            game_intro_video.draw(screen)

    # =====================================================
    # TRANSITION OVERLAY
    # =====================================================

    transition.draw(
        screen
    )

    # =====================================================
    # OPENING CINEMATIC TEXT
    # =====================================================

    if scene == "INTRO_BUS":

        title_font = pygame.font.Font(
            None,
            42
        )

        text_font = pygame.font.Font(
            None,
            24
        )

        title = title_font.render(
            "CAMPUS OUTBREAK",
            True,
            (235, 235, 230)
        )

        subtitle = text_font.render(
            "Pragati Engineering College  •  10:47 PM",
            True,
            (170, 180, 190)
        )

        screen.blit(
            title,
            title.get_rect(
                center=(WIDTH // 2, HEIGHT - 105)
            )
        )

        screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(WIDTH // 2, HEIGHT - 68)
            )
        )

    elif scene == "INTRO_REVEAL":

        # Clean cinematic frame. The actual story is delivered
        # after the player names are entered.
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (0, 0, WIDTH, 82)
        )

        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (0, HEIGHT - 82, WIDTH, 82)
        )


    # =========================================================
    # CINEMATIC NAME INPUT / STORY
    # =========================================================

    if scene == "INTRO_DIALOGUE" and intro_dialogue_active:

        # Strong cinematic focus.
        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 115)
        )

        screen.blit(
            overlay,
            (0, 0)
        )

        card_width = 800
        card_height = 210

        card = pygame.Rect(
            (WIDTH - card_width) // 2,
            (HEIGHT - card_height) // 2,
            card_width,
            card_height
        )

        # Shadow.
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            card.move(0, 9),
            border_radius=16
        )

        pygame.draw.rect(
            screen,
            (10, 14, 18),
            card,
            border_radius=16
        )

        pygame.draw.rect(
            screen,
            (90, 100, 108),
            card,
            2,
            border_radius=16
        )

        pygame.draw.rect(
            screen,
            (225, 183, 58),
            (
                card.x,
                card.y,
                card.width,
                5
            ),
            border_radius=4
        )

        speaker, line = intro_dialogue[
            intro_dialogue_index
        ]

        speaker_font = pygame.font.Font(
            None,
            31
        )

        line_font = pygame.font.Font(
            None,
            28
        )

        hint_font = pygame.font.Font(
            None,
            18
        )

        speaker_surface = speaker_font.render(
            speaker,
            True,
            (225, 183, 58)
        )

        screen.blit(
            speaker_surface,
            (
                card.x + 30,
                card.y + 25
            )
        )

        # Wrap line.
        words = line.split()
        wrapped = []
        current = ""

        for word in words:

            candidate = (
                current + " " + word
            ).strip()

            if (
                line_font.size(candidate)[0]
                > card.width - 60
            ):
                wrapped.append(current)
                current = word
            else:
                current = candidate

        if current:
            wrapped.append(current)

        for index, wrapped_line in enumerate(wrapped):

            surface = line_font.render(
                wrapped_line,
                True,
                (238, 240, 238)
            )

            screen.blit(
                surface,
                surface.get_rect(
                    center=(
                        card.centerx,
                        card.y + 92 + index * 34
                    )
                )
            )

        hint = hint_font.render(
            "E  CONTINUE",
            True,
            (145, 152, 156)
        )

        screen.blit(
            hint,
            (
                card.right - hint.get_width() - 26,
                card.bottom - 29
            )
        )


        # BENTO-STYLE LOCATION CARD
        bento = pygame.Rect(28, 28, 360, 92)

        pygame.draw.rect(
            screen, (7, 11, 15), bento, border_radius=14
        )
        pygame.draw.rect(
            screen, (82, 92, 100), bento, 2, border_radius=14
        )
        pygame.draw.rect(
            screen, (225, 183, 58),
            (bento.x, bento.y, 5, bento.height),
            border_radius=4
        )

        eyebrow_font = pygame.font.Font(None, 18)
        title_font = pygame.font.Font(None, 28)

        eyebrow = eyebrow_font.render(
            "LOCATION  //  CAMPUS", True, (145, 155, 160)
        )
        title = title_font.render(
            "PRAGATI ENGINEERING", True, (242, 242, 236)
        )
        subtitle = eyebrow_font.render(
            "COLLEGE", True, (225, 183, 58)
        )

        screen.blit(eyebrow, (bento.x + 20, bento.y + 13))
        screen.blit(title, (bento.x + 20, bento.y + 38))
        screen.blit(subtitle, (bento.x + 20, bento.y + 66))

    if scene == "CAMPUS" and gun_picked:

        hint_font = pygame.font.Font(None, 22)

        hint = hint_font.render(
            "WASD / ARROWS  MOVE     E  INTERACT",
            True,
            (225, 230, 225)
        )

        shadow = hint_font.render(
            "WASD / ARROWS  MOVE     E  INTERACT",
            True,
            (10, 12, 14)
        )

        screen.blit(
            shadow,
            (22, HEIGHT - 32)
        )

        screen.blit(
            hint,
            (20, HEIGHT - 34)
        )

    elif scene == "MAIN_BLOCK":

        hint_font = pygame.font.Font(None, 22)

        hint = hint_font.render(
            "WASD / ARROWS  MOVE     E  INVESTIGATE",
            True,
            (225, 230, 225)
        )

        shadow = hint_font.render(
            "WASD / ARROWS  MOVE     E  INVESTIGATE",
            True,
            (10, 12, 14)
        )

        screen.blit(shadow, (22, HEIGHT - 32))
        screen.blit(hint, (20, HEIGHT - 34))

    elif scene == "RESEARCH_LIBRARY":

        hint_font = pygame.font.Font(None, 22)
        hint = hint_font.render("WASD / ARROWS  MOVE     E  ENTER HIDDEN DOOR", True, (225, 230, 225))
        screen.blit(hint, (20, HEIGHT - 34))

    elif scene == "RESEARCH_DEPARTMENT":

        hint_font = pygame.font.Font(None, 22)
        hint = hint_font.render("WASD / ARROWS  MOVE     LMB  FIRE     R  RELOAD     E  RESCUE / CONTINUE", True, (225, 230, 225))
        screen.blit(hint, (20, HEIGHT - 34))

    elif scene == "MECHANICAL_BLOCK":

        hint_font = pygame.font.Font(None, 22)

        hint = hint_font.render(
            "WASD / ARROWS  MOVE     LMB  FIRE     R  RELOAD     E  CONTINUE",
            True,
            (225, 230, 225)
        )

        shadow = hint_font.render(
            "WASD / ARROWS  MOVE     LMB  FIRE     R  RELOAD     E  CONTINUE",
            True,
            (10, 12, 14)
        )

        screen.blit(
            shadow,
            (22, HEIGHT - 32)
        )

        screen.blit(
            hint,
            (20, HEIGHT - 34)
        )

    elif scene == "LIBRARY":

        hint_font = pygame.font.Font(None, 22)

        hint = hint_font.render(
            "WASD / ARROWS  MOVE     LMB  FIRE     R  RELOAD",
            True,
            (225, 230, 225)
        )

        shadow = hint_font.render(
            "WASD / ARROWS  MOVE     LMB  FIRE     R  RELOAD",
            True,
            (10, 12, 14)
        )

        screen.blit(
            shadow,
            (22, HEIGHT - 32)
        )

        screen.blit(
            hint,
            (20, HEIGHT - 34)
        )

    pygame.display.flip()


# =========================================================
# SHUTDOWN
# =========================================================

if game_intro_video is not None:
    game_intro_video.stop()

pygame.quit()
sys.exit()
