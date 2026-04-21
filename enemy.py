# -*- coding: utf-8 -*-
import pygame
import os

from constants import GRAVITY, DISPLAY_SCALE

_ENEMY_DIR = os.path.join(os.path.dirname(__file__), "sprites", "enemy")

_img_cache = {}

def _load_img(path):
    if path not in _img_cache:
        _img_cache[path] = pygame.image.load(path).convert_alpha()
    return _img_cache[path]


# ---------------------------------------------------------------------------
# Sheet-based animator (enemies 01-14, 18-22 — same 3×4 layout as player)
# ---------------------------------------------------------------------------

SHEET_FRAME_W = 32
SHEET_FRAME_H = 32

_SHEET_ANIMS = {
    "walk_right": {"row": 2, "frames": 3, "fps": 8, "start_col": 0},
    "walk_left":  {"row": 1, "frames": 3, "fps": 8, "start_col": 0},
    "idle_right": {"row": 2, "frames": 1, "fps": 1, "start_col": 1},
    "idle_left":  {"row": 1, "frames": 1, "fps": 1, "start_col": 1},
}

class _SheetAnimator:
    def __init__(self, sheet_path):
        self._sheet = _load_img(sheet_path)
        self._anim  = "idle_right"
        self._col   = 0
        self._timer = 0.0

    def set_animation(self, name):
        if name != self._anim:
            self._anim  = name
            self._col   = 0
            self._timer = 0.0

    def update(self, dt):
        anim = _SHEET_ANIMS[self._anim]
        self._timer += dt
        if self._timer >= 1.0 / anim["fps"]:
            self._timer = 0.0
            self._col   = (self._col + 1) % anim["frames"]

    def draw(self, surface, dest_rect, cam_x):
        anim  = _SHEET_ANIMS[self._anim]
        col   = anim["start_col"] + self._col
        frame = pygame.Surface((SHEET_FRAME_W, SHEET_FRAME_H), pygame.SRCALPHA)
        frame.blit(self._sheet, (0, 0),
                   (col * SHEET_FRAME_W, anim["row"] * SHEET_FRAME_H,
                    SHEET_FRAME_W, SHEET_FRAME_H))
        dw = int(dest_rect.w * DISPLAY_SCALE)
        dh = int(dest_rect.h * DISPLAY_SCALE)
        dx = dest_rect.centerx - cam_x - dw // 2
        dy = dest_rect.bottom - dh
        scaled = pygame.transform.scale(frame, (dw, dh))
        surface.blit(scaled, (dx, dy))




# ===========================================================================
# Enemy base class
# ===========================================================================

class Enemy:
    """
    Patrols between patrol_left and patrol_right on platforms.
    Subclasses set WIDTH, HEIGHT, SPEED and build self._animator.
    """

    WIDTH  = 28
    HEIGHT = 32
    SPEED  = 70

    REVIVE_DELAY = 5.0   # seconds before respawn

    def __init__(self, x, y, patrol_left, patrol_right):
        self._origin_x     = x
        self._origin_y     = y
        self.rect          = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.vx            = float(self.SPEED)
        self.vy            = 0.0
        self.facing        = 1
        self.on_ground     = False
        self.patrol_left   = patrol_left
        self.patrol_right  = patrol_right
        self.alive         = True
        self._revive_timer = 0.0
        self._animator     = None   # set by subclass

    # ------------------------------------------------------------------

    def update(self, dt, platforms):
        if not self.alive:
            self._revive_timer -= dt
            if self._revive_timer <= 0:
                self._revive()
            return

        # Gravity
        self.vy += GRAVITY * dt

        # Horizontal
        self.rect.x += int(self.vx * dt)
        self._resolve_h(platforms)

        # Patrol bounce
        if self.rect.left <= self.patrol_left:
            self.rect.left = self.patrol_left
            self.vx = abs(self.vx)
            self.facing = 1
        elif self.rect.right >= self.patrol_right:
            self.rect.right = self.patrol_right
            self.vx = -abs(self.vx)
            self.facing = -1

        # Vertical
        dy = int(self.vy * dt)
        if dy == 0 and self.on_ground:
            dy = 1
        self.rect.y += dy
        self.on_ground = False
        self._resolve_v(platforms)

        self._update_animator(dt)

    def _resolve_h(self, platforms):
        for plat in platforms:
            if getattr(plat, 'breakable', False) and plat.broken:
                continue
            if self.rect.colliderect(plat.rect):
                if self.vx > 0:
                    self.rect.right = plat.rect.left
                    self.vx = -abs(self.vx)
                    self.facing = -1
                elif self.vx < 0:
                    self.rect.left = plat.rect.right
                    self.vx = abs(self.vx)
                    self.facing = 1

    def _resolve_v(self, platforms):
        for plat in platforms:
            if getattr(plat, 'breakable', False) and plat.broken:
                continue
            if self.rect.colliderect(plat.rect):
                if self.vy > 0:
                    self.rect.bottom = plat.rect.top
                    self.on_ground   = True
                    self.vy          = 0.0
                elif self.vy < 0:
                    self.rect.top = plat.rect.bottom
                    self.vy       = 0.0

    def _update_animator(self, dt):
        if self._animator is None:
            return
        anim = "walk_right" if self.vx > 0 else "walk_left"
        self._animator.set_animation(anim)
        self._animator.update(dt)

    def kill(self):
        self.alive         = False
        self._revive_timer = self.REVIVE_DELAY

    def _revive(self):
        self.rect.x    = self._origin_x
        self.rect.y    = self._origin_y
        self.vx        = float(self.SPEED)
        self.vy        = 0.0
        self.facing    = 1
        self.on_ground = False
        self.alive     = True

    def collides_with_player(self, player_rect):
        return self.alive and self.rect.colliderect(player_rect)

    def draw(self, surface, cam_x):
        if not self.alive:
            # Blink during last 2s of revive countdown
            if self._revive_timer < 2.0 and int(self._revive_timer * 6) % 2 == 0:
                r = pygame.Rect(self.rect.x - cam_x, self.rect.y,
                                self.rect.w, self.rect.h)
                pygame.draw.rect(surface, (255, 255, 255), r, 2)
            return

        if self._animator:
            self._animator.draw(surface, self.rect, cam_x)
        else:
            r = pygame.Rect(self.rect.x - cam_x, self.rect.y,
                            self.rect.w, self.rect.h)
            pygame.draw.rect(surface, (200, 0, 0), r)


# ===========================================================================
# Concrete enemy types
# ===========================================================================

class GreenWarrior(Enemy):
    """Sheet-based enemy, file Enemy 01-1.png."""
    WIDTH  = 28
    HEIGHT = 36
    SPEED  = 65

    def __init__(self, x, y, patrol_left, patrol_right):
        super().__init__(x, y, patrol_left, patrol_right)
        path = os.path.join(_ENEMY_DIR, "Enemy 01-1.png")
        self._animator = _SheetAnimator(path)


class GreenMelee(Enemy):
    """Sheet-based enemy, file Enemy 18.png."""
    WIDTH  = 26
    HEIGHT = 34
    SPEED  = 80

    def __init__(self, x, y, patrol_left, patrol_right):
        super().__init__(x, y, patrol_left, patrol_right)
        path = os.path.join(_ENEMY_DIR, "Enemy 18.png")
        self._animator = _SheetAnimator(path)


class Ghost(Enemy):
    """Dark hooded enemy — Enemy 15-1.png (color variant 1)."""
    WIDTH  = 28
    HEIGHT = 34
    SPEED  = 50

    def __init__(self, x, y, patrol_left, patrol_right):
        super().__init__(x, y, patrol_left, patrol_right)
        path = os.path.join(_ENEMY_DIR, "Enemy 15-1.png")
        self._animator = _SheetAnimator(path)


class SpikeBall(Enemy):
    """Spiky ball enemy — Enemy 16-1.png (color variant 1)."""
    WIDTH  = 30
    HEIGHT = 30
    SPEED  = 100

    def __init__(self, x, y, patrol_left, patrol_right):
        super().__init__(x, y, patrol_left, patrol_right)
        path = os.path.join(_ENEMY_DIR, "Enemy 16-1.png")
        self._animator = _SheetAnimator(path)


class Boss(Enemy):
    """Final boss: large, multi-hit, charge + jump attacks, two phases."""

    WIDTH  = 52
    HEIGHT = 64
    SPEED  = 55
    MAX_HP = 6

    REVIVE_DELAY = 99999.0

    CHARGE_SPEED    = 310
    CHARGE_DURATION = 0.55
    CHARGE_COOLDOWN = 2.5

    JUMP_FORCE    = -520
    JUMP_COOLDOWN = 3.2
    STOMP_RADIUS  = 90

    def __init__(self, x, y, patrol_left, patrol_right):
        super().__init__(x, y, patrol_left, patrol_right)
        self.hp            = self.MAX_HP
        self._charge_timer = 0.0
        self._charge_cd    = 0.0
        self._charging     = False
        self._charge_dir   = 1
        self._hit_flash    = 0.0
        self._jump_cd      = 1.5   # initial delay before first jump
        self._was_airborne = False  # to detect landing
        self._stomp_timer  = 0.0   # visual shockwave after landing
        self._stomp_cx     = 0
        self._stomp_cy     = 0
        path = os.path.join(_ENEMY_DIR, "Enemy 22.png")
        self._animator = _SheetAnimator(path)

    @property
    def phase(self):
        return 2 if self.hp <= self.MAX_HP // 2 else 1

    @property
    def stomp_active(self):
        return self._stomp_timer > 0.15   # first 0.15s of shockwave is the hitbox

    @property
    def stomp_center(self):
        return self._stomp_cx, self._stomp_cy

    def damage(self):
        if not self.alive or self._hit_flash > 0.05:
            return False
        self._hit_flash = 0.18
        self.hp -= 1
        if self.hp <= 0:
            self.alive         = False
            self._revive_timer = self.REVIVE_DELAY
            return True
        return False

    def update(self, dt, platforms, player_rect=None):
        if not self.alive:
            return

        self._hit_flash  = max(0.0, self._hit_flash  - dt)
        self._jump_cd    = max(0.0, self._jump_cd    - dt)
        self._stomp_timer = max(0.0, self._stomp_timer - dt)

        # Phase 2 modifiers
        p2 = self.phase == 2
        charge_cd    = self.CHARGE_COOLDOWN * (0.55 if p2 else 1.0)
        charge_speed = self.CHARGE_SPEED    * (1.35 if p2 else 1.0)
        jump_cd      = self.JUMP_COOLDOWN   * (0.65 if p2 else 1.0)
        self._charge_cd = max(0.0, self._charge_cd - dt)

        # Jump attack — only when on ground and not charging
        if self.on_ground and self._jump_cd <= 0 and not self._charging:
            self.vy        = self.JUMP_FORCE
            self._jump_cd  = jump_cd
            self._was_airborne = True

        # Detect stomp landing
        if self._was_airborne and self.on_ground:
            self._was_airborne = False
            self._stomp_timer  = 0.35
            self._stomp_cx     = self.rect.centerx
            self._stomp_cy     = self.rect.bottom

        if not self.on_ground:
            self._was_airborne = True

        # Charge logic
        if self._charging:
            self._charge_timer -= dt
            self.vx = charge_speed * self._charge_dir
            if self._charge_timer <= 0:
                self._charging = False
                self.vx        = float(self.SPEED) * self.facing
        elif player_rect is not None and self._charge_cd <= 0:
            dx     = player_rect.centerx - self.rect.centerx
            dy_abs = abs(player_rect.centery - self.rect.centery)
            if abs(dx) < 280 and dy_abs < 120:
                self._charging     = True
                self._charge_timer = self.CHARGE_DURATION
                self._charge_cd    = charge_cd
                self._charge_dir   = 1 if dx > 0 else -1

        # Physics
        self.vy += GRAVITY * dt

        self.rect.x += int(self.vx * dt)
        self._resolve_h(platforms)

        if not self._charging:
            if self.rect.left <= self.patrol_left:
                self.rect.left = self.patrol_left
                self.vx        = abs(self.SPEED)
                self.facing    = 1
            elif self.rect.right >= self.patrol_right:
                self.rect.right = self.patrol_right
                self.vx         = -abs(self.SPEED)
                self.facing     = -1

        dy = int(self.vy * dt)
        if dy == 0 and self.on_ground:
            dy = 1
        self.rect.y += dy
        self.on_ground = False
        self._resolve_v(platforms)

        self._update_animator(dt)

    def draw(self, surface, cam_x):
        if not self.alive:
            return

        if self._animator:
            self._animator.draw(surface, self.rect, cam_x)
        else:
            r = pygame.Rect(self.rect.x - cam_x, self.rect.y, self.rect.w, self.rect.h)
            pygame.draw.rect(surface, (180, 0, 0), r)

        # Phase 2: red tint overlay
        if self.phase == 2:
            r = pygame.Rect(self.rect.x - cam_x, self.rect.y, self.rect.w, self.rect.h)
            tint = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            tint.fill((200, 0, 0, 70))
            surface.blit(tint, r.topleft)

        # White flash on damage
        if self._hit_flash > 0:
            r = pygame.Rect(self.rect.x - cam_x, self.rect.y, self.rect.w, self.rect.h)
            flash = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 190))
            surface.blit(flash, r.topleft)

        # Stomp shockwave ring
        if self._stomp_timer > 0:
            progress = 1.0 - (self._stomp_timer / 0.35)
            radius   = int(self.STOMP_RADIUS * progress)
            alpha    = max(0, int(200 * (1.0 - progress)))
            sx       = self._stomp_cx - cam_x
            sy       = self._stomp_cy
            if radius > 2:
                ring = pygame.Surface((radius * 2 + 4, radius + 4), pygame.SRCALPHA)
                pygame.draw.ellipse(ring, (255, 120, 0, alpha),
                                    (0, 0, radius * 2 + 4, radius + 4), 3)
                surface.blit(ring, (sx - radius - 2, sy - 2))

        # Small HP bar above boss sprite
        bar_w = self.rect.w + 20
        bar_h = 7
        bx    = self.rect.x - cam_x - 10
        by    = self.rect.y - 18
        ratio = self.hp / self.MAX_HP
        pygame.draw.rect(surface, (60,  0,  0),  (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, (220, 30, 30), (bx, by, int(bar_w * ratio), bar_h))
        pygame.draw.rect(surface, (255, 80, 80), (bx, by, bar_w, bar_h), 1)
