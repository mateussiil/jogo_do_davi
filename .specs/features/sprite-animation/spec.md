# Sprite Animation Specification

_Status: **In Progress**_

## Problem Statement

The game currently renders characters as colored rectangles. The pipo-nekonin sprite assets (32 cat variants, 32×32px frames, 3×4 spritesheet) are downloaded but unused. This feature replaces rectangles with animated sprites.

## Spritesheet Format

- File: `sprites/character/pipo-nekonin001.png` (and variants 002–032)
- Total size: 96×128px per file
- Frame size: 32×32px
- Layout: 3 columns × 4 rows = 12 frames per file

## Animation Row Mapping

| Row | Frames | Animation | Use in platformer |
|-----|--------|-----------|-------------------|
| 0   | 0,1,2  | idle      | standing still    |
| 1   | 3,4,5  | walk_left | moving left       |
| 2   | 6,7,8  | walk_right| moving right      |
| 3   | 9,10,11| jump      | airborne          |

## Character → Sprite File Mapping

| Character | Sprite file |
|-----------|-------------|
| Warrior   | pipo-nekonin001.png |
| Mage      | pipo-nekonin005.png |
| Druid     | pipo-nekonin009.png |
| Rogue     | pipo-nekonin013.png |

## Out of Scope

| Feature | Reason |
|---------|--------|
| Attack/ability animations | Sprites don't have attack frames |
| Death animation | Out of scope for prototype |
| Custom sprite per-ability | Use particle effects instead (M3) |

---

## User Stories

### P1: SpriteSheet loader ⭐ MVP

**Acceptance Criteria**:
1. WHEN SpriteSheet loaded with a path THEN it SHALL slice frames via (col * FRAME_W, row * FRAME_H)
2. WHEN get_frame(row, col) called THEN SHALL return a pygame.Surface of the correct frame
3. SHALL support horizontal flip for mirroring

### P1: AnimatedSprite component ⭐ MVP

**Acceptance Criteria**:
1. WHEN update(dt) called THEN frame index SHALL advance based on fps
2. WHEN animation changes THEN frame index SHALL reset to 0
3. WHEN draw called THEN current frame SHALL blit at the player's screen position, centered

### P1: Per-character animation state ⭐ MVP

**Acceptance Criteria**:
1. WHEN vx == 0 AND on_ground THEN animation SHALL be "idle"
2. WHEN vx < 0 THEN animation SHALL be "walk_left"
3. WHEN vx > 0 THEN animation SHALL be "walk_right"
4. WHEN NOT on_ground THEN animation SHALL be "jump"

---

## Requirement Traceability

| Req ID | Story | Status |
|--------|-------|--------|
| SPRITE-01 | SpriteSheet loader | Implementing |
| SPRITE-02 | AnimatedSprite component | Implementing |
| SPRITE-03 | Per-character animation state | Implementing |
