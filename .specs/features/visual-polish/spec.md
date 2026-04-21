# Visual Polish Specification

_Status: **Pending**_

## Problem Statement

O jogo está funcional mas visualmente inconsistente: plataformas são retângulos cinzas/marrons
que destoam do background pixel-art de floresta. Os personagens também aparecem pequenos
demais em relação ao cenário. Três melhorias visuais são necessárias.

---

## Feature 1 — Tileset Rendering para Plataformas e Chão

### Contexto

Tileset: `sprites/enemy/tileset/1 Tiles/` — 60 tiles individuais de 32×32px.

Mapeamento observado dos tiles relevantes:

| Tile | Descrição | Uso |
|------|-----------|-----|
| Tile_01 | canto superior-esquerdo (grama) | plataforma/chão: borda esq topo |
| Tile_02 | topo central (grama) | plataforma/chão: topo center fill |
| Tile_03 | canto superior-direito (grama) | plataforma/chão: borda dir topo |
| Tile_04 | interior escuro | chão: fill interno |
| Tile_07 | topo esquerdo variante | plataforma fina: borda esq |
| Tile_08 | topo central variante | plataforma fina: center fill |
| Tile_09 | topo direito variante | plataforma fina: borda dir |
| Tile_05 | borda inferior c/ dots amarelos | chão: borda inferior |
| Tile_11 | borda lateral esquerda | chão: lado esq |
| Tile_16 | borda lateral direita | chão: lado dir |

### Estratégia de Renderização

**Plataforma flutuante (thin, ≤20px altura):**
- 1 linha de tiles escalados para caber na altura
- Tile_07 (esq) + Tile_08 repetido (meio) + Tile_09 (dir)

**Chão (≥28px altura):**
- Linha do topo: Tile_01 + Tile_02 repetido + Tile_03
- Linhas internas: Tile_04 repetido
- Tiles reescalados verticalmente para cobrir a altura do rect

**BreakableBlock:**
- Mantém visual atual (cor BREAK_COL + X marker) para ser facilmente identificável

### User Stories

#### VISUAL-01 — Plataformas com Tile

**Acceptance Criteria:**
1. WHEN Platform com altura ≤ 20px desenhada THEN SHALL usar Tile_07/08/09 (esq/meio/dir)
2. WHEN tiles não cobrem exatamente a largura THEN tile do meio SHALL ser repetido (tiling)
3. Tiles SHALL ser escalados para caber na altura do rect da plataforma
4. BreakableBlock SHALL manter visual atual (rect colorido + X)

#### VISUAL-02 — Chão com Tile

**Acceptance Criteria:**
1. WHEN Platform com altura > 20px desenhada THEN SHALL usar layout topo (01/02/03) + fill (04)
2. WHEN chão tem múltiplas linhas THEN cada linha SHALL repetir o tile correto horizontalmente
3. Tiles SHALL ser carregados uma vez e cacheados (não recarregar por frame)

---

## Feature 2 — Tamanho de Display dos Personagens

### Contexto

Sprites dos personagens são renderizados no tamanho do `rect` (hitbox): 24–36px de largura e
36–50px de altura. Com o background de floresta em 800×600, os personagens parecem minúsculos.

### Estratégia

Separar **hitbox size** (colisão) do **display size** (visual). O sprite é desenhado em torno
do centro do rect, com um tamanho de display maior.

Escala sugerida: **2.5×** o tamanho do hitbox, centralizado no rect.

### User Stories

#### VISUAL-03 — Display Scale para Personagens

**Acceptance Criteria:**
1. WHEN personagem desenhado THEN sprite SHALL ser escalado para `hitbox * DISPLAY_SCALE`
2. WHEN sprite desenhado THEN centro do sprite SHALL coincidir com centro do rect (não mover hitbox)
3. DISPLAY_SCALE SHALL ser configurável em `constants.py`
4. Hitbox (colisão) SHALL permanecer inalterado — apenas o visual muda

---

## Requirement Traceability

| Req ID | Story | Status |
|--------|-------|--------|
| VISUAL-01 | Plataformas com tile | Pending |
| VISUAL-02 | Chão com tile | Pending |
| VISUAL-03 | Display scale personagens | Pending |

---

## Implementation Notes

### Tileset path
`sprites/enemy/tileset/1 Tiles/Tile_XX.png` — 60 tiles, cada um 32×32px.

### Tile reference (confirmado visualmente)

| Tile | Visual confirmado | Uso |
|------|-------------------|-----|
| Tile_01 | canto superior-esquerdo (pedra escura + borda verde topo-esq) | chão: canto esq topo |
| Tile_02 | topo central (pedra escura + boulders verdes no topo) | chão: topo center fill |
| Tile_03 | canto superior-direito (pedra escura + borda verde topo-dir) | chão: canto dir topo |
| Tile_04 | interior (pedra escura com círculos) | chão: fill interno |
| Tile_05 | borda inferior (pedra + dots amarelos embaixo) | chão: borda inferior |
| Tile_07 | plataforma fina esquerda (fileira completa de boulders verdes, borda esq) | plataforma: borda esq |
| Tile_08 | plataforma fina centro (fileira de boulders verdes) | plataforma: center fill |
| Tile_09 | plataforma fina direita (fileira de boulders verdes, borda dir) | plataforma: borda dir |
| Tile_11 | borda lateral esquerda (pedra escura + borda verde lado esq) | chão: lado esq |
| Tile_16 | borda lateral direita (pedra escura + borda verde lado dir) | chão: lado dir |

### Estratégia de implementação

**VISUAL-01 — Plataforma flutuante (altura ≤ 20px):**
- 1 linha de tiles escalados para caber na altura
- Tile_07 (esq) + Tile_08 repetido (meio) + Tile_09 (dir)
- Carregar tiles uma vez, cachear em dict `{nome: Surface}` no início do jogo

**VISUAL-02 — Chão (altura > 20px):**
- Linha do topo: Tile_01 + Tile_02 repetido + Tile_03
- Linhas internas: Tile_04 repetido
- Opcionalmente: linha inferior com Tile_05; laterais com Tile_11/Tile_16
- Tiles reescalados verticalmente para cobrir o rect

**VISUAL-03 — Display scale dos personagens:**
- `DISPLAY_SCALE = 2.5` em `constants.py`
- `AnimatedSprite.draw()` calcula `display_w = hitbox_w * DISPLAY_SCALE`, `display_h = hitbox_h * DISPLAY_SCALE`
- Sprite desenhado centrado no rect — hitbox de colisão não muda
- Inimigos podem usar o mesmo `DISPLAY_SCALE` ou constante separada

**BreakableBlock:** mantém visual atual (rect colorido + marcador X) — não recebe tiles.
