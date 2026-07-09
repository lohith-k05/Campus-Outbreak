import math
import random
import pygame


class ResearchBullet:
    def __init__(self, x, y, tx, ty, speed=720):
        self.pos = pygame.Vector2(x, y)
        direction = pygame.Vector2(tx - x, ty - y)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        self.velocity = direction.normalize() * speed
        self.radius = 4
        self.alive = True
        self.damage = 1

    def update(self, dt, bounds):
        if not self.alive:
            return
        self.pos += self.velocity * dt
        if not bounds.inflate(120, 120).collidepoint(self.pos.x, self.pos.y):
            self.alive = False

    def draw(self, screen, camera):
        if not self.alive:
            return
        pygame.draw.circle(
            screen,
            (248, 220, 120),
            (int(self.pos.x - camera.x), int(self.pos.y - camera.y)),
            self.radius,
        )


class ResearchDoctorZombie:
    """Single fast infected research doctor used only in the Research Department."""

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.width = 52
        self.height = 64
        self.rect = pygame.Rect(int(x), int(y), self.width, self.height)
        self.speed = 145
        self.max_health = 10
        self.health = 10
        self.alive = True
        self.attack_cooldown = 0.7
        self.attack_delay = 0.65
        self.attack_damage = 10
        self.animation = random.random() * 10
        self.hit_flash = 0.0

    def update(self, player, dt, bounds, obstacles):
        if not self.alive:
            return

        self.animation += dt
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)

        target = pygame.Vector2(player.rect.center)
        current = pygame.Vector2(self.rect.center)
        direction = target - current
        distance = direction.length()

        if distance > 62:
            direction.normalize_ip()
            self._move(direction.x * self.speed * dt, 0, bounds, obstacles)
            self._move(0, direction.y * self.speed * dt, bounds, obstacles)
        elif self.attack_cooldown <= 0:
            if hasattr(player, "research_immunity"):
                player.research_immunity = max(
                    0, player.research_immunity - self.attack_damage
                )
            self.attack_cooldown = self.attack_delay

        self.rect.topleft = (round(self.x), round(self.y))

    def _move(self, dx, dy, bounds, obstacles):
        test = self.rect.move(round(dx), round(dy))
        if not bounds.contains(test):
            return
        for obstacle in obstacles:
            if test.colliderect(obstacle):
                return
        self.x += dx
        self.y += dy

    def take_damage(self, damage=1):
        if not self.alive:
            return False
        self.health -= damage
        self.hit_flash = 0.08
        if self.health <= 0:
            self.health = 0
            self.alive = False
            return True
        return False

    def draw(self, screen, camera):
        if not self.alive:
            return

        x = int(self.rect.x - camera.x)
        y = int(self.rect.y - camera.y)
        bob = -2 if int(self.animation * 7) % 2 else 0

        pygame.draw.ellipse(screen, (8, 9, 10), (x + 3, y + 52, 46, 13))

        coat = (238, 238, 230) if self.hit_flash <= 0 else (255, 120, 105)
        coat_dark = (165, 168, 170)
        skin = (188, 143, 112)
        hair = (42, 35, 32)

        # Legs
        pygame.draw.rect(screen, (40, 43, 47), (x + 9, y + 43 + bob, 11, 19))
        pygame.draw.rect(screen, (40, 43, 47), (x + 32, y + 43 + bob, 11, 19))

        # Lab coat
        pygame.draw.rect(screen, coat_dark, (x + 4, y + 17 + bob, 44, 31), border_radius=5)
        pygame.draw.rect(screen, coat, (x + 7, y + 15 + bob, 38, 32), border_radius=5)

        # Shirt / ID badge
        pygame.draw.rect(screen, (45, 55, 70), (x + 20, y + 20 + bob, 12, 20))
        pygame.draw.rect(screen, (55, 120, 185), (x + 34, y + 25 + bob, 7, 9))

        # Head
        pygame.draw.circle(screen, skin, (x + 26, y + 8 + bob), 17)
        pygame.draw.rect(screen, hair, (x + 11, y - 7 + bob, 30, 10), border_radius=5)

        # Infected eyes
        pygame.draw.circle(screen, (225, 45, 45), (x + 20, y + 7 + bob), 3)
        pygame.draw.circle(screen, (225, 45, 45), (x + 32, y + 7 + bob), 3)

        # Health bar
        bar_w = 64
        bar_x = x - 6
        bar_y = y - 19
        pygame.draw.rect(screen, (20, 20, 20), (bar_x, bar_y, bar_w, 6))
        pygame.draw.rect(
            screen,
            (210, 60, 60),
            (bar_x, bar_y, int(bar_w * self.health / self.max_health), 6),
        )


class ResearchDoctor:
    """Surviving researcher NPC."""

    def __init__(self, name, x, y, variant=0):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(int(x), int(y), 36, 48)
        self.variant = variant
        self.rescued = False
        self.follow_offset = pygame.Vector2(45 + variant * 42, 35 + variant * 20)

    def update_follow(self, target, dt, bounds):
        if not self.rescued:
            return
        desired = pygame.Vector2(
            target.rect.centerx + self.follow_offset.x,
            target.rect.centery + self.follow_offset.y,
        )
        direction = desired - pygame.Vector2(self.rect.center)
        if direction.length_squared() > 48 ** 2:
            direction.normalize_ip()
            self.rect.x += int(direction.x * 75 * dt)
            self.rect.y += int(direction.y * 75 * dt)
        self.rect.clamp_ip(bounds)

    def draw(self, screen, camera):
        x = int(self.rect.x - camera.x)
        y = int(self.rect.y - camera.y)
        color = (78, 145, 190) if self.variant == 0 else (105, 155, 105)

        pygame.draw.ellipse(screen, (8, 9, 10), (x + 2, y + 38, 32, 10))
        pygame.draw.rect(screen, (220, 220, 215), (x + 4, y + 13, 28, 27), border_radius=4)
        pygame.draw.rect(screen, color, (x + 9, y + 18, 18, 13), border_radius=3)
        pygame.draw.circle(screen, (190, 145, 112), (x + 18, y + 6), 13)
        pygame.draw.rect(screen, (45, 38, 34), (x + 7, y - 5, 22, 8), border_radius=4)
        pygame.draw.rect(screen, (50, 110, 165), (x + 23, y + 20, 5, 7))

        font = pygame.font.Font(None, 18)
        label = font.render(self.name, True, (235, 235, 230))
        screen.blit(label, label.get_rect(center=(x + 18, y - 18)))


class ResearchDepartment:
    """Single-combat underground Research Department chapter."""

    WIDTH = 1700
    HEIGHT = 1050

    def __init__(self, camera_cls, screen_width, screen_height):
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.bounds = pygame.Rect(50, 50, self.width - 100, self.height - 100)
        self.obstacles = [
            pygame.Rect(250, 220, 280, 42),
            pygame.Rect(720, 220, 300, 42),
            pygame.Rect(1180, 220, 250, 42),
            pygame.Rect(300, 620, 250, 42),
            pygame.Rect(760, 620, 300, 42),
            pygame.Rect(1220, 620, 260, 42),
            pygame.Rect(560, 385, 120, 180),
            pygame.Rect(1080, 385, 120, 180),
        ]
        self.camera = camera_cls(screen_width, screen_height, self.width, self.height)
        self.entry_point = (130, 500)
        self.doctor_spawn = (1370, 470)
        self.doctors = [
            ResearchDoctor("Dr. Rao", 480, 830, 0),
            ResearchDoctor("Dr. Meera", 1010, 830, 1),
        ]
        self.doctor_zombie = None
        self.bullets = []
        self.ammo = 50
        self.magazine_size = 50
        self.reload_duration = 1.0
        self.reload_timer = 0.0
        self.reloading = False
        self.fire_cooldown = 0.0
        self.fire_delay = 0.14
        self.immunity = 100
        self.max_immunity = 100
        self.started = False
        self.combat_started = False
        self.combat_complete = False
        self.player_dead = False
        self.rescued_count = 0
        self.dialogue_active = False
        self.dialogue_index = 0
        self.complete = False
        self.message = ""

        self.dialogue = [
            ("Dr. Rao", "Thank you. We thought we were trapped down here."),
            ("Dr. Meera", "The outbreak began after something failed inside this facility."),
            ("Dr. Rao", "There may still be a way to stop the infection."),
            ("Hero", "Then we find it. We need to know the truth."),
        ]

    @property
    def collision(self):
        return self.obstacles

    def reset(self, player):
        self.bullets.clear()
        self.ammo = self.magazine_size
        self.reload_timer = 0.0
        self.reloading = False
        self.fire_cooldown = 0.0
        self.immunity = self.max_immunity
        self.started = True
        self.combat_started = True
        self.combat_complete = False
        self.player_dead = False
        self.rescued_count = 0
        self.dialogue_active = False
        self.dialogue_index = 0
        self.complete = False
        self.message = "KILL THE INFECTED DOCTOR"
        self.doctor_zombie = ResearchDoctorZombie(*self.doctor_spawn)
        for doctor, pos in zip(self.doctors, [(480, 830), (1010, 830)]):
            doctor.rect.topleft = pos
            doctor.rescued = False
        player.research_immunity = self.max_immunity
        player.direction = "right"
        player.walking = False

    def start_reload(self):
        if not self.reloading and self.ammo < self.magazine_size:
            self.reloading = True
            self.reload_timer = self.reload_duration

    def shoot(self, player, target_x, target_y):
        if not self.started or self.player_dead or self.combat_complete:
            return
        if self.reloading or self.fire_cooldown > 0:
            return
        if self.ammo <= 0:
            self.start_reload()
            return

        self.bullets.append(
            ResearchBullet(
                player.rect.centerx,
                player.rect.centery,
                target_x,
                target_y,
            )
        )
        self.ammo -= 1
        self.fire_cooldown = self.fire_delay
        if self.ammo == 0:
            self.start_reload()

    def update(self, player, dt):
        if not self.started or self.player_dead:
            return

        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

        if self.reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.reload_timer = 0.0
                self.reloading = False
                self.ammo = self.magazine_size

        if not self.combat_complete:
            for bullet in self.bullets:
                bullet.update(dt, self.bounds)

            if self.doctor_zombie and self.doctor_zombie.alive:
                self.doctor_zombie.update(player, dt, self.bounds, self.obstacles)

            for bullet in self.bullets:
                if not bullet.alive or not self.doctor_zombie or not self.doctor_zombie.alive:
                    continue
                if self.doctor_zombie.rect.collidepoint(int(bullet.pos.x), int(bullet.pos.y)):
                    bullet.alive = False
                    if self.doctor_zombie.take_damage(bullet.damage):
                        self.combat_complete = True
                        self.message = "DOCTOR ZOMBIE DEFEATED  •  RESCUE THE RESEARCH DOCTORS"
                        self.bullets.clear()

            self.bullets = [b for b in self.bullets if b.alive]

        for doctor in self.doctors:
            doctor.update_follow(player, dt, self.bounds)

    def interact_doctor(self, player):
        if not self.combat_complete or self.dialogue_active:
            return
        for doctor in self.doctors:
            if not doctor.rescued and player.near(doctor.rect):
                doctor.rescued = True
                self.rescued_count += 1
                if self.rescued_count >= 2:
                    self.dialogue_active = True
                    self.dialogue_index = 0
                    self.message = "RESEARCH TEAM RESCUED"
                return

    def advance_dialogue(self):
        if not self.dialogue_active:
            return
        self.dialogue_index += 1
        if self.dialogue_index >= len(self.dialogue):
            self.dialogue_active = False
            self.complete = True
            self.message = "NEXT OBJECTIVE  •  FIND THE CURE"

    def draw(self, screen):
        camera = self.camera
        screen.fill((10, 13, 16))
        ox, oy = int(camera.x), int(camera.y)

        floor = pygame.Rect(50 - ox, 50 - oy, self.width - 100, self.height - 100)
        pygame.draw.rect(screen, (29, 34, 38), floor)

        # Laboratory floor grid.
        for x in range(60, self.width - 40, 55):
            pygame.draw.line(screen, (39, 44, 48), (x - ox, 55 - oy), (x - ox, self.height - 55 - oy))
        for y in range(60, self.height - 40, 55):
            pygame.draw.line(screen, (39, 44, 48), (55 - ox, y - oy), (self.width - 55 - ox, y - oy))

        # Outer walls.
        pygame.draw.rect(screen, (15, 18, 21), (50 - ox, 50 - oy, self.width - 100, 38), border_radius=4)
        pygame.draw.rect(screen, (15, 18, 21), (50 - ox, self.height - 88 - oy, self.width - 100, 38), border_radius=4)
        pygame.draw.rect(screen, (15, 18, 21), (50 - ox, 50 - oy, 38, self.height - 100), border_radius=4)
        pygame.draw.rect(screen, (15, 18, 21), (self.width - 88 - ox, 50 - oy, 38, self.height - 100), border_radius=4)

        # Lab stations / glass cabinets.
        for i, r in enumerate(self.obstacles):
            rr = r.move(-ox, -oy)
            pygame.draw.rect(screen, (18, 55, 66), rr, border_radius=4)
            pygame.draw.rect(screen, (65, 150, 165), rr, 2, border_radius=4)
            pygame.draw.rect(screen, (80, 175, 190), (rr.x + 12, rr.y + 9, rr.width - 24, 7), border_radius=3)
            if i % 2 == 0:
                pygame.draw.circle(screen, (120, 210, 190), (rr.centerx, rr.centery + 8), 7)

        # Research signage.
        font = pygame.font.Font(None, 25)
        label = font.render("RESEARCH DEPARTMENT  //  BIOLOGICAL LAB", True, (110, 185, 200))
        screen.blit(label, (105 - ox, 108 - oy))

        warning = font.render("BIOLOGICAL CONTAINMENT", True, (205, 70, 65))
        screen.blit(warning, (1120 - ox, 120 - oy))

        for doctor in self.doctors:
            doctor.draw(screen, camera)

        if self.doctor_zombie and self.doctor_zombie.alive:
            self.doctor_zombie.draw(screen, camera)

        for bullet in self.bullets:
            bullet.draw(screen, camera)

        # UI card.
        panel = pygame.Rect(20, 18, 420, 115)
        pygame.draw.rect(screen, (7, 11, 14), panel, border_radius=12)
        pygame.draw.rect(screen, (85, 145, 165), panel, 2, border_radius=12)
        title = pygame.font.Font(None, 28)
        small = pygame.font.Font(None, 20)
        screen.blit(title.render("RESEARCH DEPARTMENT", True, (150, 205, 215)), (panel.x + 16, panel.y + 12))
        screen.blit(small.render(self.message, True, (235, 235, 230)), (panel.x + 16, panel.y + 50))
        screen.blit(small.render(f"IMMUNITY  {self.immunity}/100", True, (220, 100, 90) if self.immunity < 35 else (120, 220, 135)), (panel.x + 16, panel.y + 78))

        ammo = pygame.Rect(screen.get_width() - 235, screen.get_height() - 95, 215, 76)
        pygame.draw.rect(screen, (7, 11, 14), ammo, border_radius=10)
        pygame.draw.rect(screen, (100, 145, 160), ammo, 2, border_radius=10)
        screen.blit(title.render(f"{self.ammo:02d}/{self.magazine_size}", True, (235, 225, 195)), (ammo.x + 14, ammo.y + 9))
        reload_text = f"RELOADING {max(0, self.reload_timer):.1f}s" if self.reloading else "R  RELOAD"
        screen.blit(small.render(reload_text, True, (225, 180, 75)), (ammo.x + 14, ammo.y + 48))

        if self.dialogue_active:
            self.draw_dialogue(screen)

        if self.complete and not self.dialogue_active:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 85))
            screen.blit(overlay, (0, 0))
            f = pygame.font.Font(None, 40)
            t = f.render("RESEARCH TEAM RESCUED", True, (120, 225, 150))
            screen.blit(t, t.get_rect(center=(screen.get_width() // 2, 170)))
            f2 = pygame.font.Font(None, 25)
            n = f2.render("NEXT OBJECTIVE  •  FIND THE CURE", True, (245, 201, 55))
            screen.blit(n, n.get_rect(center=(screen.get_width() // 2, 215)))

    def draw_dialogue(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 135))
        screen.blit(overlay, (0, 0))
        box = pygame.Rect(100, screen.get_height() - 205, screen.get_width() - 200, 165)
        pygame.draw.rect(screen, (8, 12, 15), box, border_radius=12)
        pygame.draw.rect(screen, (110, 190, 205), box, 2, border_radius=12)
        speaker, line = self.dialogue[self.dialogue_index]
        sf = pygame.font.Font(None, 30)
        lf = pygame.font.Font(None, 25)
        hf = pygame.font.Font(None, 20)
        screen.blit(sf.render(speaker, True, (130, 205, 215)), (box.x + 22, box.y + 16))
        screen.blit(lf.render(line, True, (240, 240, 235)), (box.x + 22, box.y + 58))
        hint = hf.render("Press E to continue", True, (170, 180, 180))
        screen.blit(hint, (box.right - hint.get_width() - 22, box.bottom - 28))

    def draw_elevator(self, screen, timer):
        screen.fill((6, 7, 9))
        w, h = screen.get_size()
        # Elevator interior.
        pygame.draw.rect(screen, (31, 34, 38), (150, 70, w - 300, h - 140), border_radius=10)
        pygame.draw.rect(screen, (12, 14, 17), (180, 95, w - 360, h - 190), 5, border_radius=6)
        pygame.draw.line(screen, (85, 88, 92), (w // 2, 110), (w // 2, h - 110), 2)
        pygame.draw.rect(screen, (22, 24, 27), (w // 2 - 4, 130, 8, h - 260))

        # Moving light / subtle descent effect.
        pulse = int(30 + 18 * (0.5 + 0.5 * math.sin(timer * 5)))
        pygame.draw.rect(screen, (pulse, pulse + 5, pulse + 8), (235, 125, w - 470, 8), border_radius=4)

        big = pygame.font.Font(None, 44)
        small = pygame.font.Font(None, 25)
        screen.blit(big.render("RESEARCH ELEVATOR", True, (210, 215, 215)), big.render("RESEARCH ELEVATOR", True, (210, 215, 215)).get_rect(center=(w // 2, 185)))

        floors = ["GROUND", "B1", "B2", "RESEARCH"]
        idx = min(3, int(timer / 1.15))
        floor_text = small.render(floors[idx], True, (110, 215, 205))
        screen.blit(floor_text, floor_text.get_rect(center=(w // 2, 245)))

        if timer < 1.0:
            status = "DOORS CLOSING..."
        elif timer < 4.2:
            status = "DESCENDING..."
        else:
            status = "RESEARCH LEVEL"
        status_s = small.render(status, True, (190, 195, 195))
        screen.blit(status_s, status_s.get_rect(center=(w // 2, 575)))
