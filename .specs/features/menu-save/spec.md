# Menu & Save System Specification

_Status: **Implementing**_

## Problem Statement

O jogo inicia direto no gameplay sem nenhuma tela de entrada. Não há como salvar ou retomar
progresso. Três adições são necessárias: menu principal, sistema de save/load e menu de pausa.

---

## Estados do Jogo

```
MAIN_MENU ──► PLAYING ──► PAUSED
    ▲              │           │
    └──────────────┴───────────┘
```

| Estado | Trigger de entrada | Trigger de saída |
|--------|--------------------|------------------|
| MAIN_MENU | início / "Menu Principal" no pause | "Novo Jogo" ou "Carregar Jogo" |
| PLAYING | seleção no menu | ESC → PAUSED |
| PAUSED | ESC durante PLAYING | "Continuar" → PLAYING / "Menu Principal" |

---

## Feature 1 — Menu Principal

### Acceptance Criteria

1. WHEN jogo inicia THEN SHALL exibir menu principal antes do gameplay
2. Menu SHALL mostrar título "2D Platformer" e duas opções: "Novo Jogo" / "Carregar Jogo"
3. WHEN "Carregar Jogo" selecionado E save não existe THEN opção SHALL aparecer desabilitada (cinza)
4. Navegação SHALL funcionar com setas UP/DOWN + ENTER e com clique do mouse
5. WHEN "Novo Jogo" selecionado THEN jogo SHALL iniciar do SPAWN com nível resetado
6. Background SHALL usar a mesma imagem de floresta do jogo

---

## Feature 2 — Sistema de Save/Load

### Formato do save (`save.json`)

```json
{
  "player_idx": 0,
  "position": [100, 490],
  "broken_blocks": [[514, 514], [514, 488]]
}
```

| Campo | Descrição |
|-------|-----------|
| `player_idx` | índice do personagem ativo (0-3) |
| `position` | [x, y] do centro do personagem ativo |
| `broken_blocks` | lista de [x, y] dos BreakableBlocks quebrados |

### Acceptance Criteria

1. WHEN "Salvar" selecionado THEN SHALL escrever `save.json` na raiz do projeto
2. WHEN save escrito THEN SHALL exibir mensagem "Jogo salvo!" por 2s no menu de pausa
3. WHEN "Carregar Jogo" selecionado THEN SHALL ler `save.json`, restaurar posição e blocos quebrados
4. WHEN `save.json` não existe THEN load SHALL ser silenciosamente ignorado (não crashar)
5. Personagens não ativos SHALL ser reposicionados no mesmo ponto do personagem salvo

---

## Feature 3 — Menu de Pausa

### Acceptance Criteria

1. WHEN ESC pressionado durante PLAYING THEN jogo SHALL pausar e exibir menu de pausa
2. Menu SHALL mostrar três opções: "Continuar" / "Salvar Jogo" / "Menu Principal"
3. WHEN "Continuar" selecionado THEN jogo SHALL retomar exatamente do ponto pausado
4. WHEN "Salvar Jogo" selecionado THEN SHALL salvar e exibir confirmação "Jogo salvo!"
5. WHEN "Menu Principal" selecionado THEN SHALL voltar ao menu sem resetar (permite retomar via load)
6. Menu SHALL renderizar sobre o jogo com overlay semi-transparente escuro
7. Navegação SHALL funcionar com setas UP/DOWN + ENTER e clique do mouse

---

## Implementation Notes

- `menu.py`: classes `MainMenu` e `PauseMenu`
- `Game` ganha `self.state` ("MAIN_MENU" | "PLAYING" | "PAUSED")
- Save path: `os.path.join(os.path.dirname(__file__), "save.json")`
- Ao carregar: `create_level()` + `create_enemies()` + restaurar broken_blocks por coordenada

---

## Requirement Traceability

| Req ID | Story | Status |
|--------|-------|--------|
| MENU-01 | Menu principal | Implementing |
| MENU-02 | Save/load JSON | Implementing |
| MENU-03 | Menu de pausa | Implementing |
