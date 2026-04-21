# -*- coding: utf-8 -*-
import pygame
import os
import math

from constants import (
    GRAVITY, LEVEL_WIDTH,
    BLACK, C_PROJ, DISPLAY_SCALE,
)

# ==============================================================================
# Sprite animation
# ==============================================================================

FRAME_W = 32
FRAME_H = 32

ANIMATIONS = {
    "idle_left":  {"row": 1, "frames": 1, "fps": 1,  "start_col": 1},
    "idle_right": {"row": 2, "frames": 1, "fps": 1,  "start_col": 1},
    "walk_left":  {"row": 1, "frames": 3, "fps": 8,  "start_col": 0},
    "walk_right": {"row": 2, "frames": 3, "fps": 8,  "start_col": 0},
    "jump":       {"row": 2, "frames": 1, "fps": 1,  "start_col": 1},
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


class Fireball:
    """Fireball projectile fired by the Guerreiro."""

    def __init__(self, x, y, direction, speed=340, radius=11):
        self.x       = float(x)
        self.y       = float(y)
        self.vx      = speed * direction
        self.radius  = radius
        self.active  = True
        self._timer  = 0.0   # for flicker animation

    def update(self, dt):
        self.x      += self.vx * dt
        self._timer += dt
        if self.x < -200 or self.x > LEVEL_WIDTH + 200:
            self.active = False

    def draw(self, surface, cam_x):
        if not self.active:
            return
        cx = int(self.x - cam_x)
        cy = int(self.y)
        # Outer glow — orange
        pygame.draw.circle(surface, (255, 100,   0), (cx, cy), self.radius)
        # Inner core — yellow, flickers
        inner = self.radius - 3 + int(2 * abs((self._timer * 12 % 2) - 1))
        pygame.draw.circle(surface, (255, 230,  50), (cx, cy), max(3, inner))


# ==============================================================================
# AnimatedSprite
# ==============================================================================

class AnimatedSprite:
    """Handles frame timing and drawing for a single spritesheet."""

    def __init__(self, sheet_path):
        self._sheet  = _load_sheet(sheet_path)
        self._anim   = "idle_right"
        self._col    = 0
        self._timer  = 0.0

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
        anim      = ANIMATIONS[self._anim]
        sheet_col = anim.get("start_col", 0) + self._col
        frame     = get_frame(self._sheet, anim["row"], sheet_col)
        dw = int(dest_rect.w * DISPLAY_SCALE)
        dh = int(dest_rect.h * DISPLAY_SCALE)
        dx = dest_rect.centerx - cam_x - dw // 2
        dy = dest_rect.bottom - dh          # bottom-aligned to hitbox
        scaled = pygame.transform.scale(frame, (dw, dh))
        surface.blit(scaled, (dx, dy))


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
    JUMP_FORCE  = -480
    MAX_JUMPS   = 1
    SPRITE_FILE = None

    _SPRITES_DIR = os.path.join(os.path.dirname(__file__), "sprites", "character")

    ATTACK_REACH    = 40    # hitbox width in front of player
    ATTACK_DURATION = 0.15  # seconds the hitbox stays active
    ATTACK_COOLDOWN = 0.40

    def __init__(self, x, y):
        self.rect        = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.vx          = 0.0
        self.vy          = 0.0
        self.on_ground   = False
        self.jumps_left  = self.MAX_JUMPS
        self.facing      = 1
        self.projectiles = []
        self._atk_timer  = 0.0   # > 0 while attack hitbox is active
        self._atk_cd     = 0.0   # cooldown between attacks

        if self.SPRITE_FILE:
            path = os.path.join(self._SPRITES_DIR, self.SPRITE_FILE)
            self._sprite = AnimatedSprite(path)
        else:
            self._sprite = None

    def handle_input(self, keys, events):
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
                elif event.key == pygame.K_j:
                    if self._atk_cd <= 0:
                        self._atk_timer = self.ATTACK_DURATION
                        self._atk_cd    = self.ATTACK_COOLDOWN

    def use_ability(self, events, platforms):
        pass

    def update(self, dt, platforms):
        self.vy += GRAVITY * dt

        self.rect.x += int(self.vx * dt)
        self._resolve_h(platforms)

        dy = int(self.vy * dt)
        if dy == 0 and self.on_ground:
            dy = 1  # keep player pressed against platform when gravity truncates to zero
        self.rect.y += dy
        self.on_ground = False
        self._resolve_v(platforms)

        if self.on_ground:
            self.jumps_left = self.MAX_JUMPS

        if self.rect.left < 0:
            self.rect.left = 0

        self._atk_timer = max(0.0, self._atk_timer - dt)
        self._atk_cd    = max(0.0, self._atk_cd    - dt)

        self.projectiles = [p for p in self.projectiles if p.active]
        for p in self.projectiles:
            p.update(dt)

        if self._sprite:
            if not self.on_ground:
                anim = "jump"
            elif self.vx < 0:
                anim = "walk_left"
            elif self.vx > 0:
                anim = "walk_right"
            else:
                anim = "idle_right" if self.facing == 1 else "idle_left"
            self._sprite.set_animation(anim)
            self._sprite.update(dt)

    def _iter_solid(self, platforms):
        for plat in platforms:
            if getattr(plat, 'breakable', False) and plat.broken:
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

    @property
    def attack_rect(self):
        """Active melee hitbox in front of player, or None."""
        if self._atk_timer <= 0:
            return None
        if self.facing == 1:
            x = self.rect.right
        else:
            x = self.rect.left - self.ATTACK_REACH
        return pygame.Rect(x, self.rect.top + self.rect.h // 4,
                           self.ATTACK_REACH, self.rect.h // 2)

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

        for p in self.projectiles:
            p.draw(surface, cam_x)

        ar = self.attack_rect
        if ar:
            slash = pygame.Surface((ar.w, ar.h), pygame.SRCALPHA)
            alpha = int(200 * (self._atk_timer / self.ATTACK_DURATION))
            slash.fill((255, 255, 100, alpha))
            surface.blit(slash, (ar.x - cam_x, ar.y))


# ==============================================================================
# Character subclasses
# ==============================================================================

class Warrior(Player):
    NAME        = "Guerreiro"
    COLOR       = (220,  40,  40)
    WIDTH       = 36
    HEIGHT      = 50
    SPEED       = 140
    JUMP_FORCE  = -520
    MAX_JUMPS   = 1
    SPRITE_FILE = "pipo-nekonin001.png"

    SPIDER_RADIUS   = 70
    SPIDER_DURATION = 0.30
    SPIDER_COOLDOWN = 1.8

    def __init__(self, x, y):
        super().__init__(x, y)
        self._break_cd     = 0.0
        self._spider_timer = 0.0
        self._spider_cd    = 0.0

    def update(self, dt, platforms):
        super().update(dt, platforms)
        self._break_cd     = max(0.0, self._break_cd    - dt)
        self._spider_timer = max(0.0, self._spider_timer - dt)
        self._spider_cd    = max(0.0, self._spider_cd   - dt)

    def use_ability(self, events, platforms):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self._break_cd <= 0:
                    self._smash(platforms)
                elif event.key == pygame.K_t and self._spider_cd <= 0:
                    self._spider_timer = self.SPIDER_DURATION
                    self._spider_cd    = self.SPIDER_COOLDOWN

    @property
    def spider_strike_active(self):
        return self._spider_timer > 0

    @property
    def spider_center(self):
        return self.rect.centerx, self.rect.centery

    def draw(self, surface, cam_x):
        super().draw(surface, cam_x)
        if not self.spider_strike_active:
            return

        progress = 1.0 - (self._spider_timer / self.SPIDER_DURATION)
        radius   = int(self.SPIDER_RADIUS * (0.3 + 0.7 * progress))
        alpha    = max(0, int(220 * (1.0 - progress)))
        cx       = self.rect.centerx - cam_x
        cy       = self.rect.centery

        # Draw once onto a single SRCALPHA surface
        fx, fy = cx - radius - 4, cy - radius - 4
        fw, fh = (radius + 4) * 2, (radius + 4) * 2
        fx = max(0, fx)
        fy = max(0, fy)
        fx, fy = int(fx), int(fy)
        buf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        lx, ly = cx - fx, cy - fy   # local coords inside buf

        # 8 web lines
        for i in range(8):
            angle = math.radians(i * 45 + progress * 180)
            ex = int(lx + radius * math.cos(angle))
            ey = int(ly + radius * math.sin(angle))
            pygame.draw.line(buf, (180, 80, 200, alpha), (int(lx), int(ly)), (ex, ey), 2)

        # Ring
        pygame.draw.circle(buf, (220, 60, 240, max(0, alpha - 40)),
                           (int(lx), int(ly)), radius, 3)

        surface.blit(buf, (fx, fy))

    @property
    def cooldown_bars(self):
        return [
            ("SPACE", "Quebrar", self._break_cd,    0.5),
            ("T",     "Aranha",  self._spider_cd,   self.SPIDER_COOLDOWN),
            ("J",     "Ataque",  self._atk_cd,      self.ATTACK_COOLDOWN),
        ]

    def _smash(self, platforms):
        overlap = 8
        reach   = self.rect.w + 24
        if self.facing == 1:
            px = self.rect.right - overlap
        else:
            px = self.rect.left - reach + overlap
        probe = pygame.Rect(px, self.rect.top, reach, self.rect.h)
        for plat in platforms:
            if getattr(plat, 'breakable', False) and not plat.broken:
                if probe.colliderect(plat.rect):
                    plat.broken    = True
                    self._break_cd = 0.5
                    break


class Mage(Player):
    NAME        = "Mago"
    COLOR       = (148,   0, 211)
    WIDTH       = 28
    HEIGHT      = 38
    SPEED       = 200
    JUMP_FORCE  = -620
    MAX_JUMPS   = 1
    SPRITE_FILE = "pipo-nekonin013.png"

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

    @property
    def cooldown_bars(self):
        return [
            ("SPACE", "Projétil", self._shoot_cd, 0.3),
            ("J",     "Ataque",   self._atk_cd,   self.ATTACK_COOLDOWN),
        ]


class Druid(Player):
    NAME        = "Druida"
    COLOR       = ( 34, 139,  34)
    WIDTH       = 30
    HEIGHT      = 42
    SPEED       = 170
    JUMP_FORCE  = -780
    MAX_JUMPS   = 2
    SPRITE_FILE = "pipo-nekonin009.png"

    @property
    def cooldown_bars(self):
        return [
            ("J", "Ataque", self._atk_cd, self.ATTACK_COOLDOWN),
        ]


class Rogue(Player):
    NAME          = "Ladino"
    COLOR         = (255, 140,   0)
    WIDTH         = 24
    HEIGHT        = 36
    SPEED         = 320
    JUMP_FORCE    = -620
    MAX_JUMPS     = 1
    SPRITE_FILE   = "pipo-nekonin005.png"

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
        if self._dashing:
            self._dash_timer -= dt
            if self._dash_timer <= 0:
                self._dashing = False
        self._dash_cd = max(0.0, self._dash_cd - dt)
        super().update(dt, platforms)

    def handle_input(self, keys, events):
        super().handle_input(keys, events)
        if self._dashing:
            self.vx = self.DASH_SPEED * self._dash_dir

    def use_ability(self, events, platforms):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_LSHIFT:
                if not self._dashing and self._dash_cd <= 0:
                    self._dashing    = True
                    self._dash_timer = self.DASH_DURATION
                    self._dash_cd    = self.DASH_COOLDOWN
                    self._dash_dir   = self.facing

    @property
    def cooldown_bars(self):
        return [
            ("SHIFT", "Dash",   self._dash_cd, self.DASH_COOLDOWN),
            ("J",     "Ataque", self._atk_cd,  self.ATTACK_COOLDOWN),
        ]

    def draw(self, surface, cam_x):
        super().draw(surface, cam_x)
        if self._dashing:
            r = pygame.Rect(self.rect.x - cam_x, self.rect.y,
                            self.rect.w, self.rect.h)
            flash = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 90))
            surface.blit(flash, r.topleft)
