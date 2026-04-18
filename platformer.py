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

import pygame
import sys
import os

pygame.init()

# ==============================================================================
# Sprite animation
# ==============================================================================

FRAME_W = 32
FRAME_H = 32

ANIMATIONS = {
    #                 row  frames  fps  start_col
    "idle":       {"row": 1, "frames": 1, "fps": 1,  "start_col": 1},  # middle frame of walk row
    "walk_left":  {"row": 1, "frames": 3, "fps": 8,  "start_col": 0},
    "walk_right": {"row": 2, "frames": 3, "fps": 8,  "start_col": 0},
    "jump":       {"row": 2, "frames": 1, "fps": 1,  "start_col": 1},  # middle frame, static
}

_sprite_cache = {}

def _load_sheet(path):
    if path not in _sprite_cache:
        sheet = pygame.image.load(path).convert_alpha()
        _sprite_cache[path] = sheet
    return _sprite_cache[path]

def get_frame(sheet, row, col):
    frame = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
    frame.blit(sheet, (0, 0), (col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H))
    return frame

# ==============================================================================
# Constants
# ==============================================================================

WIDTH       = 800
HEIGHT      = 600
FPS         = 60
GRAVITY     = 900       # pixels per second squared
LEVEL_WIDTH = 2200      # total horizontal level extent

# ==============================================================================
# Colours
# ==============================================================================

SKY       = (135, 206, 235)
BLACK     = (  0,   0,   0)
DARK_GRAY = ( 50,  50,  50)
GRAY      = (110, 110, 110)
BROWN     = (101,  67,  33)
BREAK_COL = (180, 100,  30)

# Character colours
C_WARRIOR = (220,  40,  40)   # red
C_MAGE    = (148,   0, 211)   # purple
C_DRUID   = ( 34, 139,  34)   # green
C_ROGUE   = (255, 140,   0)   # orange

C_PROJ    = (  0, 230, 230)   # cyan projectile


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
        r = pygame.Rect(self.rect.x - cam_x, self.rect.y,
                        self.rect.w, self.rect.h)
        pygame.draw.rect(surface, self.color, r)
        pygame.draw.rect(surface, DARK_GRAY, r, 2)


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
        # Cross marker signals "breakable"
        cx, cy = r.centerx, r.centery
        pygame.draw.line(surface, (90, 45, 0), (cx - 8, cy - 8), (cx + 8, cy + 8), 2)
        pygame.draw.line(surface, (90, 45, 0), (cx + 8, cy - 8), (cx - 8, cy + 8), 2)


# ==============================================================================
# Projectile
# ==============================================================================

class Projectile:
    """Simple circle projectile fired by the Mage."""

    def __init__(self, x, y, direction, speed=420, radius=7):
        self.x      = float(x)
        self.y      = float(y)
        self.vx     = speed * direction
        self.radius = radius
        self.active = True

    def update(self, dt):
        self.x += self.vx * dt
        if self.x < -200 or self.x > LEVEL_WIDTH + 200:
            self.active = False

    def draw(self, surface, cam_x):
        if self.active:
            pygame.draw.circle(surface, C_PROJ,
                               (int(self.x - cam_x), int(self.y)), self.radius)


# ==============================================================================
# AnimatedSprite
# ==============================================================================

class AnimatedSprite:
    """Handles frame timing and drawing for a single spritesheet."""

    def __init__(self, sheet_path):
        self._sheet    = _load_sheet(sheet_path)
        self._anim     = "idle"
        self._col      = 0
        self._timer    = 0.0

    def set_animation(self, name):
        if name != self._anim:
            self._anim  = name
            self._col   = 0
            self._timer = 0.0

    def update(self, dt):
        anim = ANIMATIONS[self._anim]
        self._timer += dt
        if self._timer >= 1.0 / anim["fps"]:
            self._timer = 0.0
            self._col   = (self._col + 1) % anim["frames"]

    def draw(self, surface, dest_rect, cam_x):
        anim  = ANIMATIONS[self._anim]
        frame = get_frame(self._sheet, anim["row"], self._col)
        # Scale frame to the player's bounding box and center it
        scaled = pygame.transform.scale(frame, (dest_rect.w, dest_rect.h))
        surface.blit(scaled, (dest_rect.x - cam_x, dest_rect.y))


# ==============================================================================
# Player base
# ==============================================================================

class Player:
    """
    Base player. Subclasses override class-level stats and use_ability().
    Physics: AABB collision against Platforms, constant GRAVITY downward.
    """

    NAME        = "Player"
    COLOR       = (200, 200, 200)
    WIDTH       = 30
    HEIGHT      = 40
    SPEED       = 200
    JUMP_FORCE  = -480       # negative = upward
    MAX_JUMPS   = 1
    SPRITE_FILE = None       # set in subclasses

    _SPRITES_DIR = os.path.join(os.path.dirname(__file__), "sprites", "character")

    def __init__(self, x, y):
        self.rect        = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.vx          = 0.0
        self.vy          = 0.0
        self.on_ground   = False
        self.jumps_left  = self.MAX_JUMPS
        self.facing      = 1           # 1 = right, -1 = left
        self.projectiles = []

        if self.SPRITE_FILE:
            path = os.path.join(self._SPRITES_DIR, self.SPRITE_FILE)
            self._sprite = AnimatedSprite(path)
        else:
            self._sprite = None

    # --------------------------------------------------------------------------
    # Input
    # --------------------------------------------------------------------------

    def handle_input(self, keys, events):
        """Standard horizontal movement and jump."""
        self.vx = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -self.SPEED
            self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = self.SPEED
            self.facing = 1

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    if self.jumps_left > 0:
                        self.vy = self.JUMP_FORCE
                        self.jumps_left -= 1

    def use_ability(self, events, platforms):
        """Override in subclasses to add special moves."""
        pass

    # --------------------------------------------------------------------------
    # Physics
    # --------------------------------------------------------------------------

    def update(self, dt, platforms):
        # Apply gravity
        self.vy += GRAVITY * dt

        # Horizontal movement then collision
        self.rect.x += int(self.vx * dt)
        self._resolve_h(platforms)

        # Vertical movement then collision
        self.rect.y += int(self.vy * dt)
        self.on_ground = False
        self._resolve_v(platforms)

        # Replenish jumps on landing
        if self.on_ground:
            self.jumps_left = self.MAX_JUMPS

        # Hard left wall
        if self.rect.left < 0:
            self.rect.left = 0

        # Update and prune projectiles
        self.projectiles = [p for p in self.projectiles if p.active]
        for p in self.projectiles:
            p.update(dt)

        # Sprite animation state
        if self._sprite:
            if not self.on_ground:
                anim = "jump"
            elif self.vx < 0:
                anim = "walk_left"
            elif self.vx > 0:
                anim = "walk_right"
            else:
                anim = "idle"
            self._sprite.set_animation(anim)
            self._sprite.update(dt)

    def _iter_solid(self, platforms):
        """Yield platforms that are currently solid (skips broken blocks)."""
        for plat in platforms:
            if isinstance(plat, BreakableBlock) and plat.broken:
                continue
            yield plat

    def _resolve_h(self, platforms):
        for plat in self._iter_solid(platforms):
            if self.rect.colliderect(plat.rect):
                if self.vx > 0:
                    self.rect.right = plat.rect.left
                elif self.vx < 0:
                    self.rect.left  = plat.rect.right
                self.vx = 0.0

    def _resolve_v(self, platforms):
        for plat in self._iter_solid(platforms):
            if self.rect.colliderect(plat.rect):
                if self.vy > 0:
                    self.rect.bottom = plat.rect.top
                    self.on_ground   = True
                    self.vy          = 0.0
                elif self.vy < 0:
                    self.rect.top = plat.rect.bottom
                    self.vy       = 0.0

    # --------------------------------------------------------------------------
    # Draw
    # --------------------------------------------------------------------------

    def draw(self, surface, cam_x):
        if self._sprite:
            self._sprite.draw(surface, self.rect, cam_x)
        else:
            r = pygame.Rect(self.rect.x - cam_x, self.rect.y,
                            self.rect.w, self.rect.h)
            pygame.draw.rect(surface, self.COLOR, r)
            pygame.draw.rect(surface, BLACK, r, 2)

            eye_y = r.top + max(6, r.h // 5)
            eye_x = (r.right - 8) if self.facing == 1 else (r.left + 8)
            pygame.draw.circle(surface, BLACK, (eye_x, eye_y), 3)

        # Draw own projectiles
        for p in self.projectiles:
            p.draw(surface, cam_x)


# ==============================================================================
# Character subclasses
# ==============================================================================

class Warrior(Player):
    """
    Tank fighter.
    - Slow speed, low jump.
    - SPACE: smash the breakable block directly in front.
    """

    NAME        = "Warrior"
    COLOR       = C_WARRIOR
    WIDTH       = 36
    HEIGHT      = 50
    SPEED       = 140
    JUMP_FORCE  = -370
    MAX_JUMPS   = 1
    SPRITE_FILE = "pipo-nekonin001.png"

    def __init__(self, x, y):
        super().__init__(x, y)
        self._break_cd = 0.0       # cooldown between smashes

    def update(self, dt, platforms):
        super().update(dt, platforms)
        self._break_cd = max(0.0, self._break_cd - dt)

    def use_ability(self, events, platforms):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self._break_cd <= 0:
                    self._smash(platforms)

    def _smash(self, platforms):
        """Destroy the nearest breakable block directly ahead."""
        probe = pygame.Rect(
            self.rect.x + self.facing * self.rect.w,
            self.rect.y,
            self.rect.w,
            self.rect.h,
        )
        for plat in platforms:
            if isinstance(plat, BreakableBlock) and not plat.broken:
                if probe.colliderect(plat.rect):
                    plat.broken    = True
                    self._break_cd = 0.5
                    break


class Mage(Player):
    """
    Balanced caster.
    - Medium speed and jump.
    - SPACE: shoot a cyan projectile forward.
    """

    NAME        = "Mage"
    COLOR       = C_MAGE
    WIDTH       = 28
    HEIGHT      = 38
    SPEED       = 200
    JUMP_FORCE  = -480
    MAX_JUMPS   = 1
    SPRITE_FILE = "pipo-nekonin005.png"

    def __init__(self, x, y):
        super().__init__(x, y)
        self._shoot_cd = 0.0

    def update(self, dt, platforms):
        super().update(dt, platforms)
        self._shoot_cd = max(0.0, self._shoot_cd - dt)

    def use_ability(self, events, platforms):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self._shoot_cd <= 0:
                    offset_x = self.facing * (self.WIDTH // 2 + 6)
                    self.projectiles.append(
                        Projectile(
                            self.rect.centerx + offset_x,
                            self.rect.centery,
                            self.facing,
                        )
                    )
                    self._shoot_cd = 0.3


class Druid(Player):
    """
    Nature jumper.
    - Slightly slower movement.
    - High jump force + double-jump (passive: MAX_JUMPS = 2).
    """

    NAME        = "Druid"
    COLOR       = C_DRUID
    WIDTH       = 30
    HEIGHT      = 42
    SPEED       = 170
    JUMP_FORCE  = -630
    MAX_JUMPS   = 2       # double jump is the passive ability
    SPRITE_FILE = "pipo-nekonin009.png"


class Rogue(Player):
    """
    Speedster.
    - Fastest base movement.
    - Left SHIFT: dash (brief very-high-speed burst).
    """

    NAME          = "Rogue"
    COLOR         = C_ROGUE
    WIDTH         = 24
    HEIGHT        = 36
    SPEED         = 320
    JUMP_FORCE    = -480
    MAX_JUMPS     = 1
    SPRITE_FILE   = "pipo-nekonin013.png"

    DASH_SPEED    = 850
    DASH_DURATION = 0.18
    DASH_COOLDOWN = 0.80

    def __init__(self, x, y):
        super().__init__(x, y)
        self._dashing    = False
        self._dash_timer = 0.0
        self._dash_cd    = 0.0
        self._dash_dir   = 1

    def update(self, dt, platforms):
        # Tick dash timers before physics so vx override is applied correctly
        if self._dashing:
            self._dash_timer -= dt
            if self._dash_timer <= 0:
                self._dashing = False
        self._dash_cd = max(0.0, self._dash_cd - dt)
        super().update(dt, platforms)

    def handle_input(self, keys, events):
        super().handle_input(keys, events)
        if self._dashing:
            # Override horizontal velocity with dash speed
            self.vx = self.DASH_SPEED * self._dash_dir

    def use_ability(self, events, platforms):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_LSHIFT:
                if not self._dashing and self._dash_cd <= 0:
                    self._dashing    = True
                    self._dash_timer = self.DASH_DURATION
                    self._dash_cd    = self.DASH_COOLDOWN
                    self._dash_dir   = self.facing

    def draw(self, surface, cam_x):
        super().draw(surface, cam_x)
        # Semi-transparent white flash while dashing
        if self._dashing:
            r = pygame.Rect(self.rect.x - cam_x, self.rect.y,
                            self.rect.w, self.rect.h)
            flash = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 90))
            surface.blit(flash, r.topleft)


# ==============================================================================
# Level definition
# ==============================================================================

def create_level():
    """
    World layout (not to scale):

      x=0          x=500  gap  x=650                      x=2200
      [== ground ==]      150px[====== ground continues ========]

    Key sections:
      - Gap at x 500-650  : 150 px wide, best crossed with Druid's high jump
      - Breakable wall at x~790 : Warrior smashes through; others must go around
      - Speed corridor x 900-1300 : open ground, Rogue shines
      - Tall tower x 1440-1600  : stacked short platforms, needs Druid double-jump
    """
    platforms = []

    # Ground (split by gap)
    platforms.append(Platform(   0, 560,  500, 40, BROWN))  # left ground
    platforms.append(Platform( 650, 560, 1550, 40, BROWN))  # right ground

    # Left warm-up platforms
    platforms.append(Platform( 120, 460,  120, 18))
    platforms.append(Platform( 300, 390,  100, 18))
    platforms.append(Platform( 440, 320,  120, 18))         # launch pad above gap

    # After-gap platforms
    platforms.append(Platform( 670, 470,  160, 18))
    platforms.append(Platform( 870, 400,  100, 18))

    # Breakable wall (two stacked blocks blocking ground-level path)
    platforms.append(BreakableBlock(790, 520, 40, 40))
    platforms.append(BreakableBlock(790, 480, 40, 40))

    # Speed corridor (x 950-1350)
    platforms.append(Platform( 950, 340,  180, 18))
    platforms.append(Platform(1160, 270,  160, 18))
    platforms.append(Platform(1320, 340,  140, 18))

    # Tall tower (Druid showcase, x 1440-1600)
    platforms.append(Platform(1440, 480,   80, 18))
    platforms.append(Platform(1500, 390,   80, 18))
    platforms.append(Platform(1560, 300,   80, 18))
    platforms.append(Platform(1560, 210,  140, 18))         # tower summit

    # Final stretch
    platforms.append(Platform(1720, 350,  200, 18))
    platforms.append(Platform(1950, 440,  180, 18))
    platforms.append(Platform(2080, 360,  100, 18))         # finish platform

    return platforms


# ==============================================================================
# Camera
# ==============================================================================

class Camera:
    """Smooth horizontal-scrolling camera; lerps toward the player center."""

    SMOOTH = 8.0    # lerp speed (higher = snappier)

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

    SPAWN = (60, 490)

    def __init__(self):
        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("2D Platformer")
        self.clock   = pygame.time.Clock()
        self.font_sm = pygame.font.SysFont("monospace", 16)
        self.font_md = pygame.font.SysFont("monospace", 22, bold=True)
        self.running = True

        self.platforms = create_level()

        sx, sy = self.SPAWN
        self.characters = [
            Warrior(sx, sy),
            Mage   (sx, sy),
            Druid  (sx, sy),
            Rogue  (sx, sy),
        ]
        self.idx = 0

        self.camera       = Camera()
        self._tab_held    = False

    @property
    def player(self):
        return self.characters[self.idx]

    # --------------------------------------------------------------------------
    # Character switch
    # --------------------------------------------------------------------------

    def _switch_character(self):
        """Cycle to the next character, carrying over position and velocity."""
        old       = self.player
        self.idx  = (self.idx + 1) % len(self.characters)
        new       = self.player

        new.rect.centerx = old.rect.centerx
        new.rect.bottom  = old.rect.bottom
        new.vx           = old.vx
        new.vy           = old.vy
        new.on_ground    = old.on_ground
        new.jumps_left   = new.MAX_JUMPS if old.on_ground else 0
        new.projectiles  = []

    # --------------------------------------------------------------------------
    # Main loop
    # --------------------------------------------------------------------------

    def run(self):
        while self.running:
            # Cap dt to avoid tunnelling after focus loss
            dt     = min(self.clock.tick(FPS) / 1000.0, 0.05)
            events = pygame.event.get()

            # System events
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False

            keys = pygame.key.get_pressed()

            # TAB: switch character (debounced)
            if keys[pygame.K_TAB]:
                if not self._tab_held:
                    self._switch_character()
                self._tab_held = True
            else:
                self._tab_held = False

            # Update active player
            p = self.player
            p.use_ability(events, self.platforms)   # abilities before movement
            p.handle_input(keys, events)
            p.update(dt, self.platforms)

            # Camera follows player
            self.camera.update(p.rect, dt)

            # Respawn if fell off screen
            if p.rect.top > HEIGHT + 80:
                p.rect.topleft = self.SPAWN
                p.vx = p.vy = 0.0

            self._draw()

        pygame.quit()
        sys.exit()

    # --------------------------------------------------------------------------
    # Drawing
    # --------------------------------------------------------------------------

    def _draw(self):
        self.screen.fill(SKY)
        cam_x = self.camera.int_x

        # Level
        for plat in self.platforms:
            plat.draw(self.screen, cam_x)

        # Active character
        self.player.draw(self.screen, cam_x)

        # HUD ----------------------------------------------------------------

        p = self.player

        # Character name (top-left)
        name_surf = self.font_md.render("[ " + p.NAME + " ]", True, BLACK)
        self.screen.blit(name_surf, (10, 10))

        # Ability hint (below name)
        hints = {
            "Warrior": "SPACE - Break block",
            "Mage":    "SPACE - Shoot",
            "Druid":   "W/Up twice - Double jump (passive)",
            "Rogue":   "L-SHIFT - Dash",
        }
        hint = hints.get(p.NAME, "")
        hint_surf = self.font_sm.render(hint, True, DARK_GRAY)
        self.screen.blit(hint_surf, (10, 38))

        # Character selector dots (top-right)
        dot_colors = [C_WARRIOR, C_MAGE, C_DRUID, C_ROGUE]
        dot_labels = ["W", "M", "Dr", "Ro"]
        for i, (col, lbl) in enumerate(zip(dot_colors, dot_labels)):
            dx = WIDTH - 160 + i * 38
            dy = 14
            pygame.draw.circle(self.screen, col, (dx, dy), 10)
            if i == self.idx:
                pygame.draw.circle(self.screen, BLACK, (dx, dy), 10, 2)
            ls = self.font_sm.render(lbl, True, BLACK)
            self.screen.blit(ls, (dx - ls.get_width() // 2, dy + 14))

        # Bottom bar (controls reminder)
        ctrl = "A/D - Move   W/Up - Jump   TAB - Switch char   ESC - Quit"
        ctrl_surf = self.font_sm.render(ctrl, True, DARK_GRAY)
        self.screen.blit(ctrl_surf, (10, HEIGHT - 24))

        # FPS (bottom-right)
        fps_surf = self.font_sm.render("FPS " + str(int(self.clock.get_fps())), True, DARK_GRAY)
        self.screen.blit(fps_surf, (WIDTH - 70, HEIGHT - 24))

        pygame.display.flip()


# ==============================================================================
# Entry point
# ==============================================================================

if __name__ == "__main__":
    Game().run()
