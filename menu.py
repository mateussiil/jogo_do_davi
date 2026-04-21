# -*- coding: utf-8 -*-
import pygame
from constants import WIDTH, HEIGHT, BLACK, DARK_GRAY, C_WARRIOR, C_MAGE, C_DRUID, C_ROGUE

_WHITE      = (255, 255, 255)
_HIGHLIGHT  = (255, 220,  60)
_DISABLED   = (100, 100, 100)
_OVERLAY    = (  0,   0,   0, 160)


def _center_x(surf, surface_w):
    return (surface_w - surf.get_width()) // 2


class UsernameMenu:
    MAX_LEN = 16

    def __init__(self, background, current_name=""):
        self._bg       = background
        self.text      = current_name
        self.done      = False
        self._cursor_t = 0.0
        self._font_lg  = pygame.font.SysFont("monospace", 44, bold=True)
        self._font_md  = pygame.font.SysFont("monospace", 30, bold=True)
        self._font_sm  = pygame.font.SysFont("monospace", 16)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.text.strip():
                    self.done = True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    if self.text.strip():
                        self.done = True
                else:
                    ch = event.unicode
                    if ch.isprintable() and len(self.text) < self.MAX_LEN:
                        self.text += ch

    def update(self, dt):
        self._cursor_t += dt

    def draw(self, surface):
        surface.blit(self._bg, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill(_OVERLAY)
        surface.blit(ov, (0, 0))

        title = self._font_lg.render("BEM-VINDO!", True, _WHITE)
        surface.blit(title, (_center_x(title, WIDTH), 110))

        prompt = self._font_sm.render("Digite seu nome de jogador:", True, DARK_GRAY)
        surface.blit(prompt, (_center_x(prompt, WIDTH), 190))

        # Input box
        box_w, box_h = 360, 54
        box_x = (WIDTH - box_w) // 2
        box_y = 220
        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_surf.fill((20, 20, 20, 220))
        surface.blit(box_surf, (box_x, box_y))
        pygame.draw.rect(surface, _HIGHLIGHT, (box_x, box_y, box_w, box_h), 2)

        cursor = "|" if int(self._cursor_t * 2) % 2 == 0 else " "
        display = self.text + cursor
        txt = self._font_md.render(display, True, _WHITE)
        surface.blit(txt, (box_x + 14, box_y + (box_h - txt.get_height()) // 2))

        hint = self._font_sm.render("ENTER para confirmar", True, (100, 100, 100))
        surface.blit(hint, (_center_x(hint, WIDTH), 292))

        pygame.display.flip()


class MainMenu:
    def __init__(self, background, has_save):
        self._bg      = background
        self._font_lg = pygame.font.SysFont("monospace", 48, bold=True)
        self._font_md = pygame.font.SysFont("monospace", 28, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 16)
        self._items      = ["Novo Jogo", "Carregar Jogo", "Loja"]
        self._sel        = 0
        self._item_rects = []
        self.has_save    = has_save
        self.choice      = None

    # ------------------------------------------------------------------

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._sel = (self._sel - 1) % len(self._items)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._sel = (self._sel + 1) % len(self._items)
                elif event.key == pygame.K_RETURN:
                    self._confirm()
            elif event.type == pygame.MOUSEMOTION:
                self._hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._hover(event.pos)
                self._confirm()

    def _confirm(self):
        if self._sel == 0:
            self.choice = "new"
        elif self._sel == 1 and self.has_save:
            self.choice = "load"
        elif self._sel == 2:
            self.choice = "shop"

    def _hover(self, pos):
        for i, r in enumerate(self._item_rects):
            if r.collidepoint(pos):
                self._sel = i

    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.blit(self._bg, (0, 0))

        # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(_OVERLAY)
        surface.blit(overlay, (0, 0))

        # Title
        title = self._font_lg.render("2D Platformer", True, _WHITE)
        surface.blit(title, (_center_x(title, WIDTH), 140))

        sub = self._font_sm.render("use as setas + ENTER ou clique", True, DARK_GRAY)
        surface.blit(sub, (_center_x(sub, WIDTH), 210))

        # Menu items
        self._item_rects = []
        start_y = 290
        for i, label in enumerate(self._items):
            disabled = (i == 1 and not self.has_save)
            color = _DISABLED if disabled else (_HIGHLIGHT if i == self._sel else _WHITE)
            surf  = self._font_md.render(
                ("► " if i == self._sel and not disabled else "  ") + label,
                True, color,
            )
            x = _center_x(surf, WIDTH)
            y = start_y + i * 54
            surface.blit(surf, (x, y))
            self._item_rects.append(pygame.Rect(x, y, surf.get_width(), surf.get_height()))

        pygame.display.flip()


# ==============================================================================

class LevelSelectMenu:
    COLS  = 5
    ROWS  = 4
    TOTAL = 20

    def __init__(self, background):
        self._bg      = background
        self._font_lg = pygame.font.SysFont("monospace", 40, bold=True)
        self._font_md = pygame.font.SysFont("monospace", 22, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 14)
        self._sel        = 0
        self.choice      = None   # int 1-20, or "back"
        self._cell_rects = []

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._sel = (self._sel + 1) % self.TOTAL
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._sel = (self._sel - 1) % self.TOTAL
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._sel = min(self._sel + self.COLS, self.TOTAL - 1)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._sel = max(self._sel - self.COLS, 0)
                elif event.key == pygame.K_RETURN:
                    self.choice = self._sel + 1
                elif event.key == pygame.K_ESCAPE:
                    self.choice = "back"
            elif event.type == pygame.MOUSEMOTION:
                self._hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._hover(event.pos)
                self.choice = self._sel + 1

    def _hover(self, pos):
        for i, r in enumerate(self._cell_rects):
            if r.collidepoint(pos):
                self._sel = i

    def draw(self, surface):
        surface.blit(self._bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(_OVERLAY)
        surface.blit(overlay, (0, 0))

        title = self._font_lg.render("SELECIONAR FASE", True, _WHITE)
        surface.blit(title, (_center_x(title, WIDTH), 55))

        sub = self._font_sm.render(
            "Setas / WASD para navegar   ENTER para confirmar   ESC para voltar",
            True, DARK_GRAY,
        )
        surface.blit(sub, (_center_x(sub, WIDTH), 108))

        cell_w, cell_h = 90, 58
        gap    = 14
        grid_w = self.COLS * cell_w + (self.COLS - 1) * gap
        grid_x = (WIDTH - grid_w) // 2
        grid_y = 148

        self._cell_rects = []
        for i in range(self.TOTAL):
            col = i % self.COLS
            row = i // self.COLS
            cx  = grid_x + col * (cell_w + gap)
            cy  = grid_y + row * (cell_h + gap)
            rect = pygame.Rect(cx, cy, cell_w, cell_h)
            self._cell_rects.append(rect)

            selected   = (i == self._sel)
            cell_surf  = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
            cell_surf.fill((200, 170, 30, 220) if selected else (30, 30, 30, 200))
            surface.blit(cell_surf, (cx, cy))
            pygame.draw.rect(surface, _HIGHLIGHT if selected else (80, 80, 80), rect, 2)

            num   = self._font_md.render(str(i + 1), True, BLACK if selected else _WHITE)
            lbl   = self._font_sm.render("FASE", True, BLACK if selected else (130, 130, 130))
            surface.blit(lbl, (cx + (cell_w - lbl.get_width()) // 2, cy + 8))
            surface.blit(num, (cx + (cell_w - num.get_width()) // 2, cy + 22))

        pygame.display.flip()


# ==============================================================================

class ShopMenu:
    _CHARS  = [("Guerreiro", C_WARRIOR, 0),
               ("Mago",      C_MAGE,   40),
               ("Druida",    C_DRUID,  80),
               ("Ladino",    C_ROGUE, 130)]

    def __init__(self, background, coins, owned):
        self._bg     = background
        self.coins   = coins
        self.owned   = set(owned)
        self.choice  = None
        self._sel    = 0
        self._font_lg = pygame.font.SysFont("monospace", 36, bold=True)
        self._font_md = pygame.font.SysFont("monospace", 20, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 14)
        self._card_rects = []

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self._sel = (self._sel - 1) % 4
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._sel = (self._sel + 1) % 4
                elif event.key == pygame.K_RETURN:
                    self._try_buy(self._sel)
                elif event.key == pygame.K_r:
                    self.choice = "rename"
                elif event.key == pygame.K_ESCAPE:
                    self.choice = "back"
            elif event.type == pygame.MOUSEMOTION:
                for i, r in enumerate(self._card_rects):
                    if r.collidepoint(event.pos):
                        self._sel = i
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, r in enumerate(self._card_rects):
                    if r.collidepoint(event.pos):
                        self._sel = i
                        self._try_buy(i)

    def _try_buy(self, idx):
        _, _, price = self._CHARS[idx]
        if idx not in self.owned and self.coins >= price:
            self.coins -= price
            self.owned.add(idx)

    def draw(self, surface):
        surface.blit(self._bg, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        surface.blit(ov, (0, 0))

        title = self._font_lg.render("LOJA DE PERSONAGENS", True, (255, 215, 0))
        surface.blit(title, ((WIDTH - title.get_width()) // 2, 40))

        coin_txt = self._font_md.render(f"Suas moedas: {self.coins}", True, (255, 215, 0))
        surface.blit(coin_txt, ((WIDTH - coin_txt.get_width()) // 2, 88))

        sub = self._font_sm.render(
            "← → navegar   ENTER comprar   R mudar nome (1.000.000.000.000)   ESC voltar",
            True, (140, 140, 140))
        surface.blit(sub, (_center_x(sub, WIDTH), 116))

        cw, ch = 156, 220
        gap    = 16
        total  = len(self._CHARS) * cw + (len(self._CHARS) - 1) * gap
        sx     = (WIDTH - total) // 2
        sy     = 150

        self._card_rects = []
        for i, (name, color, price) in enumerate(self._CHARS):
            cx   = sx + i * (cw + gap)
            rect = pygame.Rect(cx, sy, cw, ch)
            self._card_rects.append(rect)

            sel = (i == self._sel)
            card = pygame.Surface((cw, ch), pygame.SRCALPHA)
            card.fill((200, 170, 30, 200) if sel else (25, 25, 25, 210))
            surface.blit(card, (cx, sy))
            pygame.draw.rect(surface, _HIGHLIGHT if sel else (70, 70, 70), rect, 2)

            # circle
            owned = i in self.owned
            circ_col = color if owned else (80, 80, 80)
            pygame.draw.circle(surface, circ_col, (cx + cw // 2, sy + 56), 30)
            if not owned:
                lk = self._font_md.render("X", True, (180, 180, 180))
                surface.blit(lk, (cx + cw // 2 - lk.get_width() // 2, sy + 42))

            # name
            nm = self._font_md.render(name, True, BLACK if sel else (220, 220, 220))
            surface.blit(nm, (cx + (cw - nm.get_width()) // 2, sy + 100))

            # status / price
            if owned:
                st = self._font_sm.render("COMPRADO", True, (80, 220, 80))
            elif self.coins >= price:
                st = self._font_sm.render(f"COMPRAR  {price}", True,
                                           BLACK if sel else _HIGHLIGHT)
            else:
                st = self._font_sm.render(f"PRECISA {price}", True, (160, 80, 80))
            surface.blit(st, (cx + (cw - st.get_width()) // 2, sy + 130))

            # coin icon
            pygame.draw.circle(surface, (255, 215, 0),
                                (cx + cw // 2, sy + 166), 9)
            pv = self._font_sm.render(str(price) if not owned else "", True, BLACK)
            surface.blit(pv, (cx + cw // 2 - pv.get_width() // 2, sy + 158))

        pygame.display.flip()


# ==============================================================================

class PauseMenu:
    def __init__(self):
        self._font_lg = pygame.font.SysFont("monospace", 36, bold=True)
        self._font_md = pygame.font.SysFont("monospace", 24, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 15)
        self._items      = ["Continuar", "Salvar Jogo", "Menu Principal"]
        self._sel        = 0
        self._item_rects = []
        self.choice      = None
        self._msg        = ""
        self._msg_timer  = 0.0

    # ------------------------------------------------------------------

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.choice = "resume"
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._sel = (self._sel - 1) % len(self._items)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._sel = (self._sel + 1) % len(self._items)
                elif event.key == pygame.K_RETURN:
                    self._confirm()
            elif event.type == pygame.MOUSEMOTION:
                self._hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._hover(event.pos)
                self._confirm()

    def _confirm(self):
        actions = ["resume", "save", "main_menu"]
        self.choice = actions[self._sel]

    def _hover(self, pos):
        for i, r in enumerate(self._item_rects):
            if r.collidepoint(pos):
                self._sel = i

    def show_message(self, text):
        self._msg       = text
        self._msg_timer = 2.0

    def update(self, dt):
        if self._msg_timer > 0:
            self._msg_timer -= dt
            if self._msg_timer <= 0:
                self._msg = ""

    # ------------------------------------------------------------------

    def draw(self, surface, dt=0):
        self.update(dt)

        # Semi-transparent overlay over the game
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(_OVERLAY)
        surface.blit(overlay, (0, 0))

        # Panel
        panel_w, panel_h = 340, 260
        panel_x = (WIDTH  - panel_w) // 2
        panel_y = (HEIGHT - panel_h) // 2
        panel   = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 200))
        surface.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(surface, _HIGHLIGHT,
                         (panel_x, panel_y, panel_w, panel_h), 2)

        # Title
        title = self._font_lg.render("PAUSADO", True, _WHITE)
        surface.blit(title, (panel_x + (panel_w - title.get_width()) // 2,
                              panel_y + 18))

        # Items
        self._item_rects = []
        start_y = panel_y + 90
        for i, label in enumerate(self._items):
            color = _HIGHLIGHT if i == self._sel else _WHITE
            surf  = self._font_md.render(
                ("► " if i == self._sel else "  ") + label,
                True, color,
            )
            x = panel_x + (panel_w - surf.get_width()) // 2
            y = start_y + i * 46
            surface.blit(surf, (x, y))
            self._item_rects.append(pygame.Rect(x, y, surf.get_width(), surf.get_height()))

        # Save confirmation message
        if self._msg:
            msg_surf = self._font_sm.render(self._msg, True, _HIGHLIGHT)
            surface.blit(msg_surf,
                         (panel_x + (panel_w - msg_surf.get_width()) // 2,
                          panel_y + panel_h - 28))

        pygame.display.flip()
