# -*- coding: utf-8 -*-
import pygame
from constants import WIDTH, HEIGHT, BLACK, DARK_GRAY

_WHITE      = (255, 255, 255)
_HIGHLIGHT  = (255, 220,  60)
_DISABLED   = (100, 100, 100)
_OVERLAY    = (  0,   0,   0, 160)


def _center_x(surf, surface_w):
    return (surface_w - surf.get_width()) // 2


class MainMenu:
    def __init__(self, background, has_save):
        self._bg      = background
        self._font_lg = pygame.font.SysFont("monospace", 48, bold=True)
        self._font_md = pygame.font.SysFont("monospace", 28, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 16)
        self._items      = ["Novo Jogo", "Carregar Jogo"]
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
