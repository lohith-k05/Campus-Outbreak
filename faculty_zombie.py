import pygame


class FacultyZombie:
    """Large and fast infected faculty member. Requires 10 bullets."""

    def __init__(self, x, y, speed=118):
        self.x = float(x)
        self.y = float(y)
        self.width = 54
        self.height = 68
        self.rect = pygame.Rect(int(x), int(y), self.width, self.height)
        self.speed = speed
        self.max_health = 10
        self.health = 10
        self.alive = True
        self.attack_cooldown = 0.35
        self.attack_delay = 0.70
        self.attack_damage = 10
        self.animation = 0.0

    def update(self, player, dt, bounds, obstacles):
        if not self.alive:
            return
        self.animation += dt
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        target = pygame.Vector2(player.rect.centerx, player.rect.centery)
        current = pygame.Vector2(self.rect.center)
        direction = target - current
        distance = direction.length()
        if distance > 58:
            direction.normalize_ip()
            self._move(direction.x * self.speed * dt, 0, bounds, obstacles)
            self._move(0, direction.y * self.speed * dt, bounds, obstacles)
        elif self.attack_cooldown <= 0:
            if hasattr(player, "mechanical_immunity"):
                player.mechanical_immunity = max(0, player.mechanical_immunity - self.attack_damage)
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
        bob = -2 if int(self.animation * 6) % 2 else 0
        pygame.draw.ellipse(screen, (8, 8, 9), (x + 3, y + self.height - 5, self.width - 6, 14))
        pygame.draw.rect(screen, (38, 38, 43), (x + 9, y + 39 + bob, 13, 24))
        pygame.draw.rect(screen, (38, 38, 43), (x + 31, y + 39 + bob, 13, 24))
        pygame.draw.rect(screen, (15, 16, 18), (x + 5, y + 60 + bob, 18, 8))
        pygame.draw.rect(screen, (15, 16, 18), (x + 30, y + 60 + bob, 18, 8))
        body = pygame.Rect(x + 6, y + 18 + bob, 43, 28)
        pygame.draw.rect(screen, (68, 72, 78), body, border_radius=5)
        pygame.draw.rect(screen, (100, 105, 110), (body.x + 5, body.y + 3, 33, 21), border_radius=3)
        pygame.draw.polygon(screen, (65, 42, 45), [(x + 25, y + 23 + bob), (x + 31, y + 23 + bob), (x + 28, y + 39 + bob)])
        pygame.draw.rect(screen, (180, 125, 94), (x + 21, y + 12 + bob, 12, 10))
        head = pygame.Rect(x + 12, y - 1 + bob, 30, 27)
        pygame.draw.rect(screen, (172, 116, 89), head, border_radius=7)
        pygame.draw.rect(screen, (43, 43, 44), (head.x + 2, head.y, 26, 10), border_radius=6)
        pygame.draw.rect(screen, (214, 50, 45), (head.x + 6, head.y + 14, 5, 4))
        pygame.draw.rect(screen, (214, 50, 45), (head.x + 20, head.y + 14, 5, 4))
        pygame.draw.rect(screen, (13, 14, 15), (x, y - 13, self.width, 6))
        pygame.draw.rect(screen, (205, 54, 45), (x, y - 13, int(self.width * self.health / self.max_health), 6))