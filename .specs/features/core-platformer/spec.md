# Core Platformer Specification

_Status: **Implemented** (M1 complete)_

## Problem Statement

Build a playable 2D platformer prototype that demonstrates a party-switching mechanic: four characters with distinct abilities, each essential to navigate a deliberately designed level.

## Goals

- [x] Player can move, jump, and use a unique ability per character
- [x] Level requires all four characters to navigate optimally
- [x] Game is playable in a single session without a menu or save system

## Out of Scope

| Feature | Reason |
|---------|--------|
| Sprite animations | M2 — assets downloaded, not integrated |
| Sound / music | M3 polish |
| Multiple levels | M3 polish |
| Enemies / combat | Out of scope for prototype |
| Save system | Not needed for a demo |

---

## User Stories

### P1: Move and Jump ⭐ MVP — VERIFIED

**User Story**: As a player, I want to move left/right and jump so that I can navigate the level.

**Acceptance Criteria**:

1. WHEN A/Left held THEN character SHALL move left at its SPEED
2. WHEN D/Right held THEN character SHALL move right at its SPEED
3. WHEN W/Up pressed AND jumps_left > 0 THEN character SHALL jump with JUMP_FORCE
4. WHEN character lands on a platform THEN jumps_left SHALL reset to MAX_JUMPS
5. WHEN character hits a wall THEN horizontal velocity SHALL zero out
6. WHEN character falls below HEIGHT+80 THEN character SHALL respawn at SPAWN (60, 490)

**Independent Test**: Run the game, move left/right, jump onto platforms.

---

### P1: 4 Distinct Characters ⭐ MVP — VERIFIED

**User Story**: As a player, I want four characters with unique abilities so that each feels different to play.

**Acceptance Criteria**:

1. WHEN active character is Warrior THEN stats SHALL be SPEED=140, JUMP=-370, size=36×50
2. WHEN active character is Mage THEN stats SHALL be SPEED=200, JUMP=-480, size=28×38
3. WHEN active character is Druid THEN stats SHALL be SPEED=170, JUMP=-630, MAX_JUMPS=2, size=30×42
4. WHEN active character is Rogue THEN stats SHALL be SPEED=320, JUMP=-480, size=24×36

---

### P1: Character Abilities ⭐ MVP — VERIFIED

**User Story**: As a player, I want each character to have a unique active or passive ability.

**Acceptance Criteria**:

1. WHEN Warrior presses SPACE AND a BreakableBlock is directly ahead THEN block SHALL become broken (solid=false), cooldown=0.5s
2. WHEN Mage presses SPACE THEN a cyan Projectile SHALL spawn at Mage's facing side, travel at 420 px/s, cooldown=0.3s
3. WHEN Druid presses jump a second time mid-air THEN Druid SHALL jump again (double jump passive, no key needed)
4. WHEN Rogue presses L-SHIFT AND not dashing AND cooldown elapsed THEN Rogue SHALL dash at 850 px/s for 0.18s, cooldown=0.8s
5. WHEN Rogue is dashing THEN a white semi-transparent flash SHALL overlay the character

---

### P1: Character Switch ⭐ MVP — VERIFIED

**User Story**: As a player, I want to cycle through characters with TAB so that I can pick the right tool for the obstacle.

**Acceptance Criteria**:

1. WHEN TAB pressed THEN active character SHALL cycle to the next in order [Warrior → Mage → Druid → Rogue → Warrior]
2. WHEN switching THEN new character SHALL inherit position (centerx/bottom) and velocity from the old one
3. WHEN switching while in air THEN new character SHALL have jumps_left=0
4. WHEN switching while on ground THEN new character SHALL have jumps_left=MAX_JUMPS
5. WHEN TAB held THEN switch SHALL NOT repeat (debounced)

---

### P1: Level Design ⭐ MVP — VERIFIED

**User Story**: As a player, I want a level that requires each character's ability so that switching is meaningful.

**Acceptance Criteria**:

1. SHALL have a 150px gap (x=500–650) that requires Druid's high/double jump to cross cleanly
2. SHALL have two stacked BreakableBlocks at x≈790 blocking the ground path — Warrior clears them, others go around
3. SHALL have an open speed corridor (x=950–1350) where Rogue's speed is an advantage
4. SHALL have a tall stacked tower (x=1440–1600) requiring Druid's double jump to reach the summit
5. Total level width SHALL be 2200px

---

### P1: Camera ⭐ MVP — VERIFIED

**User Story**: As a player, I want smooth horizontal scrolling so the level feels larger than the window.

**Acceptance Criteria**:

1. WHEN player moves right THEN camera SHALL lerp toward centering the player (lerp factor=8.0)
2. Camera x SHALL be clamped to [0, LEVEL_WIDTH − WIDTH]
3. dt SHALL be capped at 0.05s to prevent tunnelling after focus loss

---

### P1: HUD ⭐ MVP — VERIFIED

**User Story**: As a player, I want on-screen information about the active character and controls.

**Acceptance Criteria**:

1. WHEN active character changes THEN top-left SHALL display "[ CharacterName ]" in bold monospace
2. WHEN active character changes THEN ability hint SHALL update below the name
3. Top-right SHALL show four colored dots (W/M/Dr/Ro); the active one SHALL have a black border
4. Bottom bar SHALL display controls reminder
5. Bottom-right SHALL display live FPS

---

## Edge Cases

- WHEN Warrior tries to smash while cooldown > 0 THEN no smash occurs
- WHEN Mage tries to shoot while cooldown > 0 THEN no projectile spawns
- WHEN Rogue tries to dash while dashing OR cooldown > 0 THEN dash does not trigger
- WHEN player rect.left < 0 THEN player SHALL be pushed to x=0 (hard left wall)
- WHEN projectile x < -200 OR > LEVEL_WIDTH+200 THEN projectile.active = False

---

## Requirement Traceability

| Req ID | Story | Status |
|--------|-------|--------|
| PLAT-01 | Move and Jump | Verified |
| PLAT-02 | 4 Characters | Verified |
| PLAT-03 | Abilities | Verified |
| PLAT-04 | Character Switch | Verified |
| PLAT-05 | Level Design | Verified |
| PLAT-06 | Camera | Verified |
| PLAT-07 | HUD | Verified |

**Coverage:** 7 total, 7 verified ✅

---

## Success Criteria

- [x] All 4 characters playable with distinct feel
- [x] Level traversable using character synergies
- [x] 60 FPS on a mid-range machine
- [ ] Sprite visuals replacing colored rectangles (M2)
