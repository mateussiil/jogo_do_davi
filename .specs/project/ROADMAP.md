# Roadmap

## M1 — Core Platformer (✅ Done)

Playable prototype with all four characters, physics, one level, HUD.

- [x] Physics engine (AABB collision, gravity, camera scroll)
- [x] 4 characters: Warrior, Mage, Druid, Rogue
- [x] Character abilities (smash, shoot, double jump, dash)
- [x] Level designed around character strengths
- [x] HUD (name, ability hint, character dots, controls, FPS)
- [x] Respawn on fall

## M2 — Sprite Visuals (🔄 In Progress)

Replace colored rectangles with animated sprites from the pipo-nekonin asset pack.

- [x] Sprite loading and animation system (`AnimatedSprite`, `_load_sheet`, `get_frame`)
- [x] Idle / walk / jump animations per character (idle_left, idle_right, walk_left, walk_right, jump)
- [x] Background image applied (`sprites/tileset/2 Background/Background.png`)
- [x] Refactor: separação em `constants.py`, `player.py`, `platformer.py`
- [x] Enemy system com 4 tipos (GreenWarrior, GreenMelee, Ghost, SpikeBall)
- [ ] Tileset rendering para plataformas e chão (VISUAL-01, VISUAL-02) — tiles em `sprites/enemy/tileset/1 Tiles/` — spec: `features/visual-polish/`
- [ ] Display scale dos personagens — separar hitbox de visual (VISUAL-03)

- [x] Menu principal com "Novo Jogo" / "Carregar Jogo" (MENU-01)
- [x] Save/load em `save.json` com posição + blocos quebrados (MENU-02)
- [x] Menu de pausa com ESC — "Continuar" / "Salvar" / "Menu Principal" (MENU-03)

## M3 — Polish (🔲 Not started)

- [ ] Sound effects and background music
- [ ] Particle effects (dash trail, projectile impact, block break)
- [ ] Multiple levels or a level selector
- [ ] Main menu / game-over screen
