# Mario Cat — Feature Specification

_Status: **Draft**_
_Scope: Large_

## Vision

Transformar o jogo num platformer ao estilo Mario protagonizado pelo gatinho (`pipo-nekonin`).
Os sprites de gato já existem. O que falta são as mecânicas clássicas do Mario:
pisar em inimigos, coletar moedas, vidas, pontuação e fase projetada para isso.

---

## Feature 1 — Personagem Único: O Gatinho

### Contexto

O jogo atual tem 4 personagens com troca via TAB. No modo Mario, um único gato é controlado.
Os sprites `pipo-nekonin001–032` já estão em `sprites/character/`.

### User Stories

#### NEKO-01 — Cat Player (personagem único)

**Acceptance Criteria:**
1. WHEN o jogo inicia THEN o jogador controla um único gato (sem troca TAB)
2. O gato usa os sprites `pipo-nekonin` existentes com animações idle/walk/jump
3. Controles: A/D (mover), W ou SPACE (pular), sem habilidade especial
4. O gato tem `3 vidas`; ao ser atingido perde 1 vida; com 0 vidas → game over
5. Ao ser atingido o gato pisca por 1.5s de invencibilidade (sem morrer na hora)

---

## Feature 2 — Stomp (pisar nos inimigos)

### Contexto

No Mario, pular em cima do inimigo o derrota e dá um bounce para cima no jogador.
Atualmente os inimigos causam dano de contato lateral — isso deve continuar.

### Regras

- **Stomp detectado** quando: `player.rect.bottom <= enemy.rect.top + 8` E `player.vy > 0`
- **Ao stomp**: inimigo morto (animação ou rect desaparece), jogador recebe bounce (`vy = -300`), +100 pontos
- **Dano lateral**: se colidir lateralmente com inimigo → perde 1 vida (com I-frames)
- **SpikeBall e Boss**: não podem ser pisados (dão dano mesmo vindo de cima)

### User Stories

#### NEKO-02 — Stomp mechanic

**Acceptance Criteria:**
1. WHEN jogador cai sobre inimigo pisável THEN inimigo morre E jogador sobe (bounce vy = -300)
2. WHEN jogador colide lateralmente com inimigo THEN perde 1 vida (I-frames de 1.5s)
3. WHEN SpikeBall ou Boss atingido por cima THEN jogador perde vida (sem stomp)
4. Inimigos pisáveis: GreenWarrior, GreenMelee, Ghost
5. WHEN inimigo morto por stomp THEN +100 ao score

---

## Feature 3 — Moedas

### Contexto

Moedas espalhadas pelo nível — o ingrediente Mario mais icônico.
Coletadas por contato; somam ao score e aparecem no HUD.

### Visual

Círculo amarelo (raio 8px) com brilho; ou sprite do tileset se disponível.
Posição: no ar entre plataformas (como Mario), não no chão.

### User Stories

#### NEKO-03 — Coins

**Acceptance Criteria:**
1. WHEN fase carregada THEN moedas aparecem nas posições definidas no level data
2. WHEN jogador toca uma moeda THEN moeda desaparece + score += 50 + coin_count += 1
3. WHEN coin_count == 100 THEN coin_count reseta para 0 E lives += 1 (como no Mario)
4. Moedas são renderizadas como círculo amarelo (8px) até haver sprite dedicado
5. Moedas salvas/carregadas junto com o estado do save (quais foram coletadas)

---

## Feature 4 — Score e Vidas no HUD

### Contexto

O HUD atual mostra nome do personagem, hint de habilidade, FPS. No modo Mario,
ele deve mostrar: score, moedas coletadas e vidas restantes.

### User Stories

#### NEKO-04 — HUD Mario-style

**Acceptance Criteria:**
1. WHEN jogo rodando THEN HUD exibe: `SCORE: XXXXXX`, `🪙 XX`, `♥ X` (ou equivalente em texto)
2. Score e lives persistem no `save.json`
3. WHEN lives == 0 THEN game over screen com opção "Tentar de novo" / "Menu principal"
4. WHEN moeda coletada THEN coin counter anima por 0.3s (flash branco)

---

## Feature 5 — Level Mario-style

### Contexto

O level atual tem plataformas genéricas e inimigos em patrulha.
Um level ao estilo Mario tem ritmo: espaços para pular, moedas como guia, inimigos posicionados
para testar o stomp, uma saída (portal/bandeira) no fim.

### User Stories

#### NEKO-05 — Level redesign

**Acceptance Criteria:**
1. Level tem largura mínima de 3200px (scrolling horizontal)
2. Moedas posicionadas em arcos para guiar o caminho natural do jogador
3. Inimigos distribuídos para ensinar o stomp progressivamente (1 inimigo isolado primeiro)
4. Final do level: uma bandeira ou portal — ao tocar, fase completa ("Você venceu!" screen)
5. BreakableBlocks mantidos como segredo/atalho

---

## Requirement Traceability

| Req ID  | Story                      | Status  |
|---------|----------------------------|---------|
| NEKO-01 | Cat player (único)         | Pending |
| NEKO-02 | Stomp mechanic             | Pending |
| NEKO-03 | Coins                      | Pending |
| NEKO-04 | HUD Mario-style            | Pending |
| NEKO-05 | Level redesign             | Pending |

---

## Out of Scope (por ora)

- Power-ups (cogumelo, flor de fogo) — deferred
- Múltiplas fases — deferred
- Sons e música — deferred (M3)
- Os 4 personagens antigos: mantidos no código mas não usados neste modo
