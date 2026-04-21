# Project State

_Last updated: 2026-04-18_

## Status

M2 (Sprite Visuals) em andamento. Sprites de personagem integrados e animados. Background aplicado. Código refatorado em múltiplos arquivos. Problema de escala do mapa vs. personagem sendo investigado.

## Decisions

| Date | Decision | Reason |
|------|----------|--------|
| — | Single-file architecture for prototype | Simplicity; refactor into modules when adding sprites |
| 2026-04-18 | Split em `constants.py`, `player.py`, `platformer.py` | Separação de responsabilidades; `platformer.py` = controles gerais do jogo |
| — | AABB physics com integer pixel steps | Suficiente para platformer 2D a 60 FPS |
| 2026-04-18 | Duck typing (`getattr(plat, 'breakable', False)`) em vez de isinstance | Evita import circular entre player.py e platformer.py |
| 2026-04-18 | `idle_left` / `idle_right` como animações separadas | Idle usava row 1 (walk_left), personagem ficava sempre olhando para esquerda ao parar |
| 2026-04-18 | Push mínimo de 1px para baixo quando `on_ground` | Evita flickering idle↔jump causado por truncamento do `int(vy*dt)` |
| 2026-04-18 | Background escalado para 800×600 (original 576×324) | Imagem de floresta pixel-art; cobre toda a tela sem tiling |

## Blockers

_Nenhum blocker ativo._

## Próximos (M2 restante)

- VISUAL-01/02: Tileset rendering para plataformas e chão — usar `Tile_07/08/09` (plataformas finas) e `Tile_01/02/03/04` (chão). Tiles 32×32px, escalados para caber no rect.
- VISUAL-03: `DISPLAY_SCALE = 2.5` em constants.py; sprite desenhado 2.5× o hitbox, centralizado — hitbox de colisão não muda.

## Bugs Corrigidos

| Data | Bug | Fix |
|------|-----|-----|
| 2026-04-18 | Personagem alternando idle↔jump mesmo parado | Push de 1px garante detecção de colisão com o chão todo frame |
| 2026-04-18 | Personagem sempre olhava para esquerda ao parar | Adicionado `idle_left`/`idle_right` selecionado por `facing` |

## Deferred Ideas

- Networked co-op: each player controls one character
- Procedurally generated levels
- Character unlock progression
- Ability upgrades / skill trees
- Tileset rendering para plataformas (M2 pendente)

## Preferences

_No model tips recorded yet._
