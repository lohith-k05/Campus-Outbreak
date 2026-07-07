import random
import pygame

from zombie import Bullet
from student_zombie import StudentZombie
from faculty_zombie import FacultyZombie
from npc import NPC


class LibraryBlock:
    def __init__(self):
        self.width = 1800
        self.height = 1100
        self.entry_point = (900, 970)
        self.player_bounds = pygame.Rect(55, 55, self.width - 110, self.height - 110)
        self.walls = [
            pygame.Rect(0, 0, self.width, 40),
            pygame.Rect(0, self.height - 40, self.width, 40),
            pygame.Rect(0, 0, 40, self.height),
            pygame.Rect(self.width - 40, 0, 40, self.height),
        ]
        self.obstacles = [
            pygame.Rect(300, 310, 280, 45), pygame.Rect(760, 310, 280, 45), pygame.Rect(1220, 310, 280, 45),
            pygame.Rect(300, 650, 280, 45), pygame.Rect(760, 650, 280, 45), pygame.Rect(1220, 650, 280, 45),
        ]
        self.racks = [
            pygame.Rect(90, 100, 90, 300), pygame.Rect(90, 500, 90, 300),
            pygame.Rect(1620, 100, 90, 300), pygame.Rect(1620, 500, 90, 300),
            pygame.Rect(270, 90, 280, 70), pygame.Rect(610, 90, 280, 70),
            pygame.Rect(950, 90, 280, 70), pygame.Rect(1290, 90, 280, 70),
            pygame.Rect(270, 940, 280, 70), pygame.Rect(610, 940, 280, 70),
            pygame.Rect(950, 940, 280, 70), pygame.Rect(1290, 940, 280, 70),
        ]
        self.story_rack = pygame.Rect(730, 470, 340, 72)
        self.hidden_door = pygame.Rect(835, 458, 130, 95)

    def get_collision_rects(self):
        return self.walls + self.obstacles + [r for r in self.racks if r != self.story_rack]

    def random_spawn_points(self):
        return [
            (130, 210), (250, 230), (520, 220), (900, 210), (1280, 220), (1570, 220),
            (190, 530), (470, 540), (690, 530), (1090, 540), (1370, 535), (1580, 540),
            (180, 850), (470, 830), (780, 850), (1110, 830), (1420, 850), (1580, 850),
        ]

    def draw(self, screen, camera, rack_fallen=False, door_revealed=False):
        screen.fill((24, 24, 25))
        ox, oy = int(camera.x), int(camera.y)
        floor = pygame.Rect(40 - ox, 40 - oy, self.width - 80, self.height - 80)
        pygame.draw.rect(screen, (45, 40, 36), floor)
        for x in range(60, self.width - 40, 70):
            pygame.draw.line(screen, (57, 51, 46), (x - ox, 45 - oy), (x - ox, self.height - 45 - oy), 1)
        for y in range(60, self.height - 40, 70):
            pygame.draw.line(screen, (57, 51, 46), (45 - ox, y - oy), (self.width - 45 - ox, y - oy), 1)
        for wall in self.walls:
            pygame.draw.rect(screen, (12, 14, 16), wall.move(-ox, -oy))
        for obstacle in self.obstacles:
            r = obstacle.move(-ox, -oy)
            pygame.draw.rect(screen, (72, 55, 43), r, border_radius=5)
            pygame.draw.rect(screen, (105, 78, 55), r.inflate(-8, -8), border_radius=3)
        for rack in self.racks:
            if rack != self.story_rack:
                self._rack(screen, rack.move(-ox, -oy))
        rack = self.story_rack.move(-ox, -oy)
        if rack_fallen:
            rack = pygame.Rect(rack.x - 18, rack.y + 80, rack.height, rack.width)
        self._rack(screen, rack)
        if door_revealed:
            d = self.hidden_door.move(-ox, -oy)
            pygame.draw.rect(screen, (7, 8, 10), d, border_radius=4)
            pygame.draw.rect(screen, (165, 138, 80), d, 2, border_radius=4)
            pygame.draw.circle(screen, (190, 155, 80), (d.right - 18, d.centery), 4)

    def _rack(self, screen, rect):
        pygame.draw.rect(screen, (67, 46, 32), rect, border_radius=4)
        pygame.draw.rect(screen, (103, 72, 48), rect.inflate(-8, -8), border_radius=3)
        if rect.width > rect.height:
            colors = [(78, 47, 45), (52, 65, 78), (73, 66, 46), (59, 76, 61), (78, 57, 73)]
            for x in range(rect.left + 10, rect.right - 8, 14):
                h = random.choice((28, 34, 40))
                pygame.draw.rect(screen, random.choice(colors), (x, rect.centery - h // 2, 10, h))
        else:
            for y in range(rect.top + 10, rect.bottom - 8, 14):
                pygame.draw.rect(screen, (65, 70, 75), (rect.centerx - 15, y, 30, 10))


class LibraryCombat:
    def __init__(self, block):
        self.block = block
        self.total = 25
        self.faculty_total = 7
        self.student_total = 18
        self.zombies = []
        self.bullets = []
        self.spawned = 0
        self.faculty_spawned = 0
        self.students_spawned = 0
        self.started = False
        self.complete = False
        self.magazine_size = 50
        self.ammo = 50
        self.reloading = False
        self.reload_timer = 0.0
        self.reload_duration = 1.0
        self.fire_cooldown = 0.0
        self.fire_delay = 0.13
        self.immunity = 100
        self.max_immunity = 100
        self.spawn_timer = 0.0
        self.spawn_interval = 1.1
        self.kills = 0
        self.points = block.random_spawn_points()

    def start(self):
        self.started = True
        self.complete = False
        self.zombies.clear(); self.bullets.clear()
        self.spawned = 0; self.faculty_spawned = 0; self.students_spawned = 0
        self.ammo = 50; self.reloading = False; self.reload_timer = 0
        self.fire_cooldown = 0; self.immunity = 100; self.spawn_timer = 0.8; self.kills = 0

    def reset(self):
        self.__init__(self.block)
        self.start()

    def start_reload(self):
        if not self.reloading and self.ammo < self.magazine_size:
            self.reloading = True
            self.reload_timer = 1.0

    def shoot(self, player, tx, ty):
        if not self.started or self.complete or self.reloading or self.fire_cooldown > 0:
            return
        if self.ammo <= 0:
            self.start_reload(); return
        dx, dy = tx - player.rect.centerx, ty - player.rect.centery
        player.direction = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) else ("down" if dy > 0 else "up")
        self.bullets.append(Bullet(player.rect.centerx, player.rect.centery, tx, ty))
        self.ammo -= 1
        self.fire_cooldown = self.fire_delay
        if self.ammo == 0: self.start_reload()

    def _spawn(self, player):
        if self.spawned >= self.total: return
        remaining_f = self.faculty_total - self.faculty_spawned
        use_faculty = remaining_f > 0 and (self.students_spawned >= 8 or random.random() < 0.32)
        if self.students_spawned >= self.student_total: use_faculty = True
        if use_faculty:
            x, y = random.choice(self.points); z = FacultyZombie(x, y, random.uniform(112, 125)); self.faculty_spawned += 1
        else:
            x, y = random.choice(self.points); z = StudentZombie(x, y, random.uniform(68, 82)); self.students_spawned += 1
        if z.rect.colliderect(player.rect.inflate(280, 280)):
            choices = [p for p in self.points if not pygame.Rect(p[0], p[1], z.width, z.height).colliderect(player.rect.inflate(280, 280))]
            if choices:
                x, y = random.choice(choices); z.x, z.y = float(x), float(y); z.rect.topleft = (x, y)
        self.zombies.append(z); self.spawned += 1

    def update(self, player, dt):
        if not self.started or self.complete: return
        self.fire_cooldown = max(0, self.fire_cooldown - dt)
        if self.reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.reloading = False; self.reload_timer = 0; self.ammo = 50
        if self.spawned < self.total:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0
                for _ in range(min(random.randint(2, 3), self.total - self.spawned)): self._spawn(player)
                self.spawn_interval = random.uniform(0.9, 1.6)
        player.mechanical_immunity = self.immunity
        for z in self.zombies: z.update(player, dt, self.block.player_bounds, self.block.get_collision_rects())
        self.immunity = max(0, min(100, player.mechanical_immunity))
        for b in self.bullets: b.update(dt)
        remaining = []
        for b in self.bullets:
            hit = False
            br = pygame.Rect(int(b.position.x - b.radius), int(b.position.y - b.radius), b.radius * 2, b.radius * 2)
            for z in self.zombies:
                if z.alive and br.colliderect(z.rect):
                    z.take_damage(1); hit = True
                    if not z.alive: self.kills += 1
                    break
            if not hit and b.life > 0: remaining.append(b)
        self.bullets = remaining
        self.zombies = [z for z in self.zombies if z.alive]
        if self.spawned >= self.total and not self.zombies:
            self.complete = True; self.started = False

    def draw(self, screen, camera):
        for b in self.bullets: b.draw(screen, camera)
        for z in self.zombies: z.draw(screen, camera)


class LibraryUI:
    def draw(self, screen, combat, rack_sequence, door_revealed, dialogue, dead):
        f1, f2, f3 = pygame.font.Font(None, 30), pygame.font.Font(None, 21), pygame.font.Font(None, 42)
        p = pygame.Rect(24, 24, 355, 130)
        pygame.draw.rect(screen, (7, 10, 13), p, border_radius=10); pygame.draw.rect(screen, (165, 139, 88), p, 2, border_radius=10)
        screen.blit(f1.render("LIBRARY // SURVIVAL", True, (225, 194, 120)), (p.x+15,p.y+12))
        status = "LEVEL RESTARTING" if dead else ("HIDDEN DOOR DISCOVERED" if door_revealed else "BOOK RACK FALLING" if rack_sequence else "STORY" if dialogue else "AREA SECURED" if combat.complete else "ELIMINATE 25 INFECTED")
        screen.blit(f2.render(status, True, (238,238,230)), (p.x+15,p.y+48))
        screen.blit(f2.render(f"INFECTED: {len(combat.zombies)}   KILLS: {combat.kills}/25", True, (190,198,198)), (p.x+15,p.y+76))
        screen.blit(f2.render(f"FACULTY INFECTED: {combat.faculty_spawned}/7", True, (190,198,198)), (p.x+15,p.y+101))
        a = pygame.Rect(screen.get_width()-250, screen.get_height()-105, 225, 82)
        pygame.draw.rect(screen,(7,10,13),a,border_radius=10); pygame.draw.rect(screen,(165,139,88),a,2,border_radius=10)
        screen.blit(f3.render(f"{combat.ammo:02d}/50",True,(239,222,183)),(a.x+15,a.y+7))
        rt = f"RELOADING {max(0,combat.reload_timer):.1f}s" if combat.reloading else "R  RELOAD"
        screen.blit(f2.render(rt,True,(225,179,72)),(a.x+15,a.y+54))
        i = pygame.Rect(24,172,355,58); pygame.draw.rect(screen,(7,10,13),i,border_radius=8); pygame.draw.rect(screen,(120,75,65),i,2,border_radius=8)
        screen.blit(f2.render(f"IMMUNITY  {combat.immunity}/100",True,(235,215,205)),(i.x+15,i.y+18))
        if dead:
            ov=pygame.Surface(screen.get_size(),pygame.SRCALPHA); ov.fill((0,0,0,180)); screen.blit(ov,(0,0)); t=f3.render("HERO DOWN",True,(220,75,60)); screen.blit(t,t.get_rect(center=(screen.get_width()//2,screen.get_height()//2)))


class LibraryChapter:
    def __init__(self, player, viveka):
        self.player = player
        self.viveka = viveka
        self.block = LibraryBlock()
        self.camera = None
        self.combat = LibraryCombat(self.block)
        self.ui = LibraryUI()
        self.intro = [("Hero", "Mam, you go and look for the faculty. I'll handle this."), ("Viveka Mam", "Be careful. I'll find them.")]
        self.dialogue = [("Faculty Member", "Our Principal is in the Main Block."), ("Faculty Member", "He is surrounded by so many zombies. How are you going to help him?"), ("Hero", "I will."), ("Hero", "Mam, you have to bring these survivors out of the campus."), ("Hero", "I will bring the Principal.")]
        self.intro_active = False; self.intro_index = 0; self.dialogue_active = False; self.dialogue_index = 0
        self.viveka_searching = False; self.rack_sequence = False; self.rack_timer = 0; self.door_revealed = False; self.door_thought_active = False; self.door_thought_timer = 0
        self.dead = False; self.death_timer = 0; self.complete = False; self.faculty = [NPC("Faculty", 1120+i*55, 285+(i%2)*55, (170,125,90)) for i in range(3)]

    def reset(self):
        self.combat = LibraryCombat(self.block); self.combat.start()
        self.intro_active = True; self.intro_index = 0; self.dialogue_active = False; self.dialogue_index = 0
        self.viveka_searching = False; self.rack_sequence = False; self.rack_timer = 0; self.door_revealed = False; self.door_thought_active = False; self.door_thought_timer = 0; self.dead = False; self.death_timer = 0; self.complete = False
        self.player.x, self.player.y = self.block.entry_point; self.player.rect.topleft = (int(self.player.x), int(self.player.y)); self.player.walking=False; self.player.direction="up"
        self.viveka.rect.center=(self.player.rect.centerx-70,self.player.rect.centery+20)

    def handle_key(self, key):
        if key != pygame.K_e or self.dead: return
        if self.intro_active:
            self.intro_index += 1
            if self.intro_index >= len(self.intro): self.intro_active=False; self.viveka_searching=True
        elif self.dialogue_active:
            self.dialogue_index += 1
            if self.dialogue_index >= len(self.dialogue): self.dialogue_active=False; self.complete=True

    def shoot(self, tx, ty): self.combat.shoot(self.player, tx, ty)
    def reload(self): self.combat.start_reload()

    def update(self, dt):
        if self.dead:
            self.death_timer -= dt
            if self.death_timer <= 0: self.reset()
            return
        if self.intro_active or self.dialogue_active or self.rack_sequence or self.door_thought_active: self.player.walking=False
        elif not self.combat.complete: self.player.update(dt,self.block.width,self.block.height,self._collision())
        if self.viveka_searching and not self.dialogue_active:
            target=pygame.Vector2(self.block.width-240,170); cur=pygame.Vector2(self.viveka.rect.center); d=target-cur
            if d.length_squared()>35**2: d.normalize_ip(); cur += d*90*dt; self.viveka.rect.center=(int(cur.x),int(cur.y))
        if not self.intro_active and not self.dialogue_active and not self.rack_sequence and not self.door_thought_active and not self.combat.complete:
            self.combat.update(self.player,dt)
            if self.combat.immunity<=0:
                self.dead=True; self.death_timer=2.0; return
        if self.combat.complete and not self.rack_sequence and not self.dialogue_active and not self.complete:
            self.rack_sequence=True; self.rack_timer=0
        if self.rack_sequence:
            self.rack_timer += dt
            if self.rack_timer>=1.2: self.door_revealed=True
            if self.rack_timer>=5.2:
                self.rack_sequence=False
                self.door_thought_active=True
                self.door_thought_timer=2.0
                self.viveka_searching=False
                self.viveka.rect.center=(1110,250)
        if self.door_thought_active:
            self.door_thought_timer -= dt
            if self.door_thought_timer <= 0:
                self.door_thought_active=False
                self.dialogue_active=True
                self.dialogue_index=0

    def _collision(self):
        class C:
            def __init__(self,b): self.b=b
            def collides(self,rect): return (not self.b.player_bounds.contains(rect) or any(rect.colliderect(o) for o in self.b.get_collision_rects()))
        return C(self.block)

    def draw(self, screen, camera):
        self.block.draw(screen,camera,self.rack_sequence,self.door_revealed); self.combat.draw(screen,camera); self.viveka.draw(screen,camera)
        if self.dialogue_active:
            for f in self.faculty: f.draw(screen,camera)
        self.player.draw(screen,camera); self.ui.draw(screen,self.combat,self.rack_sequence,self.door_revealed,self.dialogue_active,self.dead)
        if self.intro_active: self._dialogue_card(screen,self.intro[self.intro_index])
        if self.door_thought_active:
            ov=pygame.Surface(screen.get_size(),pygame.SRCALPHA); ov.fill((0,0,0,95)); screen.blit(ov,(0,0))
            f=pygame.font.Font(None,36); t=f.render("What is this door for?",True,(240,240,235))
            screen.blit(t,t.get_rect(center=(screen.get_width()//2,screen.get_height()//2)))
        if self.dialogue_active: self._dialogue_card(screen,self.dialogue[self.dialogue_index])
        if self.rack_sequence:
            ov=pygame.Surface(screen.get_size(),pygame.SRCALPHA); ov.fill((0,0,0,95)); screen.blit(ov,(0,0)); f=pygame.font.Font(None,36); s=pygame.font.Font(None,23); title="A HIDDEN DOOR" if self.door_revealed else "THE BOOK RACK FALLS"; sub="What is this door for?" if self.door_revealed else "Something is moving..."; screen.blit(f.render(title,True,(235,220,170)),(screen.get_width()//2-250,80)); screen.blit(s.render(sub,True,(190,195,195)),(screen.get_width()//2-250,120))

    def _dialogue_card(self,screen,item):
        ov=pygame.Surface(screen.get_size(),pygame.SRCALPHA); ov.fill((0,0,0,125)); screen.blit(ov,(0,0)); box=pygame.Rect(110,screen.get_height()-205,screen.get_width()-220,165); pygame.draw.rect(screen,(8,12,16),box,border_radius=14); pygame.draw.rect(screen,(205,173,74),box,2,border_radius=14); f1=pygame.font.Font(None,30); f2=pygame.font.Font(None,25); f3=pygame.font.Font(None,20); screen.blit(f1.render(item[0],True,(225,183,58)),(box.x+24,box.y+20)); screen.blit(f2.render(item[1],True,(240,240,235)),(box.x+24,box.y+62)); screen.blit(f3.render("E  CONTINUE",True,(150,158,160)),(box.right-125,box.bottom-30))
