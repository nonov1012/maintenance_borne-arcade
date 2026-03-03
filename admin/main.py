#!/usr/bin/env python3
"""
Borne Arcade – Interface d'administration
Navigable joystick + 6 boutons (pas de souris).

Touches :
  ←/→   changer d'onglet
  ↑/↓   naviguer dans la liste
  F     ouvrir / confirmer
  G     action sur l'élément sélectionné
  T     action sur tout
  R     retour / fermer / rafraîchir
  H     quitter l'appli admin (retour au menu)
"""
import sys
from pathlib import Path

ADMIN_DIR = Path(__file__).parent
if str(ADMIN_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_DIR))

import pygame

from ui.games_tab   import GamesTab
from ui.updates_tab import UpdatesTab
from ui.reports_tab import ReportsTab

# --- Constantes ---
W, H   = 1280, 800
FPS    = 30
TICK_MS = 2000   # rafraîchissement auto des statuts (ms)
TAB_NAMES = ["  JEUX  ", " MAJ ", " RAPPORTS "]

# Palette globale
_BG         = (15,  15,  40)
_HEADER_BG  = (0,   25,  70)
_ACCENT     = (0,  180, 255)
_TEXT       = (220, 220, 220)
_MUTED      = (100, 100, 140)
_TAB_ON     = (0,  100, 200)
_TAB_OFF    = (18,  18,  55)
_BORDER     = (0,   80, 160)

FONT_PATH = str(ADMIN_DIR.parent / "fonts" / "PrStart.ttf")
CONTENT_Y = 148   # en-dessous de l'en-tête + onglets
CONTENT_H = H - CONTENT_Y


def load_fonts():
    try:
        fb = pygame.font.Font(FONT_PATH, 26)
        fm = pygame.font.Font(FONT_PATH, 17)
        fs = pygame.font.Font(FONT_PATH, 11)
    except Exception:
        fb = pygame.font.SysFont("monospace", 26)
        fm = pygame.font.SysFont("monospace", 17)
        fs = pygame.font.SysFont("monospace", 11)
    return fb, fm, fs


def draw_header(screen: pygame.Surface, fonts, current_tab: int):
    fb, fm, fs = fonts

    pygame.draw.rect(screen, _HEADER_BG, (0, 0, W, 78))
    pygame.draw.line(screen, _BORDER, (0, 78), (W, 78), 2)

    # Titre
    screen.blit(fm.render("BORNE ARCADE  –  ADMINISTRATION", True, _ACCENT), (20, 8))

    # Aide touches
    screen.blit(
        fs.render("←→ onglet   ↑↓ navigue   G action   T tout   F ouvrir   R retour   H quitter", True, _MUTED),
        (20, 52),
    )

    # Onglets
    tab_y, tab_h = 88, 42
    for i, name in enumerate(TAB_NAMES):
        tw = fm.size(name)[0] + 24
        tx = 20 + sum(fm.size(TAB_NAMES[j])[0] + 24 + 8 for j in range(i))
        color = _TAB_ON if i == current_tab else _TAB_OFF
        pygame.draw.rect(screen, color, (tx, tab_y, tw, tab_h), border_radius=6)
        pygame.draw.rect(screen, _BORDER, (tx, tab_y, tw, tab_h), 2, border_radius=6)
        lbl = fm.render(name, True, _TEXT if i == current_tab else _MUTED)
        screen.blit(lbl, (tx + (tw - lbl.get_width()) // 2, tab_y + (tab_h - lbl.get_height()) // 2))


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
    pygame.display.set_caption("Admin Borne Arcade")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    fonts = load_fonts()

    tabs = [
        GamesTab(screen,   fonts, CONTENT_Y, CONTENT_H, ADMIN_DIR),
        UpdatesTab(screen, fonts, CONTENT_Y, CONTENT_H, ADMIN_DIR),
        ReportsTab(screen, fonts, CONTENT_Y, CONTENT_H, ADMIN_DIR),
    ]
    current = 0
    tabs[current].on_enter()

    last_tick = pygame.time.get_ticks()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                k = event.key

                if k == pygame.K_h:
                    running = False

                elif k == pygame.K_LEFT:
                    tabs[current].on_leave()
                    current = (current - 1) % len(tabs)
                    tabs[current].on_enter()

                elif k == pygame.K_RIGHT:
                    tabs[current].on_leave()
                    current = (current + 1) % len(tabs)
                    tabs[current].on_enter()

                else:
                    tabs[current].handle_key(k)

        # Rafraîchissement automatique toutes les TICK_MS ms
        now = pygame.time.get_ticks()
        if now - last_tick >= TICK_MS:
            tabs[current].tick()
            last_tick = now

        screen.fill(_BG)
        draw_header(screen, fonts, current)
        tabs[current].draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
