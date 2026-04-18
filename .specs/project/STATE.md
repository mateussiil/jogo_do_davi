# Project State

_Last updated: 2026-04-18_

## Status

M1 (Core Platformer) is complete. Codebase lives in a single file `platformer.py`. Sprite assets are downloaded but not yet integrated.

## Decisions

| Date | Decision | Reason |
|------|----------|--------|
| — | Single-file architecture for prototype | Simplicity; refactor into modules when adding sprites |
| — | Colored rectangles for characters/platforms | Placeholder; sprite integration is M2 |
| — | AABB physics with integer pixel steps | Sufficient for a 2D platformer at 60 FPS |

## Blockers

_None._

## Deferred Ideas

- Networked co-op: each player controls one character
- Procedurally generated levels
- Character unlock progression
- Ability upgrades / skill trees

## Preferences

_No model tips recorded yet._
