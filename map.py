import pygame
import random
import math


class CampusMap:
    """
    Procedural 2D pixel-style campus map for Campus Outbreak.

    Layout:
        - NCC area behind Library Dome
        - Mechanical Block upper-left
        - Library Dome upper-center
        - Main Block upper-right with stadium
        - AI Block left-middle
        - ECE Block right-middle
        - Large Play Ground in the center/lower area
        - Bus Parking lower-left
        - Main Gate bottom-center
    """

    def __init__(self):
        # -------------------------------------------------------------
        # WORLD
        # -------------------------------------------------------------
        self.width = 2600
        self.height = 1800

        # -------------------------------------------------------------
        # PALETTE
        # -------------------------------------------------------------
        self.GRASS = (53, 128, 55)
        self.GRASS_2 = (66, 145, 61)
        self.GRASS_DARK = (31, 91, 39)
        self.GRASS_LIGHT = (91, 165, 69)

        self.ROAD = (48, 50, 53)
        self.ROAD_EDGE = (25, 28, 30)
        self.ROAD_LINE = (242, 203, 66)
        self.CROSSWALK = (230, 230, 210)

        self.PATH = (205, 176, 123)
        self.PATH_LIGHT = (231, 202, 148)
        self.PATH_DARK = (157, 125, 82)

        self.BUILDING = (184, 91, 55)
        self.BUILDING_LIGHT = (214, 119, 73)
        self.BUILDING_DARK = (101, 53, 39)
        self.ROOF = (118, 61, 48)
        self.ROOF_DARK = (76, 45, 39)
        self.WINDOW = (55, 113, 151)
        self.WINDOW_LIGHT = (112, 190, 218)

        self.WHITE = (247, 247, 235)
        self.BLACK = (18, 22, 20)
        self.YELLOW = (245, 201, 55)
        self.BLUE = (54, 137, 221)
        self.RED = (214, 55, 55)
        self.PURPLE = (130, 75, 180)

        self.GROUND = (191, 139, 78)
        self.GROUND_DARK = (164, 113, 65)
        self.TRACK = (220, 125, 82)
        self.FIELD = (76, 159, 70)

        self.TREE_TRUNK = (101, 65, 38)
        self.TREE_DARK = (24, 76, 34)
        self.TREE = (35, 111, 45)
        self.TREE_LIGHT = (75, 153, 59)

        # -------------------------------------------------------------
        # FIXED CAMPUS AREAS
        # -------------------------------------------------------------
        # Main Block - top right
        self.main_block = pygame.Rect(1160, 120, 1080, 470)

        # Main Block internal stadium/courtyard
        self.main_courtyard = pygame.Rect(1405, 205, 590, 270)

        # Library Dome - between Mech and Main Block
        self.library = pygame.Rect(850, 375, 300, 225)

        # NCC - specifically behind the library
        self.ncc_block = pygame.Rect(845, 55, 300, 220)

        # Mechanical Block - upper left
        self.mech_block = pygame.Rect(445, 325, 340, 300)

        # AI Block - vertical left-middle
        self.ai_block = pygame.Rect(445, 735, 245, 575)

        # ECE Block - vertical right-middle
        self.ece_block = pygame.Rect(2070, 705, 280, 570)

        # Large central playground
        self.playground = pygame.Rect(760, 675, 1160, 735)

        # Bus parking
        self.bus_parking = pygame.Rect(90, 790, 300, 430)

        # Main gate
        self.main_gate = pygame.Rect(1110, 1605, 380, 95)

        # AI entrance
        self.ai_entrance = pygame.Rect(
            self.ai_block.left - 18,
            self.ai_block.centery - 55,
            42,
            110,
        )
        self.ai_entrance_zone = self.ai_entrance.inflate(110, 110)

        # -------------------------------------------------------------
        # DECORATION DATA
        # -------------------------------------------------------------
        random.seed(27)

        self.trees = []
        for _ in range(190):
            x = random.randint(35, self.width - 35)
            y = random.randint(35, self.height - 35)

            # Keep major areas open.
            protected = [
                self.main_block.inflate(90, 90),
                self.playground.inflate(45, 45),
                self.ai_block.inflate(50, 50),
                self.ece_block.inflate(50, 50),
                self.mech_block.inflate(50, 50),
                self.library.inflate(70, 70),
                self.ncc_block.inflate(55, 55),
                self.bus_parking.inflate(50, 50),
                self.main_gate.inflate(70, 100),
            ]

            if any(r.collidepoint(x, y) for r in protected):
                continue

            self.trees.append((x, y, random.randint(22, 31)))

        # A few intentional trees around recognizable locations.
        self.trees.extend([
            (730, 90, 28), (780, 140, 25), (1185, 85, 28),
            (2310, 130, 30), (2420, 300, 26),
            (350, 300, 27), (350, 650, 28),
            (735, 360, 25), (1210, 650, 25),
            (725, 720, 28), (1980, 720, 28),
            (1980, 1050, 30), (1980, 1350, 28),
            (720, 1450, 29), (1980, 1450, 29),
            (400, 1450, 27), (2200, 1450, 28),
        ])

        self.lamps = [
            (405, 310), (405, 650), (805, 650), (805, 1430),
            (1160, 650), (2020, 650), (2020, 1430),
            (2410, 650), (2410, 1400), (1040, 1540),
            (1560, 1540), (2260, 1540),
        ]

        self.flowers = [
            (780, 300), (805, 330), (1180, 300), (1230, 620),
            (710, 640), (2010, 650), (2420, 650),
            (730, 1470), (1980, 1470), (1040, 1510),
            (1570, 1510), (2240, 1510),
        ]

    # ================================================================
    # MAIN DRAW
    # ================================================================

    def draw(self, screen, camera):
        screen.fill(self.GRASS)

        self._draw_ground_texture(screen, camera)
        self._draw_boundary(screen, camera)
        self._draw_roads(screen, camera)
        self._draw_walkways(screen, camera)
        self._draw_trees(screen, camera)
        self._draw_flowers(screen, camera)
        self._draw_lamps(screen, camera)

        # Buildings and landmarks
        self._draw_bus_parking(screen, camera)
        self._draw_ncc(screen, camera)
        self._draw_mech_block(screen, camera)
        self._draw_library(screen, camera)
        self._draw_main_block(screen, camera)
        self._draw_ai_block(screen, camera)
        self._draw_ece_block(screen, camera)
        self._draw_playground(screen, camera)
        self._draw_main_gate(screen, camera)
        self._draw_ai_entrance(screen, camera)

    # ================================================================
    # BACKGROUND
    # ================================================================

    def _draw_ground_texture(self, screen, camera):
        # Large subtle pixel patches.
        for x in range(40, self.width, 120):
            for y in range(40, self.height, 120):
                sx = x - camera.x
                sy = y - camera.y

                if -20 <= sx <= screen.get_width() + 20 and \
                   -20 <= sy <= screen.get_height() + 20:
                    pygame.draw.rect(
                        screen,
                        self.GRASS_2 if (x // 120 + y // 120) % 2 == 0
                        else self.GRASS,
                        (sx, sy, 18, 8),
                    )

    def _draw_boundary(self, screen, camera):
        r = pygame.Rect(
            18 - camera.x,
            18 - camera.y,
            self.width - 36,
            self.height - 36,
        )

        pygame.draw.rect(screen, self.GRASS_DARK, r, 12)
        pygame.draw.rect(screen, (224, 191, 126), r, 5)

        # Small fence posts.
        for x in range(r.left + 20, r.right - 10, 42):
            pygame.draw.rect(
                screen,
                (125, 82, 48),
                (x, r.top - 2, 6, 18),
            )
            pygame.draw.rect(
                screen,
                (125, 82, 48),
                (x, r.bottom - 16, 6, 18),
            )

    # ================================================================
    # ROADS
    # ================================================================

    def _draw_roads(self, screen, camera):
        roads = [
            # Main vertical spine
            pygame.Rect(1080, 0, 120, self.height),

            # Main horizontal road through campus
            pygame.Rect(330, 620, 2010, 78),

            # Lower horizontal road
            pygame.Rect(0, 1510, self.width, 105),

            # Left road beside AI / Mech
            pygame.Rect(380, 280, 75, 1250),

            # AI access road
            pygame.Rect(340, 680, 620, 75),

            # ECE loop road
            pygame.Rect(2390, 450, 90, 1080),

            # Road around main block
            pygame.Rect(2260, 120, 90, 520),
            pygame.Rect(1050, 590, 1300, 72),

            # Main gate approach
            pygame.Rect(1280, 1570, 90, 230),
        ]

        for road in roads:
            shadow = road.inflate(12, 12)
            pygame.draw.rect(
                screen,
                self.ROAD_EDGE,
                self._screen_rect(shadow, camera),
            )
            pygame.draw.rect(
                screen,
                self.ROAD,
                self._screen_rect(road, camera),
            )

        # Yellow road markings.
        for y in range(35, self.height, 90):
            self._rect(
                screen,
                self.ROAD_LINE,
                (1135, y, 8, 42),
                camera,
            )

        for x in range(20, self.width, 105):
            self._rect(
                screen,
                self.ROAD_LINE,
                (x, 1554, 48, 7),
                camera,
            )

        for y in range(315, 1510, 90):
            self._rect(
                screen,
                self.ROAD_LINE,
                (413, y, 7, 38),
                camera,
            )

        # Main horizontal markings.
        for x in range(360, 2320, 100):
            self._rect(
                screen,
                self.ROAD_LINE,
                (x, 655, 48, 6),
                camera,
            )

        # Crosswalks.
        self._crosswalk(screen, camera, 1070, 612, 135, 28, True)
        self._crosswalk(screen, camera, 1270, 1500, 110, 25, True)
        self._crosswalk(screen, camera, 2350, 605, 30, 90, False)
        self._crosswalk(screen, camera, 430, 600, 75, 28, True)

    def _crosswalk(self, screen, camera, x, y, w, h, horizontal=True):
        if horizontal:
            for px in range(x, x + w, 18):
                self._rect(
                    screen,
                    self.CROSSWALK,
                    (px, y, 9, h),
                    camera,
                )
        else:
            for py in range(y, y + h, 18):
                self._rect(
                    screen,
                    self.CROSSWALK,
                    (x, py, w, 9),
                    camera,
                )

    # ================================================================
    # WALKWAYS
    # ================================================================

    def _draw_walkways(self, screen, camera):
        paths = [
            # Library path
            pygame.Rect(970, 275, 55, 100),

            # Library to main block
            pygame.Rect(1125, 465, 300, 35),

            # AI entrance path
            pygame.Rect(395, 960, 50, 40),

            # Main gate to playground
            pygame.Rect(1280, 1385, 90, 185),

            # ECE path
            pygame.Rect(2010, 930, 60, 40),

            # Mech path
            pygame.Rect(785, 455, 65, 42),

            # NCC path
            pygame.Rect(970, 275, 55, 100),
        ]

        for path in paths:
            self._rect(screen, self.PATH_DARK, path.inflate(8, 8), camera)
            self._rect(screen, self.PATH, path, camera)
            self._rect(screen, self.PATH_LIGHT, path, camera, 3)

    # ================================================================
    # TREES / FLOWERS / LIGHTS
    # ================================================================

    def _draw_trees(self, screen, camera):
        for x, y, size in self.trees:
            sx = x - camera.x
            sy = y - camera.y

            if sx < -80 or sx > screen.get_width() + 80 or \
               sy < -80 or sy > screen.get_height() + 80:
                continue

            # Shadow
            pygame.draw.ellipse(
                screen,
                (30, 78, 36),
                (sx - size, sy + size // 2, size * 2, 15),
            )

            # Trunk
            pygame.draw.rect(
                screen,
                self.TREE_TRUNK,
                (sx - 5, sy + 2, 10, 24),
            )

            # Pixel-style layered foliage
            pygame.draw.circle(
                screen,
                self.TREE_DARK,
                (sx, sy),
                size,
            )
            pygame.draw.circle(
                screen,
                self.TREE,
                (sx - 5, sy - 5),
                max(8, size - 7),
            )
            pygame.draw.circle(
                screen,
                self.TREE_LIGHT,
                (sx - size // 2, sy - size // 2),
                max(4, size // 4),
            )

    def _draw_flowers(self, screen, camera):
        for x, y in self.flowers:
            sx, sy = x - camera.x, y - camera.y
            pygame.draw.circle(screen, (255, 220, 80), (sx, sy), 4)
            pygame.draw.circle(screen, (230, 75, 120), (sx + 5, sy), 3)
            pygame.draw.circle(screen, (140, 80, 220), (sx - 5, sy), 3)
            pygame.draw.line(
                screen,
                (45, 110, 45),
                (sx, sy + 3),
                (sx, sy + 14),
                2,
            )

    def _draw_lamps(self, screen, camera):
        for x, y in self.lamps:
            sx, sy = x - camera.x, y - camera.y

            pygame.draw.rect(
                screen,
                (50, 48, 43),
                (sx - 2, sy - 18, 4, 25),
            )
            pygame.draw.circle(
                screen,
                (255, 218, 100),
                (sx, sy - 21),
                5,
            )
            pygame.draw.circle(
                screen,
                (255, 238, 150),
                (sx, sy - 21),
                2,
            )

    # ================================================================
    # BUS PARKING
    # ================================================================

    def _draw_bus_parking(self, screen, camera):
        rect = self._screen_rect(self.bus_parking, camera)

        pygame.draw.rect(
            screen,
            self.ROAD_EDGE,
            rect.inflate(12, 12),
            border_radius=8,
        )
        pygame.draw.rect(
            screen,
            (57, 60, 62),
            rect,
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            self.PATH_LIGHT,
            rect,
            5,
            border_radius=6,
        )

        # Parking bays
        for y in range(rect.top + 35, rect.bottom - 30, 70):
            pygame.draw.line(
                screen,
                (220, 210, 180),
                (rect.left + 15, y),
                (rect.right - 15, y),
                2,
            )

        # Buses
        for i in range(5):
            bx = rect.left + 38
            by = rect.top + 35 + i * 72

            pygame.draw.rect(
                screen,
                (222, 178, 46),
                (bx, by, 205, 38),
                border_radius=5,
            )
            pygame.draw.rect(
                screen,
                (65, 116, 145),
                (bx + 22, by + 7, 100, 15),
            )
            pygame.draw.rect(
                screen,
                (248, 215, 95),
                (bx + 126, by + 7, 45, 15),
            )

            pygame.draw.circle(
                screen, (25, 25, 25), (bx + 32, by + 39), 6
            )
            pygame.draw.circle(
                screen, (25, 25, 25), (bx + 174, by + 39), 6
            )

        self._label(screen, "BUS PARKING", rect.centerx, rect.top - 22)

        # Parking sign
        pygame.draw.rect(
            screen,
            self.BLUE,
            (rect.centerx - 20, rect.bottom - 65, 40, 40),
            border_radius=4,
        )
        self._label(screen, "P", rect.centerx, rect.bottom - 45, 22)

    # ================================================================
    # NCC
    # ================================================================

    def _draw_ncc(self, screen, camera):
        rect = self._screen_rect(self.ncc_block, camera)
        self._building_base(screen, rect)

        yard = rect.inflate(-70, -65)
        pygame.draw.rect(screen, (69, 133, 65), yard)

        # Small parade area
        pygame.draw.rect(
            screen,
            (54, 92, 53),
            (yard.left + 30, yard.top + 20, yard.width - 60, 80),
        )

        # Flag pole
        pygame.draw.line(
            screen,
            (45, 45, 45),
            (rect.centerx, rect.top + 25),
            (rect.centerx, rect.bottom - 25),
            4,
        )
        pygame.draw.polygon(
            screen,
            self.RED,
            [
                (rect.centerx, rect.top + 28),
                (rect.centerx + 40, rect.top + 40),
                (rect.centerx, rect.top + 52),
            ],
        )

        self._windows(screen, rect)
        self._label(screen, "NCC AREA", rect.centerx, rect.top - 22)

    # ================================================================
    # MECHANICAL BLOCK
    # ================================================================

    def _draw_mech_block(self, screen, camera):
        rect = self._screen_rect(self.mech_block, camera)
        self._building_base(screen, rect)

        courtyard = rect.inflate(-70, -70)
        pygame.draw.rect(screen, (68, 126, 63), courtyard)

        workshop = pygame.Rect(
            courtyard.left + 28,
            courtyard.top + 28,
            courtyard.width - 56,
            courtyard.height - 56,
        )
        pygame.draw.rect(screen, (213, 130, 79), workshop)
        pygame.draw.rect(screen, self.BUILDING_DARK, workshop, 4)

        # Workshop machinery blocks
        for x, y in [
            (workshop.left + 35, workshop.top + 35),
            (workshop.right - 70, workshop.top + 35),
            (workshop.left + 35, workshop.bottom - 65),
            (workshop.right - 70, workshop.bottom - 65),
        ]:
            pygame.draw.rect(screen, (102, 103, 100), (x, y, 35, 30))
            pygame.draw.rect(screen, (63, 66, 65), (x + 7, y + 7, 21, 16))

        self._windows(screen, rect)
        self._label(screen, "MECH BLOCK", rect.centerx, rect.top - 24)

    # ================================================================
    # LIBRARY DOME
    # ================================================================

    def _draw_library(self, screen, camera):
        cx = self.library.centerx - camera.x
        cy = self.library.centery - camera.y

        # Shadow
        pygame.draw.ellipse(
            screen,
            (38, 58, 37),
            (cx - 155, cy - 82, 310, 175),
        )

        # Main circular building
        pygame.draw.ellipse(
            screen,
            self.BUILDING_DARK,
            (cx - 145, cy - 82, 290, 165),
        )
        pygame.draw.ellipse(
            screen,
            self.BUILDING_LIGHT,
            (cx - 137, cy - 75, 274, 150),
        )

        # Segmented roof
        for angle in range(0, 360, 30):
            a = math.radians(angle)
            x1 = cx + int(math.cos(a) * 105)
            y1 = cy + int(math.sin(a) * 72)
            x2 = cx + int(math.cos(a) * 132)
            y2 = cy + int(math.sin(a) * 88)
            pygame.draw.line(
                screen,
                self.ROOF_DARK,
                (x1, y1),
                (x2, y2),
                6,
            )

        # Dome
        pygame.draw.circle(
            screen,
            (229, 213, 177),
            (cx, cy - 12),
            52,
        )
        pygame.draw.circle(
            screen,
            (248, 237, 204),
            (cx - 12, cy - 24),
            33,
        )
        pygame.draw.circle(
            screen,
            self.ROOF_DARK,
            (cx, cy - 65),
            7,
        )

        # Entrance
        pygame.draw.rect(
            screen,
            self.BUILDING_DARK,
            (cx - 32, cy + 35, 64, 40),
        )
        pygame.draw.rect(
            screen,
            (73, 112, 135),
            (cx - 20, cy + 40, 40, 35),
        )

        self._label(screen, "LIBRARY DOME", cx, cy + 105)

    # ================================================================
    # MAIN BLOCK
    # ================================================================

    def _draw_main_block(self, screen, camera):
        rect = self._screen_rect(self.main_block, camera)

        self._building_base(screen, rect)

        # Central courtyard
        courtyard = self._screen_rect(self.main_courtyard, camera)
        pygame.draw.rect(screen, (52, 117, 57), courtyard)
        pygame.draw.rect(screen, (226, 183, 112), courtyard, 7)

        # Running track
        track = pygame.Rect(
            courtyard.centerx - 230,
            courtyard.centery - 90,
            460,
            180,
        )
        pygame.draw.ellipse(screen, self.TRACK, track)

        # Inner field
        field = pygame.Rect(
            courtyard.centerx - 175,
            courtyard.centery - 62,
            350,
            124,
        )
        pygame.draw.ellipse(screen, self.FIELD, field)

        # Track center line
        pygame.draw.line(
            screen,
            (245, 224, 178),
            (field.centerx, field.top),
            (field.centerx, field.bottom),
            3,
        )
        pygame.draw.circle(
            screen,
            (245, 224, 178),
            field.center,
            27,
            3,
        )

        # Goal areas
        pygame.draw.rect(
            screen,
            (245, 224, 178),
            (field.left + 8, field.centery - 23, 38, 46),
            2,
        )
        pygame.draw.rect(
            screen,
            (245, 224, 178),
            (field.right - 46, field.centery - 23, 38, 46),
            2,
        )

        # Solar panels / roof strips
        pygame.draw.rect(
            screen,
            self.ROOF_DARK,
            (rect.left + 30, rect.top + 16, rect.width - 60, 30),
        )
        pygame.draw.rect(
            screen,
            self.ROOF_DARK,
            (rect.left + 30, rect.bottom - 46, rect.width - 60, 30),
        )
        pygame.draw.rect(
            screen,
            self.ROOF_DARK,
            (rect.left + 15, rect.top + 46, 32, rect.height - 92),
        )
        pygame.draw.rect(
            screen,
            self.ROOF_DARK,
            (rect.right - 47, rect.top + 46, 32, rect.height - 92),
        )

        # Blue solar-panel highlights
        for x in range(rect.left + 60, rect.right - 60, 72):
            pygame.draw.rect(
                screen,
                (46, 102, 134),
                (x, rect.top + 20, 48, 20),
            )
            pygame.draw.line(
                screen,
                (94, 158, 184),
                (x + 24, rect.top + 20),
                (x + 24, rect.top + 40),
                2,
            )

        self._windows(screen, rect)
        self._label(screen, "MAIN BLOCK", rect.centerx, rect.top - 25)

    # ================================================================
    # AI BLOCK
    # ================================================================

    def _draw_ai_block(self, screen, camera):
        rect = self._screen_rect(self.ai_block, camera)

        self._building_base(screen, rect)

        inner = rect.inflate(-45, -35)
        pygame.draw.rect(screen, (216, 119, 73), inner)

        # Roof
        pygame.draw.rect(
            screen,
            self.ROOF_DARK,
            (inner.left + 10, inner.top + 10, inner.width - 20, 34),
        )

        # Window rows
        for y in range(inner.top + 70, inner.bottom - 25, 54):
            pygame.draw.rect(
                screen,
                self.WINDOW,
                (inner.left + 22, y, inner.width - 44, 22),
            )
            pygame.draw.rect(
                screen,
                self.WINDOW_LIGHT,
                (inner.left + 26, y + 4, inner.width - 52, 6),
            )

        # AI signage
        sign = pygame.Rect(
            rect.centerx - 65,
            rect.centery - 22,
            130,
            44,
        )
        pygame.draw.rect(screen, self.BLACK, sign, border_radius=6)
        pygame.draw.rect(screen, self.YELLOW, sign, 2, border_radius=6)
        self._label(screen, "AI BLOCK", sign.centerx, sign.centery, 22)

        # AI warning marker
        pygame.draw.circle(
            screen,
            self.YELLOW,
            (rect.left + 22, rect.centery),
            10,
        )
        self._label(
            screen,
            "!",
            rect.left + 22,
            rect.centery - 1,
            18,
        )

    # ================================================================
    # ECE BLOCK
    # ================================================================

    def _draw_ece_block(self, screen, camera):
        rect = self._screen_rect(self.ece_block, camera)

        self._building_base(screen, rect)

        inner = rect.inflate(-38, -35)
        pygame.draw.rect(screen, (213, 119, 73), inner)

        for y in range(inner.top + 40, inner.bottom - 20, 50):
            pygame.draw.rect(
                screen,
                self.WINDOW,
                (inner.left + 22, y, inner.width - 44, 20),
            )
            pygame.draw.rect(
                screen,
                self.WINDOW_LIGHT,
                (inner.left + 25, y + 3, inner.width - 50, 6),
            )

        sign = pygame.Rect(
            rect.centerx - 60,
            rect.centery - 25,
            120,
            50,
        )
        pygame.draw.rect(screen, self.BLACK, sign, border_radius=6)
        pygame.draw.rect(screen, self.YELLOW, sign, 2, border_radius=6)
        self._label(screen, "ECE BLOCK", sign.centerx, sign.centery, 20)

    # ================================================================
    # PLAYGROUND
    # ================================================================

    def _draw_playground(self, screen, camera):
        rect = self._screen_rect(self.playground, camera)

        # Dirt/playground area
        pygame.draw.rect(
            screen,
            self.GROUND_DARK,
            rect.inflate(12, 12),
        )
        pygame.draw.rect(
            screen,
            self.GROUND,
            rect,
        )

        # Random dirt patches
        for i in range(24):
            x = rect.left + 70 + ((i * 173) % max(1, rect.width - 140))
            y = rect.top + 65 + ((i * 97) % max(1, rect.height - 130))
            pygame.draw.circle(
                screen,
                (198, 148, 83),
                (x, y),
                7 + (i % 5),
            )

        # Running track
        track = pygame.Rect(
            rect.centerx - 330,
            rect.centery - 190,
            660,
            380,
        )
        pygame.draw.ellipse(
            screen,
            self.TRACK,
            track,
            16,
        )

        # Inner grass field
        field = pygame.Rect(
            rect.centerx - 250,
            rect.centery - 135,
            500,
            270,
        )
        pygame.draw.ellipse(
            screen,
            self.FIELD,
            field,
        )

        # Football markings
        pygame.draw.line(
            screen,
            (245, 224, 178),
            (field.centerx, field.top),
            (field.centerx, field.bottom),
            3,
        )
        pygame.draw.circle(
            screen,
            (245, 224, 178),
            field.center,
            36,
            3,
        )

        # Basketball court on lower-right
        court = pygame.Rect(
            rect.right - 280,
            rect.bottom - 205,
            220,
            145,
        )
        pygame.draw.rect(screen, (229, 160, 69), court)
        pygame.draw.rect(
            screen,
            (248, 221, 156),
            court,
            3,
        )
        pygame.draw.line(
            screen,
            (248, 221, 156),
            court.midtop,
            court.midbottom,
            2,
        )
        pygame.draw.circle(
            screen,
            (248, 221, 156),
            court.center,
            28,
            2,
        )

        # Tire obstacles / props
        tire_positions = [
            (rect.left + 120, rect.top + 130),
            (rect.left + 145, rect.top + 145),
            (rect.right - 150, rect.top + 110),
            (rect.right - 120, rect.top + 130),
            (rect.left + 170, rect.bottom - 120),
        ]
        for x, y in tire_positions:
            pygame.draw.circle(screen, (35, 35, 37), (x, y), 18)
            pygame.draw.circle(screen, (76, 76, 76), (x, y), 9)
            pygame.draw.circle(screen, (30, 30, 30), (x, y), 5)

        self._label(
            screen,
            "PLAY GROUND",
            rect.centerx,
            rect.top + 32,
        )

    # ================================================================
    # MAIN GATE
    # ================================================================

    def _draw_main_gate(self, screen, camera):
        rect = self._screen_rect(self.main_gate, camera)

        # Gate shadow
        pygame.draw.rect(
            screen,
            self.ROAD_EDGE,
            rect.inflate(18, 18),
            border_radius=8,
        )

        # Pillars
        pygame.draw.rect(
            screen,
            (190, 155, 105),
            (rect.left, rect.top - 35, 52, 95),
        )
        pygame.draw.rect(
            screen,
            (190, 155, 105),
            (rect.right - 52, rect.top - 35, 52, 95),
        )

        # Gate opening
        pygame.draw.rect(
            screen,
            (45, 42, 39),
            (rect.left + 48, rect.top, rect.width - 96, 42),
        )

        # Metal bars
        for x in range(rect.left + 60, rect.right - 60, 25):
            pygame.draw.rect(
                screen,
                (100, 100, 92),
                (x, rect.top + 4, 5, 32),
            )

        # Lamps
        pygame.draw.circle(
            screen,
            self.YELLOW,
            (rect.left + 26, rect.top - 12),
            7,
        )
        pygame.draw.circle(
            screen,
            self.YELLOW,
            (rect.right - 26, rect.top - 12),
            7,
        )

        self._label(
            screen,
            "MAIN GATE",
            rect.centerx,
            rect.bottom + 25,
        )

    # ================================================================
    # AI ENTRANCE
    # ================================================================

    def _draw_ai_entrance(self, screen, camera):
        rect = self._screen_rect(self.ai_entrance, camera)

        platform = rect.inflate(26, 26)
        pygame.draw.rect(
            screen,
            self.PATH_LIGHT,
            platform,
        )

        pygame.draw.rect(
            screen,
            (25, 27, 28),
            rect,
        )
        pygame.draw.rect(
            screen,
            self.YELLOW,
            rect,
            3,
        )

        # Blue interaction marker
        pygame.draw.circle(
            screen,
            self.BLUE,
            (rect.centerx, rect.top - 20),
            10,
        )
        pygame.draw.circle(
            screen,
            (220, 240, 255),
            (rect.centerx, rect.top - 20),
            5,
        )

        self._label(
            screen,
            "AI ENTRANCE",
            rect.centerx,
            rect.top - 48,
            18,
        )

    # ================================================================
    # BUILDING HELPERS
    # ================================================================

    def _building_base(self, screen, rect):
        shadow = rect.move(12, 12)

        pygame.draw.rect(
            screen,
            (31, 47, 31),
            shadow,
        )
        pygame.draw.rect(
            screen,
            self.BUILDING,
            rect,
        )
        pygame.draw.rect(
            screen,
            self.BUILDING_LIGHT,
            rect,
            5,
        )

        # Top roof strip
        pygame.draw.rect(
            screen,
            self.ROOF_DARK,
            (rect.left + 10, rect.top + 10, rect.width - 20, 26),
        )

    def _windows(self, screen, rect):
        # Upper row
        for x in range(rect.left + 38, rect.right - 30, 52):
            pygame.draw.rect(
                screen,
                self.WINDOW,
                (x, rect.top + 48, 28, 17),
            )
            pygame.draw.rect(
                screen,
                self.WINDOW_LIGHT,
                (x + 3, rect.top + 51, 22, 5),
            )

        # Lower row
        for x in range(rect.left + 38, rect.right - 30, 52):
            pygame.draw.rect(
                screen,
                self.WINDOW,
                (x, rect.bottom - 68, 28, 17),
            )

    # ================================================================
    # DRAW / LABEL HELPERS
    # ================================================================

    def _screen_rect(self, rect, camera):
        return pygame.Rect(
            rect.x - camera.x,
            rect.y - camera.y,
            rect.width,
            rect.height,
        )

    def _rect(self, screen, color, values, camera, width=0):
        x, y, w, h = values
        r = pygame.Rect(
            x - camera.x,
            y - camera.y,
            w,
            h,
        )
        pygame.draw.rect(screen, color, r, width)

    def _label(self, screen, text, x, y, size=22):
        # IMPORTANT:
        # x and y must always be individual numeric coordinates.
        # This avoids the tuple/int error from the previous map.py.
        font = pygame.font.Font(None, size)

        shadow = font.render(text, True, self.BLACK)
        surface = font.render(text, True, self.WHITE)

        text_rect = surface.get_rect(
            center=(int(x), int(y))
        )

        screen.blit(shadow, text_rect.move(3, 3))
        screen.blit(surface, text_rect)
