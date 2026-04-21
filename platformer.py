# -*- coding: utf-8 -*-
"""
2D Platformer - 4 Character Switcher
=====================================
Controls:
  A / Left Arrow  - Move left
  D / Right Arrow - Move right
  W / Up Arrow    - Jump
  TAB             - Switch character
  SPACE           - Ability (Mage: shoot, Warrior: break block)
  Left SHIFT      - Dash (Rogue only)
  ESC             - Quit
"""

importafrom constants import (
    WIDTH, HEIGHT, FPS, LEVEL_WIDTH,
    SKY, BLACK, DARK_GRAY, GRAY, BROWN, BREAK_COL,
    C_WARRIOR, C_MAGE, C_DRUID, C_ROGUE,
)
from player import Warrior, Mage, Druid, Rogue
from enemy import GreenWarrior, GreenMelee, Ghost, SpikeBall, Boss
from menu import MainMenu, PauseMenu

SAVE_PATH = os.path.join(os.path.dirname(__file__), "save.json")

pygame.init()


# ==============================================================================
# Tile rendering helpers
# ==============================================================================

_TILE_DIR    = os.path.join(os.path.dirname(__file__), "sprites", "enemy", "tileset", "1 Tiles")
_tile_raw    = {}   # filename → Surface (32×32 original)
_tile_scaled = {}   # (filename, w, h) → Surface

def _get_tile(name, w, h):
    if name not in _tile_raw:
        _tile_raw[name] = pygame.image.load(
            os.path.join(_TILE_DIR, name)).convert_alpha()
    key = (name, w, h)
    if key not in _tile_scaled:
        _tile_scaled[key] = pygame.transform.scale(_tile_raw[name], (w, h))
    return _tile_scaled[key]

def _tile_row(surface, name, tile_w, tile_h, row_x, row_y, total_w):
    """Blit a tile repeatedly to fill total_w pixels horizontally."""
    t = _get_tile(name, tile_w, tile_h)
    x = row_x
    while x < row_x + total_w:
        clip = min(tile_w, row_x + total_w - x)
        surface.blit(t, (x, row_y), (0, 0, clip, tile_h))
        x += tile_w

def _draw_ground_tiles(surface, rx, ry, rw, rh):
    """Tile_01/02/03 top strip + Tile_04 fill for ground platforms."""
    ts   = 16   # tile size for this context
    top  = min(ts, rh)
    fill = rh - top

    _get_tile("Tile_01.png", ts, top)   # warm cache
    surface.blit(_get_tile("Tile_01.png", ts, top), (rx, ry))
    _tile_row(surface, "Tile_02.png", ts, top, rx + ts, ry, rw - 2 * ts)
    surface.blit(_get_tile("Tile_03.png", ts, top), (rx + rw - ts, ry))

    if fill > 0:
        fy = ry + top
        while fy < ry + rh:
            fh = min(ts, ry + rh - fy)
            _tile_row(surface, "Tile_04.png", ts, fh, rx, fy, rw)
            fy += ts

def _draw_platform_tiles(surface, rx, ry, rw, rh):
    """Tile_07/08/09 for thin floating platforms."""
    ts = rh   # scale tile to platform height so it fits exactly
    if rw <= ts:
        _tile_row(surface, "Tile_08.png", rw, rh, rx, ry, rw)
        return
    surface.blit(_get_tile("Tile_07.png", ts, rh), (rx, ry))
    _tile_row(surface, "Tile_08.png", ts, rh, rx + ts, ry, rw - 2 * ts)
    surface.blit(_get_tile("Tile_09.png", ts, rh), (rx + rw - ts, ry))


# ==============================================================================
# Platform / Block
# ==============================================================================

class Platform:
    """A solid surface the player can stand on."""

    def __init__(self, x, y, w, h, color=None):
        self.rect      = pygame.Rect(x, y, w, h)
        self.color     = color if color is not None else GRAY
        self.breakable = False

    def draw(self, surface, cam_x):
        rx = self.rect.x - cam_x
        ry = self.rect.y
        rw = self.rect.w
        rh = self.rect.h
        if rh > 20:
            _draw_ground_tiles(surface, rx, ry, rw, rh)
        else:
            _draw_platform_tiles(surface, rx, ry, rw, rh)


class Checkpoint:
    """Flag post that updates the player's respawn point on contact."""

    W, H      = 14, 48
    COLOR_OFF = (180, 180,  40)   # yellow — not yet reached
    COLOR_ON  = ( 40, 210,  80)   # green  — activated

    def __init__(self, x, y):
        # x,y = ground level; post rises upward
        self.rect    = pygame.Rect(x, y - self.H, self.W, self.H)
        self.active  = False
        self.spawn_x = x + self.W // 2
        self.spawn_y = y

    def try_activate(self, player_rect):
        if not self.active and self.rect.colliderect(player_rect):
            self.active = True
            return True
        return False

    def draw(self, surface, cam_x):
        rx = self.rect.x - cam_x
        ry = self.rect.y
        # pole
        pygame.draw.rect(surface, (120, 80, 40), (rx + 5, ry, 4, self.H))
        # flag
        flag_color = self.COLOR_ON if self.active else self.COLOR_OFF
        pts = [
            (rx + 9,  ry + 4),
            (rx + 26, ry + 12),
            (rx + 9,  ry + 20),
        ]
        pygame.draw.polygon(surface, flag_color, pts)


class BreakableBlock(Platform):
    """Cracked brick. Only the Warrior can destroy it (SPACE while adjacent)."""

    def __init__(self, x, y, w=40, h=40):
        super().__init__(x, y, w, h, BREAK_COL)
        self.breakable = True
        self.broken    = False

    def draw(self, surface, cam_x):
        if self.broken:
            return
        r = pygame.Rect(self.rect.x - cam_x, self.rect.y,
                        self.rect.w, self.rect.h)
        pygame.draw.rect(surface, self.color, r)
        pygame.draw.rect(surface, (90, 45, 0), r, 2)
        cx, cy = r.centerx, r.centery
        pygame.draw.line(surface, (90, 45, 0), (cx - 8, cy - 8), (cx + 8, cy + 8), 2)
        pygame.draw.line(surface, (90, 45, 0), (cx + 8, cy - 8), (cx - 8, cy + 8), 2)


# ==============================================================================
# Level definition
# ==============================================================================

def create_level():
    platforms = []

    # ------------------------------------------------------------------ Zone 1
    # Ground (gap at x=325–423)
    platforms.append(Platform(  0, 540,  325, 30, BROWN))
    platforms.append(Platform(423, 540, 1127, 30, BROWN))  # x=423-1550

    # Warm-up platforms
    platforms.append(Platform( 78, 475,  78, 14))
    platforms.append(Platform(195, 423,  65, 14))
    platforms.append(Platform(286, 371,  78, 14))

    # After-gap
    platforms.append(Platform(436, 488, 104, 14))
    platforms.append(Platform(566, 423,  65, 14))

    # Breakable wall
    platforms.append(BreakableBlock(514, 514, 26, 26))
    platforms.append(BreakableBlock(514, 488, 26, 26))

    # Speed corridor
    platforms.append(Platform(618, 358, 117, 14))
    platforms.append(Platform(754, 306, 104, 14))
    platforms.append(Platform(858, 358,  91, 14))

    # Tall tower
    platforms.append(Platform( 936, 462,  52, 14))
    platforms.append(Platform( 975, 384,  52, 14))
    platforms.append(Platform(1014, 306,  52, 14))
    platforms.append(Platform(1014, 228,  91, 14))

    # Bridge to zone 2
    platforms.append(Platform(1118, 371, 130, 14))
    platforms.append(Platform(1235, 449, 117, 14))
    platforms.append(Platform(1352, 371,  65, 14))

    # ------------------------------------------------------------------ Zone 2
    # Ponte suspensa — gap at x=1550–1700, stepping stones needed (Druid)
    platforms.append(Platform(1550, 488,  65, 14))   # ledge before gap
    platforms.append(Platform(1620, 436,  52, 14))   # stone 1
    platforms.append(Platform(1680, 371,  52, 14))   # stone 2 (high)
    platforms.append(Platform(1740, 436,  52, 14))   # stone 3
    platforms.append(Platform(1800, 540, 400, 30, BROWN))  # ground resumes x=1800

    platforms.append(Platform(1820, 462,  78, 14))
    platforms.append(Platform(1900, 384,  65, 14))
    platforms.append(Platform(1970, 306,  78, 14))
    platforms.append(Platform(2040, 384,  65, 14))

    # ------------------------------------------------------------------ Zone 3
    # Corredor de blocos — Warrior necessary, 3 breakable walls
    platforms.append(Platform(2200, 540, 550, 30, BROWN))  # ground x=2200-2750

    platforms.append(BreakableBlock(2260, 514, 26, 26))    # wall 1 (2 tall)
    platforms.append(BreakableBlock(2260, 488, 26, 26))
    platforms.append(Platform(2240, 423, 91, 14))          # platform above

    platforms.append(BreakableBlock(2400, 514, 26, 26))    # wall 2 (3 tall)
    platforms.append(BreakableBlock(2400, 488, 26, 26))
    platforms.append(BreakableBlock(2400, 462, 26, 26))
    platforms.append(Platform(2380, 371, 104, 14))

    platforms.append(BreakableBlock(2560, 514, 26, 26))    # wall 3 (2 tall)
    platforms.append(BreakableBlock(2560, 488, 26, 26))
    platforms.append(Platform(2540, 436,  78, 14))

    platforms.append(Platform(2650, 358,  91, 14))
    platforms.append(Platform(2700, 280,  78, 14))         # height challenge

    # ------------------------------------------------------------------ Zone 4
    # Plataformas no céu — gap at x=2750-2900, no ground (Druid + Rogue)
    platforms.append(Platform(2750, 462,  65, 14))
    platforms.append(Platform(2820, 384,  65, 14))
    platforms.append(Platform(2890, 306,  65, 14))
    platforms.append(Platform(2960, 228,  78, 14))         # summit
    platforms.append(Platform(3030, 306,  65, 14))
    platforms.append(Platform(3080, 384,  65, 14))

    # ------------------------------------------------------------------ Zone 5
    # Arena do boss — chão amplo para o boss ter espaço de patrulha
    platforms.append(Platform(2980, 540, 320, 30, BROWN))  # x=2980-3300

    # Torre lateral (acesso visual, não bloqueia o boss)
    platforms.append(Platform(2990, 462,  52, 14))
    platforms.append(Platform(3000, 384,  52, 14))
    platforms.append(Platform(3010, 306,  52, 14))
    platforms.append(Platform(3010, 228, 120, 14))         # topo da torre

    return platforms


def create_checkpoints():
    return [
        Checkpoint( 430, 540),   # CP1 — início após gap
        Checkpoint(1560, 540),   # CP2 — ponte suspensa
        Checkpoint(2210, 540),   # CP3 — corredor de blocos
        Checkpoint(2760, 462),   # CP4 — plataformas no céu (plataforma flutuante)
        Checkpoint(2985, 540),   # CP5 — arena do boss
    ]


def create_enemies():
    return [
        # Zone 1
        GreenWarrior(100,  490,   0,  300),
        Ghost(       460,  435, 423,  560),
        GreenMelee(  650,  490, 423,  850),
        SpikeBall(   780,  330, 618,  858),
        GreenWarrior(1000, 420, 936, 1066),
        Ghost(       1180, 320,1118, 1365),

        # Zone 2 — ponte suspensa
        SpikeBall(   1840, 435,1800, 1970),
        GreenMelee(  1960, 357,1900, 2100),

        # Zone 3 — corredor de blocos
        GreenWarrior(2300, 490,2200, 2450),
        SpikeBall(   2480, 357,2380, 2560),
        GreenMelee(  2620, 490,2550, 2750),
        Ghost(       2680, 253,2650, 2750),

        # Zone 4 — plataformas no céu
        Ghost(       2850, 357,2820, 2960),
        SpikeBall(   2990, 279,2960, 3080),

        # Zone 5 — guardas antes da arena do boss
        GreenWarrior(3000, 476, 2980, 3080),
        SpikeBall(   3060, 476, 2980, 3120),
    ]


# ==============================================================================
# Camera
# ==============================================================================

class Camera:
    """Smooth horizontal-scrolling camera; lerps toward the player center."""

    SMOOTH = 8.0

    def __init__(self):
        self.x = 0.0

    def update(self, player_rect, dt):
        target = float(player_rect.centerx - WIDTH // 2)
        target = max(0.0, min(target, float(LEVEL_WIDTH - WIDTH)))
        self.x += (target - self.x) * min(1.0, self.SMOOTH * dt)

    @property
    def int_x(self):
        return int(self.x)


# ==============================================================================
# Game
# ==============================================================================

class Game:
    """Top-level controller: main loop, character roster, camera, HUD."""

    SPAWN = (40, 490)

    def __init__(self):
        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("2D Platformer")
        self.clock   = pygame.time.Clock()
        self.font_sm = pygame.font.SysFont("monospace", 16)
        self.font_md = pygame.font.SysFont("monospace", 22, bold=True)
        self.running = True
        self.state   = "MAIN_MENU"

        music_path = os.path.join(os.path.dirname(__file__),
                                   "music", "exploration-chiptune-rpg-adventure-theme.mp3")
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)   # -1 = loop infinito

        bg_path = os.path.join(os.path.dirname(__file__),
                               "sprites", "enemy", "tileset", "2 Background", "Background.png")
        raw_bg = pygame.image.load(bg_path).convert()
        self.background = pygame.transform.scale(raw_bg, (WIDTH, HEIGHT))

        self._init_level()

        self.main_menu  = MainMenu(self.background, os.path.exists(SAVE_PATH))
        self.pause_menu = PauseMenu()

    # ------------------------------------------------------------------
    # Level / character initialisation
    # ------------------------------------------------------------------

    def _init_level(self):
        self.platforms   = create_level()
        self.enemies     = create_enemies()
        self.checkpoints = create_checkpoints()
        self.spawn       = list(self.SPAWN)   # mutable, updated by checkpoints
        sx, sy = self.spawn
        self.characters = [
            Warrior(sx, sy),
            Mage   (sx, sy),
            Druid  (sx, sy),
            Rogue  (sx, sy),
        ]
        self.idx    = 0
        self.lives  = 3
        self.camera = Camera()
        # Boss spawns on Zone 5 arena (platform top = 540, boss height = 64)
        self.boss   = Boss(3150, 476, 2995, 3285)

    @property
    def player(self):
        return self.characters[self.idx]

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def save_game(self):
        p = self.player
        broken = [
            [pl.rect.x, pl.rect.y]
            for pl in self.platforms
            if getattr(pl, "breakable", False) and pl.broken
        ]
        active_cps = [cp.spawn_x for cp in self.checkpoints if cp.active]
        data = {
            "player_idx":  self.idx,
            "position":    [p.rect.centerx, p.rect.bottom],
            "spawn":       self.spawn,
            "lives":       self.lives,
            "broken_blocks": broken,
            "checkpoints": active_cps,
        }
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f)

    def load_game(self):
        if not os.path.exists(SAVE_PATH):
            return
        with open(SAVE_PATH) as f:
            data = json.load(f)

        self._init_level()
        self.idx   = data.get("player_idx", 0)
        self.spawn = data.get("spawn", list(self.SPAWN))
        self.lives = data.get("lives", 3)
        cx, cy     = data.get("position", self.spawn)
        for ch in self.characters:
            ch.rect.centerx = cx
            ch.rect.bottom  = cy

        for bx, by in data.get("broken_blocks", []):
            for pl in self.platforms:
                if getattr(pl, "breakable", False) and pl.rect.x == bx and pl.rect.y == by:
                    pl.broken = True

        active_cps = set(data.get("checkpoints", []))
        for cp in self.checkpoints:
            if cp.spawn_x in active_cps:
                cp.active = True

    # ------------------------------------------------------------------
    # Character switch
    # ------------------------------------------------------------------

    def _switch_character(self):
        old      = self.player
        self.idx = (self.idx + 1) % len(self.characters)
        new      = self.player

        new.rect.centerx = old.rect.centerx
        new.rect.bottom  = old.rect.bottom
        new.vx           = old.vx
        new.vy           = old.vy
        new.on_ground    = old.on_ground
        new.jumps_left   = new.MAX_JUMPS if old.on_ground else 0
        new.projectiles  = []

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        while self.running:
            dt     = min(self.clock.tick(FPS) / 1000.0, 0.05)
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            if self.state == "MAIN_MENU":
                self._run_main_menu(events)
            elif self.state == "PLAYING":
                self._run_playing(events, dt)
            elif self.state == "PAUSED":
                self._run_paused(events, dt)

        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------

    def _run_main_menu(self, events):
        self.main_menu.handle_events(events)
        if self.main_menu.choice == "new":
            self._init_level()
            self.state = "PLAYING"
        elif self.main_menu.choice == "load":
            self.load_game()
            self.state = "PLAYING"
        self.main_menu.choice = None
        self.main_menu.draw(self.screen)

    def _run_playing(self, events, dt):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.pause_menu._sel    = 0
                    self.pause_menu.choice  = None
                    self.state = "PAUSED"
                    return
                elif event.key == pygame.K_TAB:
                    self._switch_character()

        keys = pygame.key.get_pressed()
        p    = self.player
        p.use_ability(events, self.platforms)
        p.handle_input(keys, events)
        p.update(dt, self.platforms)

        for cp in self.checkpoints:
            if cp.try_activate(p.rect):
                self.spawn = [cp.spawn_x, cp.spawn_y]

        # Spider strike — area of effect
        if getattr(p, 'spider_strike_active', False):
            scx, scy = p.spider_center
            r = p.SPIDER_RADIUS
            for enemy in self.enemies:
                if enemy.alive:
                    import math
                    dx = enemy.rect.centerx - scx
                    dy = enemy.rect.centery - scy
                    if math.hypot(dx, dy) <= r:
                        enemy.kill()

        atk_rect = p.attack_rect
        for proj in p.projectiles:
            proj_rect = pygame.Rect(int(proj.x) - proj.radius, int(proj.y) - proj.radius,
                                    proj.radius * 2, proj.radius * 2)
            for enemy in self.enemies:
                if enemy.alive and proj_rect.colliderect(enemy.rect):
                    enemy.kill()
                    proj.active = False
            if self.boss.alive and proj_rect.colliderect(self.boss.rect):
                self.boss.damage()
                proj.active = False

        for enemy in self.enemies:
            enemy.update(dt, self.platforms)
            if not enemy.alive:
                continue
            if atk_rect and atk_rect.colliderect(enemy.rect):
                enemy.kill()
            elif enemy.collides_with_player(p.rect):
                self._lose_life()
                return

        # Boss update + combat
        self.boss.update(dt, self.platforms, p.rect)
        if self.boss.alive:
            if atk_rect and atk_rect.colliderect(self.boss.rect):
                self.boss.damage()
            if getattr(p, 'spider_strike_active', False):
                scx, scy = p.spider_center
                import math as _math
                dx = self.boss.rect.centerx - scx
                dy = self.boss.rect.centery - scy
                if _math.hypot(dx, dy) <= p.SPIDER_RADIUS:
                    self.boss.damage()
            # Stomp shockwave hurts player
            if self.boss.stomp_active:
                import math as _math2
                scx, scy = self.boss.stomp_center
                dx = p.rect.centerx - scx
                dy = p.rect.centery - scy
                if _math2.hypot(dx, dy) <= self.boss.STOMP_RADIUS:
                    self._lose_life()
                    return
            # Charge / contact hurts player
            if self.boss.alive and self.boss.rect.colliderect(p.rect):
                self._lose_life()
                return
        if not self.boss.alive and self.boss.hp <= 0:
            self._draw_victory()
            return

        self.camera.update(p.rect, dt)

        if p.rect.top > HEIGHT + 80:
            self._lose_life()
            return

        self._draw_game()

    def _lose_life(self):
        self.lives -= 1
        p = self.player
        if self.lives <= 0:
            self._draw_game_over()
        else:
            p.rect.centerx, p.rect.bottom = self.spawn
            p.vx = p.vy = 0.0

    def _draw_game_over(self):
        font_lg = pygame.font.SysFont("monospace", 52, bold=True)
        font_sm = pygame.font.SysFont("monospace", 22)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        t = font_lg.render("GAME OVER", True, (220, 40, 40))
        s = font_sm.render("Pressione ENTER para o menu principal", True, (200, 200, 200))
        self.screen.blit(t, ((WIDTH - t.get_width()) // 2, HEIGHT // 2 - 50))
        self.screen.blit(s, ((WIDTH - s.get_width()) // 2, HEIGHT // 2 + 20))
        pygame.display.flip()
        # Wait for ENTER
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self._init_level()
                    self.main_menu._sel   = 0
                    self.main_menu.choice = None
                    self.state = "MAIN_MENU"
                    return

    def _run_paused(self, events, dt):
        self.pause_menu.handle_events(events)
        choice = self.pause_menu.choice

        if choice == "resume":
            self.state = "PLAYING"
            self.pause_menu.choice = None
        elif choice == "save":
            self.save_game()
            self.pause_menu.show_message("Jogo salvo!")
            self.pause_menu.choice = None
            self.main_menu.has_save = True
        elif choice == "main_menu":
            self.main_menu.has_save = os.path.exists(SAVE_PATH)
            self.main_menu.choice   = None
            self.main_menu._sel     = 0
            self.state = "MAIN_MENU"
            self.pause_menu.choice  = None

        self._draw_game()
        self.pause_menu.draw(self.screen, dt)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw_boss_hud(self):
        bar_w  = 300
        bar_h  = 14
        bx     = (WIDTH - bar_w) // 2
        by     = 10
        ratio  = self.boss.hp / self.boss.MAX_HP

        # Background
        panel = pygame.Surface((bar_w + 20, bar_h + 22), pygame.SRCALPHA)
        panel.fill((10, 10, 10, 190))
        self.screen.blit(panel, (bx - 10, by - 4))

        label = self.font_sm.render("CHEFE FINAL", True, (255, 80, 80))
        self.screen.blit(label, (bx + (bar_w - label.get_width()) // 2, by))

        by2 = by + 14
        pygame.draw.rect(self.screen, (60,  0,  0),  (bx, by2, bar_w, bar_h))
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            # Gradient: dark red → bright red based on remaining HP
            r_col = (180 + int(75 * ratio), 20, 20)
            pygame.draw.rect(self.screen, r_col, (bx, by2, fill_w, bar_h))
        pygame.draw.rect(self.screen, (255, 80, 80), (bx, by2, bar_w, bar_h), 1)

        # HP pips
        pip_w = bar_w // self.boss.MAX_HP - 2
        for i in range(self.boss.MAX_HP):
            px = bx + i * (bar_w // self.boss.MAX_HP)
            pygame.draw.line(self.screen, (10, 10, 10),
                             (px, by2), (px, by2 + bar_h), 1)

    def _draw_victory(self):
        font_lg = pygame.font.SysFont("monospace", 54, bold=True)
        font_md = pygame.font.SysFont("monospace", 24)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        t1 = font_lg.render("VITÓRIA!", True, (255, 215, 0))
        t2 = font_md.render("Você derrotou o Chefe Final!", True, (220, 220, 220))
        t3 = font_md.render("Pressione ENTER para o menu principal", True, (160, 160, 160))
        self.screen.blit(t1, ((WIDTH - t1.get_width()) // 2, HEIGHT // 2 - 80))
        self.screen.blit(t2, ((WIDTH - t2.get_width()) // 2, HEIGHT // 2 + 10))
        self.screen.blit(t3, ((WIDTH - t3.get_width()) // 2, HEIGHT // 2 + 50))
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self._init_level()
                    self.main_menu._sel   = 0
                    self.main_menu.choice = None
                    self.state = "MAIN_MENU"
                    return

    def _draw_cooldown_bars(self, player):
        bars      = getattr(player, 'cooldown_bars', [])
        bar_w     = 90
        bar_h     = 8
        label_h   = 13
        slot_w    = bar_w + 16
        slot_h    = label_h + bar_h + 10
        padding   = 10
        total_w   = len(bars) * slot_w + (len(bars) - 1) * 6
        base_x    = (WIDTH - total_w) // 2
        base_y    = HEIGHT - 58

        font = pygame.font.SysFont("monospace", 11, bold=True)

        for i, (key, name, cd, max_cd) in enumerate(bars):
            x = base_x + i * (slot_w + 6)
            y = base_y

            # Background panel
            panel = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            panel.fill((10, 10, 10, 180))
            self.screen.blit(panel, (x, y))

            # Key + name label
            label = font.render(f"[{key}] {name}", True, (180, 180, 180))
            self.screen.blit(label, (x + (slot_w - label.get_width()) // 2, y + 3))

            # Bar background
            bx, by = x + 4, y + label_h + 5
            pygame.draw.rect(self.screen, (40, 40, 40), (bx, by, bar_w, bar_h))

            # Bar fill — ratio 1.0 = ready, 0.0 = just used
            ratio = 1.0 - (cd / max_cd) if max_cd > 0 else 1.0
            fill  = int(bar_w * ratio)
            if fill > 0:
                if ratio >= 1.0:
                    color = (212, 175, 55)    # gold — ready
                else:
                    r = int(100 + 112 * ratio)
                    color = (r, int(80 * ratio), 10)   # dark orange → gold
                pygame.draw.rect(self.screen, color, (bx, by, fill, bar_h))

            # Border
            pygame.draw.rect(self.screen, (80, 80, 80), (bx, by, bar_w, bar_h), 1)

    def _draw_game(self):
        self.screen.blit(self.background, (0, 0))
        cam_x = self.camera.int_x

        for plat in self.platforms:
            plat.draw(self.screen, cam_x)

        for cp in self.checkpoints:
            cp.draw(self.screen, cam_x)

        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x)

        self.boss.draw(self.screen, cam_x)
        self.player.draw(self.screen, cam_x)

        p = self.player

        name_surf = self.font_md.render("[ " + p.NAME + " ]", True, BLACK)
        self.screen.blit(name_surf, (10, 10))

        # Lives — red hearts
        for i in range(3):
            color = (210, 30, 30) if i < self.lives else (60, 60, 60)
            hx = 10 + i * 22
            pygame.draw.circle(self.screen, color, (hx + 5,  56), 6)
            pygame.draw.circle(self.screen, color, (hx + 15, 56), 6)
            pts = [(hx, 59), (hx + 10, 70), (hx + 20, 59)]
            pygame.draw.polygon(self.screen, color, pts)

        hints = {
            "Guerreiro": "SPACE - Quebrar bloco   T - Golpe de aranha",
            "Mago":      "SPACE - Lançar projétil",
            "Druida":    "W/Cima duas vezes - Duplo salto (passivo)",
            "Ladino":    "L-SHIFT - Dash",
        }
        hint_surf = self.font_sm.render(hints.get(p.NAME, ""), True, DARK_GRAY)
        self.screen.blit(hint_surf, (10, 38))

        dot_colors = [C_WARRIOR, C_MAGE, C_DRUID, C_ROGUE]
        dot_labels = ["Gu", "Ma", "Dr", "La"]
        for i, (col, lbl) in enumerate(zip(dot_colors, dot_labels)):
            dx = WIDTH - 160 + i * 38
            dy = 14
            pygame.draw.circle(self.screen, col, (dx, dy), 10)
            if i == self.idx:
                pygame.draw.circle(self.screen, BLACK, (dx, dy), 10, 2)
            ls = self.font_sm.render(lbl, True, BLACK)
            self.screen.blit(ls, (dx - ls.get_width() // 2, dy + 14))

        self._draw_cooldown_bars(p)

        # Boss HP bar — shown at top-center when boss is alive
        if self.boss.alive:
            self._draw_boss_hud()

        ctrl_surf = self.font_sm.render(
            "A/D - Mover   W - Pular   J - Atacar   TAB - Trocar   ESC - Pause",
            True, DARK_GRAY,
        )
        self.screen.blit(ctrl_surf, (10, HEIGHT - 24))

        fps_surf = self.font_sm.render("FPS " + str(int(self.clock.get_fps())), True, DARK_GRAY)
        self.screen.blit(fps_surf, (WIDTH - 70, HEIGHT - 24))

        pygame.display.flip()


# ==============================================================================
# Entry point
# ====================
#==========================================================

if __name__ == "__main__":
    Game().run()
