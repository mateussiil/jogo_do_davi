# Checkpoints Specification

_Status: **Implementing**_

## Problem Statement

Ao morrer (inimigo ou queda), o jogador sempre volta ao SPAWN inicial (x=40). Com o mundo
expandido para 3300px, isso torna o jogo frustrante. Checkpoints automáticos permitem retomar
do último ponto alcançado.

## Comportamento

- Checkpoints são objetos visíveis espalhados no nível (uma bandeira/poste)
- WHEN player toca um checkpoint THEN spawn atual é atualizado para aquele ponto
- Checkpoint ativado muda visualmente (bandeira acesa)
- Save inclui o checkpoint ativo — ao carregar, respawn começa do checkpoint salvo
- Cada checkpoint só ativa uma vez (não desativa ao morrer)

## Posições dos Checkpoints (uma por zona)

| ID | x | Zona |
|----|---|------|
| CP1 | 430 | início zona 2 (após gap) |
| CP2 | 1560 | início zona 3 (ponte suspensa) |
| CP3 | 2210 | início zona 4 (corredor de blocos) |
| CP4 | 2760 | início zona 5 (plataformas no céu) |
| CP5 | 3135 | área final |

## Acceptance Criteria

1. WHEN player rect toca checkpoint THEN `game.spawn` SHALL atualizar para posição do checkpoint
2. WHEN checkpoint ativado THEN visual SHALL mudar (bandeira amarela → verde)
3. WHEN player morre THEN SHALL respawnar no último checkpoint ativado
4. WHEN save inclui checkpoint THEN load SHALL restaurar o spawn correto
5. Checkpoints já ativados SHALL permanecer ativos após morte e reload

## Save format (atualizado)

```json
{
  "player_idx": 0,
  "position": [100, 490],
  "spawn": [430, 488],
  "broken_blocks": [[514, 514]],
  "checkpoints": [430]
}
```

## Requirement Traceability

| Req ID | Story | Status |
|--------|-------|--------|
| CP-01 | Checkpoint ativa spawn | Implementing |
| CP-02 | Visual ativo/inativo | Implementing |
| CP-03 | Respawn no checkpoint | Implementing |
| CP-04 | Save/load checkpoint | Implementing |
