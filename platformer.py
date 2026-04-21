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

import os
import sys
import json
import math
import pygame

from constants import (
    WIDTH, HEIGHT, FPS, LEVEL_WIDTH,
    SKY, BLACK, DARK_GRAY, GRAY, BROWN, BREAK_COL,
    C_WARRIOR, C_MAGE, C_DRUID, C_ROGUE,
)
from player import Warrior, Mage, Druid, Rogue
from enemy import GreenWarrior, GreenMelee, Ghost, SpikeBall, Boss
from menu import MainMenu, LevelSelectMenu, ShopMenu, PauseMenu, UsernameMenu

SAVE_PATH   = os.path.join(os.path.dirname(__file__), "save.json")
WALLET_PATH = os.path.join(os.path.dirname(__file__), "wallet.json")

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


class Coin:
    RADIUS = 7

    def __init__(self, x, y):
        self.rect      = pygame.Rect(x - self.RADIUS, y - self.RADIUS,
                                     self.RADIUS * 2, self.RADIUS * 2)
        self.collected = False
        self._t        = 0.0

    def update(self, dt):
        self._t += dt * 3.5

    def draw(self, surface, cam_x):
        if self.collected:
            return
        cx = self.rect.centerx - cam_x
        cy = self.rect.centery + int(math.sin(self._t) * 3)
        pygame.draw.circle(surface, (255, 215, 0),   (cx, cy), self.RADIUS)
        pygame.draw.circle(surface, (255, 245, 130),  (cx, cy), self.RADIUS - 3)
        pygame.draw.circle(surface, (200, 150,  0),   (cx, cy), self.RADIUS, 1)


# ==============================================================================
# Level definition
# ==============================================================================

# ==============================================================================
# Level themes — 5 themes, 4 levels each (levels 1-4, 5-8, 9-12, 13-16, 17-20)
# ==============================================================================

def _apply_speed(enemies, level):
    mult = 0.7 + (level - 1) * 0.068
    for e in enemies:
        new_spd = max(30, int(e.SPEED * mult))
        e.SPEED = new_spd
        e.vx    = float(new_spd) if e.facing >= 0 else -float(new_spd)
    return enemies


# ── Tema 0: Floresta (fases 1–4) ─────────────────────────────────────────────

def _map_floresta():
    p = []
    p.append(Platform(  0, 540,  325, 30, BROWN))
    p.append(Platform(423, 540, 1127, 30, BROWN))
    p.append(Platform( 78, 475,  78, 14))
    p.append(Platform(195, 423,  65, 14))
    p.append(Platform(286, 371,  78, 14))
    p.append(Platform(436, 488, 104, 14))
    p.append(Platform(566, 423,  65, 14))
    p.append(BreakableBlock(514, 514, 26, 26))
    p.append(BreakableBlock(514, 488, 26, 26))
    p.append(Platform(618, 358, 117, 14))
    p.append(Platform(754, 306, 104, 14))
    p.append(Platform(858, 358,  91, 14))
    p.append(Platform( 936, 462,  52, 14))
    p.append(Platform( 975, 384,  52, 14))
    p.append(Platform(1014, 306,  52, 14))
    p.append(Platform(1014, 228,  91, 14))
    p.append(Platform(1118, 371, 130, 14))
    p.append(Platform(1235, 449, 117, 14))
    p.append(Platform(1352, 371,  65, 14))
    p.append(Platform(1550, 488,  65, 14))
    p.append(Platform(1620, 436,  52, 14))
    p.append(Platform(1680, 371,  52, 14))
    p.append(Platform(1740, 436,  52, 14))
    p.append(Platform(1800, 540, 400, 30, BROWN))
    p.append(Platform(1820, 462,  78, 14))
    p.append(Platform(1900, 384,  65, 14))
    p.append(Platform(1970, 306,  78, 14))
    p.append(Platform(2040, 384,  65, 14))
    p.append(Platform(2200, 540, 550, 30, BROWN))
    p.append(BreakableBlock(2260, 514, 26, 26))
    p.append(BreakableBlock(2260, 488, 26, 26))
    p.append(Platform(2240, 423,  91, 14))
    p.append(BreakableBlock(2400, 514, 26, 26))
    p.append(BreakableBlock(2400, 488, 26, 26))
    p.append(BreakableBlock(2400, 462, 26, 26))
    p.append(Platform(2380, 371, 104, 14))
    p.append(BreakableBlock(2560, 514, 26, 26))
    p.append(BreakableBlock(2560, 488, 26, 26))
    p.append(Platform(2540, 436,  78, 14))
    p.append(Platform(2650, 358,  91, 14))
    p.append(Platform(2700, 280,  78, 14))
    p.append(Platform(2750, 462,  65, 14))
    p.append(Platform(2820, 384,  65, 14))
    p.append(Platform(2890, 306,  65, 14))
    p.append(Platform(2960, 228,  78, 14))
    p.append(Platform(3030, 306,  65, 14))
    p.append(Platform(3080, 384,  65, 14))
    p.append(Platform(2980, 540, 320, 30, BROWN))
    p.append(Platform(2990, 462,  52, 14))
    p.append(Platform(3000, 384,  52, 14))
    p.append(Platform(3010, 306,  52, 14))
    p.append(Platform(3010, 228, 120, 14))
    return p

def _cps_floresta():
    return [Checkpoint(430,540), Checkpoint(1560,540), Checkpoint(2210,540),
            Checkpoint(2760,462), Checkpoint(2985,540)]

def _ene_floresta(level):
    extra = (level - 1) % 4
    e = [
        GreenWarrior(100, 490,   0,  300), Ghost(460, 435, 423, 560),
        GreenMelee( 650, 490, 423,  850),  SpikeBall(780, 330, 618, 858),
        GreenWarrior(1000,420, 936, 1066), Ghost(1180,320,1118,1365),
        SpikeBall(1840, 435,1800,1970),    GreenMelee(1960,357,1900,2100),
        GreenWarrior(2300,490,2200,2450),  SpikeBall(2480,357,2380,2560),
        GreenMelee(2620, 490,2550,2750),   Ghost(2680,253,2650,2750),
        Ghost(2850, 357,2820,2960),        SpikeBall(2990,279,2960,3080),
        GreenWarrior(3000,476,2980,3080),  SpikeBall(3060,476,2980,3120),
    ]
    if extra >= 1: e.append(GreenMelee(500, 490, 423, 700))
    if extra >= 2: e.append(SpikeBall(1300,357,1235,1450))
    if extra >= 3: e.append(Ghost(2100,357,1970,2200))
    return _apply_speed(e, level)


# ── Tema 1: Ilhas Flutuantes (fases 5–8) ─────────────────────────────────────

def _map_ilhas():
    p = []
    # Zone 1
    p.append(Platform(  0, 510, 180, 20))
    p.append(Platform(220, 470, 110, 14))
    p.append(Platform(370, 420, 100, 14))
    p.append(Platform(500, 360, 100, 14))
    p.append(Platform(630, 420, 100, 14))
    p.append(Platform(760, 490, 130, 14))
    # Zone 2
    p.append(Platform( 930, 440, 110, 14))
    p.append(Platform(1080, 370, 110, 14))
    p.append(Platform(1220, 300,  90, 14))
    p.append(Platform(1360, 360,  90, 14))
    p.append(Platform(1490, 430, 100, 14))
    # Zone 3
    p.append(Platform(1660, 380, 160, 14))
    p.append(BreakableBlock(1710, 354, 40, 26))
    p.append(Platform(1860, 310, 100, 14))
    p.append(Platform(1990, 370, 100, 14))
    p.append(Platform(2120, 430, 120, 14))
    # Zone 4
    p.append(Platform(2290, 350,  80, 14))
    p.append(Platform(2410, 270,  80, 14))
    p.append(Platform(2530, 320,  80, 14))
    p.append(Platform(2650, 390,  80, 14))
    p.append(Platform(2760, 320,  80, 14))
    # Zone 5 — boss island
    p.append(Platform(2900, 480, 380, 22, BROWN))
    p.append(Platform(2920, 410,  60, 14))
    p.append(Platform(3020, 340,  60, 14))
    p.append(Platform(3140, 410,  60, 14))
    return p

def _cps_ilhas():
    return [Checkpoint(100,510), Checkpoint(1500,430), Checkpoint(1870,310),
            Checkpoint(2660,390), Checkpoint(2940,480)]

def _ene_ilhas(level):
    extra = (level - 1) % 4
    e = [
        SpikeBall( 400, 390, 370,  470), Ghost(530, 326, 500, 600),
        SpikeBall( 790, 460, 760,  890), Ghost(960, 406, 930,1040),
        SpikeBall(1240, 270,1220, 1310), Ghost(1390,326,1360,1450),
        GreenMelee(1700,346,1660, 1820), Ghost(1890,276,1860,1960),
        SpikeBall(2020, 340,1990, 2090), Ghost(2310,316,2290,2370),
        SpikeBall(2430, 240,2410, 2490), Ghost(2670,356,2650,2730),
        GreenMelee(2960,446,2900, 3100), SpikeBall(3050,450,2950,3270),
        Ghost(3040, 306,3020, 3080),
    ]
    if extra >= 1: e.append(Ghost(450, 326, 370, 600))
    if extra >= 2: e.append(SpikeBall(1600,346,1490,1820))
    if extra >= 3: e.append(Ghost(2200,396,2120,2410))
    return _apply_speed(e, level)


# ── Tema 2: Masmorra (fases 9–12) ────────────────────────────────────────────

def _map_masmorra():
    p = []
    p.append(Platform(0, 540, 3300, 30, BROWN))
    # Zone 1
    p.append(Platform( 80,462, 90,14)); p.append(Platform(200,384, 90,14))
    p.append(BreakableBlock(310,514,26,26)); p.append(BreakableBlock(310,488,26,26))
    p.append(BreakableBlock(310,462,26,26))
    p.append(Platform(340,462, 90,14)); p.append(Platform(460,384, 90,14))
    p.append(BreakableBlock(560,514,26,26)); p.append(BreakableBlock(560,488,26,26))
    p.append(Platform(590,462,100,14)); p.append(Platform(720,384, 90,14))
    # Zone 2
    p.append(BreakableBlock(860,514,26,26)); p.append(BreakableBlock(860,488,26,26))
    p.append(BreakableBlock(860,462,26,26)); p.append(BreakableBlock(886,514,26,26))
    p.append(BreakableBlock(886,488,26,26)); p.append(BreakableBlock(886,462,26,26))
    p.append(Platform(920,406, 90,14)); p.append(Platform(1040,462,100,14))
    p.append(Platform(1160,384, 90,14)); p.append(Platform(1280,306,100,14))
    p.append(Platform(1420,384, 90,14)); p.append(Platform(1540,462,100,14))
    # Zone 3
    p.append(BreakableBlock(1680,514,26,26)); p.append(BreakableBlock(1680,488,26,26))
    p.append(BreakableBlock(1680,462,26,26)); p.append(BreakableBlock(1706,514,26,26))
    p.append(BreakableBlock(1706,488,26,26)); p.append(BreakableBlock(1732,514,26,26))
    p.append(Platform(1780,406, 90,14)); p.append(Platform(1900,462,100,14))
    p.append(Platform(2020,384, 90,14)); p.append(Platform(2140,306,100,14))
    # Zone 4
    p.append(BreakableBlock(2260,514,26,26)); p.append(BreakableBlock(2260,488,26,26))
    p.append(BreakableBlock(2260,462,26,26)); p.append(BreakableBlock(2260,436,26,26))
    p.append(Platform(2310,462,100,14)); p.append(Platform(2440,384, 90,14))
    p.append(Platform(2560,462,100,14)); p.append(Platform(2680,384, 90,14))
    p.append(Platform(2800,306,100,14))
    # Zone 5
    p.append(BreakableBlock(2920,514,26,26)); p.append(BreakableBlock(2920,488,26,26))
    p.append(BreakableBlock(2920,462,26,26))
    p.append(Platform(2960,462, 90,14)); p.append(Platform(3080,384, 90,14))
    p.append(Platform(3180,306, 90,14))
    return p

def _cps_masmorra():
    return [Checkpoint(720,540), Checkpoint(1280,540), Checkpoint(2020,540),
            Checkpoint(2560,540), Checkpoint(2960,540)]

def _ene_masmorra(level):
    extra = (level - 1) % 4
    e = [
        GreenWarrior(130,490,  0, 310), GreenMelee(410,490,340, 550),
        GreenWarrior(620,490,590, 810), GreenMelee(1060,490,920,1160),
        GreenWarrior(1200,490,1160,1420), SpikeBall(1340,281,1280,1420),
        GreenMelee(1560,490,1420,1680), GreenWarrior(1860,490,1780,2020),
        Ghost(2060,357,1900,2140), GreenMelee(2170,490,2020,2310),
        GreenWarrior(2380,490,2260,2560), SpikeBall(2510,357,2440,2680),
        GreenMelee(2640,490,2560,2800), Ghost(2800,281,2680,2920),
        GreenWarrior(3010,490,2960,3200), GreenMelee(3110,490,3020,3290),
        SpikeBall(3160,357,3080,3280),
    ]
    if extra >= 1: e.append(GreenMelee(230,490,  0, 460))
    if extra >= 2: e.append(GreenWarrior(1740,490,1680,1900))
    if extra >= 3: e.append(SpikeBall(2270,437,2140,2440))
    return _apply_speed(e, level)


# ── Tema 3: Castelo (fases 13–16) ────────────────────────────────────────────

def _map_castelo():
    p = []
    # Zone 1 — pátio externo
    p.append(Platform(  0,540, 420,30, BROWN))
    p.append(Platform( 80,462, 60,14)); p.append(Platform(160,384, 60,14))
    p.append(Platform(240,306, 60,14)); p.append(Platform(320,228, 60,14))
    p.append(Platform(380,306, 80,14)); p.append(Platform(420,384, 80,14))
    p.append(Platform(510,462,100,14))
    # Zone 2 — muralha
    p.append(Platform(640,540, 420,30, BROWN))
    p.append(Platform(660,462, 60,14)); p.append(Platform(740,384, 60,14))
    p.append(Platform(820,306, 60,14)); p.append(Platform(900,228, 60,14))
    p.append(Platform(860,306, 60,14)); p.append(Platform(800,384, 60,14))
    p.append(Platform(960,462, 80,14)); p.append(Platform(1040,384,80,14))
    p.append(BreakableBlock(1140,514,26,26)); p.append(BreakableBlock(1140,488,26,26))
    p.append(BreakableBlock(1140,462,26,26)); p.append(Platform(1180,384,90,14))
    # Zone 3 — torre interna
    p.append(Platform(1300,540, 440,30, BROWN))
    p.append(Platform(1320,462, 60,14)); p.append(Platform(1400,384, 60,14))
    p.append(Platform(1480,306, 60,14)); p.append(Platform(1560,228, 60,14))
    p.append(Platform(1640,150, 60,14))
    p.append(Platform(1700,228, 80,14)); p.append(Platform(1780,306, 80,14))
    p.append(Platform(1860,384, 80,14))
    p.append(BreakableBlock(1960,514,26,26)); p.append(BreakableBlock(1960,488,26,26))
    p.append(Platform(2000,462, 90,14))
    # Zone 4 — ameias
    p.append(Platform(2140,540, 420,30, BROWN))
    p.append(Platform(2160,462, 60,14)); p.append(Platform(2240,384, 60,14))
    p.append(Platform(2320,306, 70,14)); p.append(Platform(2410,228, 70,14))
    p.append(Platform(2500,306, 70,14)); p.append(Platform(2580,384, 70,14))
    p.append(Platform(2660,462, 70,14))
    # Zone 5 — sala do trono
    p.append(Platform(2780,540, 520,30, BROWN))
    p.append(Platform(2800,462, 60,14)); p.append(Platform(2880,384, 60,14))
    p.append(Platform(2960,306, 60,14)); p.append(Platform(3040,228,120,14))
    p.append(BreakableBlock(2840,514,26,26)); p.append(BreakableBlock(2840,488,26,26))
    p.append(Platform(3160,306, 80,14)); p.append(Platform(3220,384, 80,14))
    return p

def _cps_castelo():
    return [Checkpoint(510,462), Checkpoint(960,462), Checkpoint(1320,540),
            Checkpoint(2160,540), Checkpoint(2800,540)]

def _ene_castelo(level):
    extra = (level - 1) % 4
    e = [
        Ghost(200,357, 80,420), GreenWarrior(370,357,240,510),
        Ghost(700,435,640,840), SpikeBall(870,201,740,1020),
        GreenMelee(980,435,960,1140), Ghost(1100,357,960,1180),
        Ghost(1440,279,1320,1560), SpikeBall(1560,201,1480,1700),
        GreenWarrior(1720,279,1560,1860), GreenMelee(1890,435,1720,2000),
        Ghost(2220,435,2140,2410), SpikeBall(2380,201,2240,2540),
        Ghost(2540,357,2410,2660), GreenMelee(2640,435,2580,2780),
        Ghost(2920,279,2800,3040), SpikeBall(3020,201,2960,3160),
        GreenWarrior(3080,490,3000,3300), GreenMelee(3170,490,3040,3300),
    ]
    if extra >= 1: e.append(SpikeBall(450,279,240,640))
    if extra >= 2: e.append(Ghost(1230,201,1040,1320))
    if extra >= 3: e.append(SpikeBall(2120,201,2000,2320))
    return _apply_speed(e, level)


# ── Tema 4: Caos (fases 17–20) ────────────────────────────────────────────────

def _map_caos():
    p = []
    # Zone 1 — misto
    p.append(Platform(  0,540, 300,30, BROWN))
    p.append(Platform( 80,462, 70,14)); p.append(Platform(170,384, 70,14))
    p.append(Platform(260,306, 70,14))
    p.append(BreakableBlock(340,514,26,26)); p.append(BreakableBlock(340,488,26,26))
    p.append(BreakableBlock(340,462,26,26))
    p.append(Platform(410,420, 80,14)); p.append(Platform(520,350, 80,14))
    p.append(Platform(630,420, 80,14))
    # Zone 2
    p.append(Platform(730,540, 400,30, BROWN))
    p.append(Platform(750,462, 60,14)); p.append(Platform(830,384, 60,14))
    p.append(Platform(910,306, 60,14)); p.append(Platform(990,228, 60,14))
    p.append(Platform(1060,306,70,14)); p.append(Platform(1140,384,70,14))
    p.append(BreakableBlock(1240,514,26,26)); p.append(BreakableBlock(1240,488,26,26))
    p.append(BreakableBlock(1240,462,26,26)); p.append(Platform(1280,384,80,14))
    # Zone 3 — ilhas
    p.append(Platform(1430,460,100,14)); p.append(Platform(1570,380,100,14))
    p.append(Platform(1700,300,100,14)); p.append(Platform(1830,380,100,14))
    p.append(BreakableBlock(1950,454,26,26)); p.append(BreakableBlock(1950,428,26,26))
    p.append(Platform(1990,380, 90,14))
    # Zone 4 — labirinto
    p.append(Platform(2110,540, 320,30, BROWN))
    p.append(Platform(2130,462, 60,14)); p.append(Platform(2210,384, 60,14))
    p.append(Platform(2290,306, 60,14)); p.append(Platform(2370,228, 60,14))
    p.append(BreakableBlock(2450,514,26,26)); p.append(BreakableBlock(2450,488,26,26))
    p.append(BreakableBlock(2450,462,26,26)); p.append(BreakableBlock(2450,436,26,26))
    p.append(Platform(2500,462, 90,14)); p.append(Platform(2610,384, 90,14))
    p.append(Platform(2710,306, 90,14))
    # Zone 5 — arena caos
    p.append(Platform(2830,540, 470,30, BROWN))
    p.append(Platform(2850,462, 60,14)); p.append(Platform(2930,384, 60,14))
    p.append(Platform(3010,306, 60,14)); p.append(Platform(3090,228,120,14))
    p.append(BreakableBlock(2910,514,26,26)); p.append(BreakableBlock(2910,488,26,26))
    p.append(Platform(3150,306, 80,14)); p.append(Platform(3210,384, 80,14))
    return p

def _cps_caos():
    return [Checkpoint(630,420), Checkpoint(1280,384), Checkpoint(1830,380),
            Checkpoint(2500,462), Checkpoint(2850,540)]

def _ene_caos(level):
    extra = (level - 1) % 4
    e = [
        GreenWarrior(150,490,  0,300), Ghost(480,393,410,630),
        SpikeBall(590,325,520,710), GreenMelee(810,490,730,910),
        Ghost(970,279,830,1110), SpikeBall(1100,357,1060,1240),
        GreenWarrior(1170,490,1110,1410), Ghost(1530,435,1430,1670),
        SpikeBall(1670,355,1570,1830), GreenMelee(1850,355,1700,2010),
        Ghost(1980,355,1830,2110), GreenWarrior(2190,490,2110,2410),
        Ghost(2350,201,2210,2510), SpikeBall(2500,437,2370,2660),
        GreenMelee(2660,357,2610,2830), GreenWarrior(2910,490,2830,3060),
        Ghost(3010,279,2930,3150), SpikeBall(3110,279,3010,3290),
        GreenMelee(3190,490,3090,3300), Ghost(3070,490,2990,3210),
    ]
    if extra >= 1: e += [GreenMelee(310,279,170,410), SpikeBall(610,393,410,730)]
    if extra >= 2: e += [Ghost(1360,357,1140,1570), GreenWarrior(2010,355,1830,2110)]
    if extra >= 3: e += [SpikeBall(2710,281,2500,2830), Ghost(3030,201,2910,3210)]
    return _apply_speed(e, level)


# ── Roteamento ────────────────────────────────────────────────────────────────

_MAPS    = [_map_floresta,  _map_ilhas,   _map_masmorra,  _map_castelo,  _map_caos  ]
_CPS     = [_cps_floresta,  _cps_ilhas,   _cps_masmorra,  _cps_castelo,  _cps_caos  ]
_ENE     = [_ene_floresta,  _ene_ilhas,   _ene_masmorra,  _ene_castelo,  _ene_caos  ]
_BOSSES  = [(3150,476,2995,3285),(3100,416,2910,3270),(3150,476,2980,3280),
            (3160,476,2990,3290),(3160,476,2990,3290)]
_SPAWNS  = [(40,490),(40,480),(40,490),(40,490),(40,490)]


def _theme(level):
    return min((level - 1) // 4, 4)

def create_level(level=1):
    return _MAPS[_theme(level)]()

def create_checkpoints(level=1):
    return _CPS[_theme(level)]()

def create_enemies(level=1):
    return _ENE[_theme(level)](level)

def _level_spawn(level):
    return _SPAWNS[_theme(level)]

def _level_boss(level):
    return _BOSSES[_theme(level)]


_COIN_POS = [
    # Tema 0 — Floresta
    [(60,510),(180,510),(460,510),(580,510),(660,510),(780,510),
     (100,450),(220,398),(310,346),(450,463),(580,398),(640,333),
     (776,281),(880,333),(960,437),(997,359),(1036,281),(1060,203),
     (1145,346),(1265,424),(1375,346),(1570,463),(1645,411),(1695,346),
     (1840,437),(1920,359),(1990,281),(2660,333),(2720,255)],
    # Tema 1 — Ilhas Flutuantes
    [(50,485),(100,485),(150,485),(250,445),(290,445),(395,395),
     (430,395),(520,335),(560,335),(650,395),(700,395),(790,465),
     (840,465),(950,415),(1000,415),(1100,345),(1150,345),(1240,275),
     (1380,335),(1510,405),(1680,355),(1720,355),(1870,285),(2010,345),
     (2150,405),(2300,325),(2430,245),(2540,295),(2660,365),(2920,455)],
    # Tema 2 — Masmorra
    [(60,510),(180,510),(360,437),(480,359),(610,437),(730,359),
     (940,381),(1060,437),(1180,359),(1300,281),(1430,359),(1560,437),
     (1800,381),(1920,437),(2040,359),(2160,281),(2320,437),(2450,359),
     (2570,437),(2690,359),(2810,281),(2970,437),(3090,359),(3190,281)],
    # Tema 3 — Castelo
    [(80,437),(160,359),(240,281),(320,203),(390,281),(430,359),
     (530,437),(660,437),(740,359),(820,281),(900,203),(970,437),
     (1060,359),(1160,359),(1200,359),(1320,437),(1400,359),(1480,281),
     (1560,203),(1640,125),(1700,203),(1780,281),(1870,437),
     (2160,437),(2240,359),(2320,281),(2410,203),(2510,281),
     (2800,437),(2880,359),(2960,281),(3040,203)],
    # Tema 4 — Caos
    [(60,510),(180,510),(100,437),(190,359),(270,281),(430,395),
     (540,325),(650,395),(760,510),(840,437),(920,359),(1000,203),
     (1070,281),(1150,359),(1290,359),(1450,435),(1580,355),(1710,275),
     (1840,355),(2000,355),(2130,510),(2210,437),(2290,359),(2370,203),
     (2510,437),(2620,359),(2720,281),(2860,437),(2940,359),(3020,281)],
]

def create_coins(level):
    positions = _COIN_POS[_theme(level)]
    return [Coin(x, y) for x, y in positions]


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

        self.current_level = 1
        self.total_coins   = 0
        self.owned_chars   = {0}
        self.username      = ""
        self._load_wallet()
        self._init_level()

        self.main_menu    = MainMenu(self.background, os.path.exists(SAVE_PATH))
        self.level_select = LevelSelectMenu(self.background)
        self.shop_menu    = ShopMenu(self.background, self.total_coins, self.owned_chars)
        self.pause_menu   = PauseMenu()
        self.username_menu = UsernameMenu(self.background, self.username)
        if not self.username:
            self.state = "USERNAME"

    # ------------------------------------------------------------------
    # Level / character initialisation
    # ------------------------------------------------------------------

    def _init_level(self, level=None):
        if level is not None:
            self.current_level = level
        self.platforms   = create_level(self.current_level)
        self.enemies     = create_enemies(self.current_level)
        self.checkpoints = create_checkpoints(self.current_level)
        sx, sy           = _level_spawn(self.current_level)
        self.spawn       = [sx, sy]
        self.characters  = [
            Warrior(sx, sy),
            Mage   (sx, sy),
            Druid  (sx, sy),
            Rogue  (sx, sy),
        ]
        self.idx    = 0
        self.lives  = 3
        self.camera = Camera()
        bx, by, bl, br   = _level_boss(self.current_level)
        self.boss        = Boss(bx, by, bl, br)
        boss_hp          = min(4 + (self.current_level - 1) * 3 // 5, 16)
        self.boss.hp     = boss_hp
        self.boss.MAX_HP = boss_hp
        spd              = 0.7 + (self.current_level - 1) * 0.068
        self.boss.SPEED        = max(35,  int(55  * spd))
        self.boss.CHARGE_SPEED = max(200, int(310 * (1.0 + (self.current_level - 1) * 0.025)))
        self.coins = create_coins(self.current_level)

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

    def _save_wallet(self):
        data = {
            "total_coins": self.total_coins,
            "owned_chars": list(self.owned_chars),
            "username":    self.username,
        }
        with open(WALLET_PATH, "w") as f:
            json.dump(data, f)

    def _load_wallet(self):
        if os.path.exists(WALLET_PATH):
            with open(WALLET_PATH) as f:
                data = json.load(f)
            self.total_coins = data.get("total_coins", 0)
            self.owned_chars = set(data.get("owned_chars", [0]))
            self.username    = data.get("username", "")
        self.owned_chars.add(0)

    # ------------------------------------------------------------------
    # Character switch
    # ------------------------------------------------------------------

    def _switch_character(self):
        old = self.player
        for _ in range(len(self.characters)):
            self.idx = (self.idx + 1) % len(self.characters)
            if self.idx in self.owned_chars:
                break
        new = self.player
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

            if self.state == "USERNAME":
                self._run_username(events, dt)
            elif self.state == "MAIN_MENU":
                self._run_main_menu(events)
            elif self.state == "LEVEL_SELECT":
                self._run_level_select(events)
            elif self.state == "SHOP":
                self._run_shop(events)
            elif self.state == "PLAYING":
                self._run_playing(events, dt)
            elif self.state == "PAUSED":
                self._run_paused(events, dt)

        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------

    def _run_username(self, events, dt):
        self.username_menu.handle_events(events)
        self.username_menu.update(dt)
        if self.username_menu.done:
            self.username = self.username_menu.text.strip() or "Jogador"
            self._save_wallet()
            back = getattr(self.username_menu, '_came_from_shop', False)
            self.state = "SHOP" if back else "MAIN_MENU"
            return
        self.username_menu.draw(self.screen)

    def _run_main_menu(self, events):
        self.main_menu.handle_events(events)
        if self.main_menu.choice == "new":
            self.main_menu.choice    = None
            self.level_select._sel   = 0
            self.level_select.choice = None
            self.state = "LEVEL_SELECT"
            return
        elif self.main_menu.choice == "load":
            self.load_game()
            self.state = "PLAYING"
        elif self.main_menu.choice == "shop":
            self.main_menu.choice = None
            self.shop_menu = ShopMenu(self.background, self.total_coins, self.owned_chars)
            self.state = "SHOP"
            return
        self.main_menu.choice = None
        self.main_menu.draw(self.screen)

    def _run_shop(self, events):
        self.shop_menu.handle_events(events)
        if self.shop_menu.choice == "back":
            self.total_coins  = self.shop_menu.coins
            self.owned_chars  = self.shop_menu.owned
            self._save_wallet()
            self.shop_menu.choice = None
            self.main_menu._sel   = 0
            self.main_menu.choice = None
            self.state = "MAIN_MENU"
            return
        if self.shop_menu.choice == "rename":
            self.total_coins = self.shop_menu.coins
            self.owned_chars = self.shop_menu.owned
            self.shop_menu.choice = None
            if self.total_coins >= 1_000_000_000_000:
                self.total_coins -= 1_000_000_000_000
                self._save_wallet()
                self.username_menu = UsernameMenu(self.background, self.username)
                self.username_menu._came_from_shop = True
                self.state = "USERNAME"
            else:
                self.shop_menu = ShopMenu(self.background, self.total_coins, self.owned_chars)
            return
        self.shop_menu.draw(self.screen)

    def _run_level_select(self, events):
        self.level_select.handle_events(events)
        if self.level_select.choice == "back":
            self.level_select.choice = None
            self.main_menu._sel      = 0
            self.main_menu.choice    = None
            self.state = "MAIN_MENU"
            return
        elif self.level_select.choice is not None:
            level = self.level_select.choice
            self.level_select.choice = None
            self._init_level(level)
            self.state = "PLAYING"
            return
        self.level_select.draw(self.screen)

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
                elif event.key == pygame.K_F10:
                    self.total_coins = 1_000_000_000_000
                    self._save_wallet()

        keys = pygame.key.get_pressed()
        p    = self.player
        p.use_ability(events, self.platforms)
        p.handle_input(keys, events)
        p.update(dt, self.platforms)

        for cp in self.checkpoints:
            if cp.try_activate(p.rect):
                self.spawn = [cp.spawn_x, cp.spawn_y]

        for coin in self.coins:
            coin.update(dt)
            if not coin.collected and coin.rect.colliderect(p.rect):
                coin.collected  = True
                self.total_coins += 1

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

        for coin in self.coins:
            coin.draw(self.screen, cam_x)

        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x)

        self.boss.draw(self.screen, cam_x)
        self.player.draw(self.screen, cam_x)

        p = self.player

        user_surf = self.font_md.render(self.username, True, (255, 220, 60))
        self.screen.blit(user_surf, (10, 10))

        name_surf = self.font_sm.render("[ " + p.NAME + " ]", True, BLACK)
        self.screen.blit(name_surf, (10, 34))

        lvl_surf = self.font_md.render(f"FASE {self.current_level}", True, BLACK)
        self.screen.blit(lvl_surf, (WIDTH // 2 - lvl_surf.get_width() // 2, 10))

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
            owned = i in self.owned_chars
            draw_col = col if owned else (60, 60, 60)
            pygame.draw.circle(self.screen, draw_col, (dx, dy), 10)
            if i == self.idx:
                pygame.draw.circle(self.screen, BLACK, (dx, dy), 10, 2)
            ls = self.font_sm.render(lbl, True, BLACK)
            self.screen.blit(ls, (dx - ls.get_width() // 2, dy + 14))
            if not owned:
                lk = self.font_sm.render("🔒", True, (200, 200, 200))
                self.screen.blit(lk, (dx - lk.get_width() // 2, dy - 8))

        # Moedas HUD
        coin_surf = self.font_md.render(f"$ {self.total_coins}", True, (255, 215, 0))
        self.screen.blit(coin_surf, (WIDTH - coin_surf.get_width() - 8, 36))

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
