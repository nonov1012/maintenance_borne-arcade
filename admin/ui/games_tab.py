"""
Onglet JEUX : liste auto-détectée, ratio de commentaires, statut doc, lancement de génération.

Touches :
  ↑↓  naviguer
  G   générer la doc du jeu sélectionné (arrière-plan)
  T   générer la doc de tous les jeux (arrière-plan)
  R   rafraîchir les statuts des workers
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

import pygame

ADMIN_DIR = Path(__file__).parent.parent
if str(ADMIN_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_DIR))

from core.status_utils import load_status

# Palette
_BG        = (15,  15,  40)
_ROW_ALT   = (20,  20,  55)
_SELECTED  = (0,   60, 140)
_TEXT      = (220, 220, 220)
_MUTED     = (120, 120, 160)
_ACCENT    = (0,  180, 255)
_BORDER    = (0,   80, 160)
_SUCCESS   = (0,  200, 100)
_WARNING   = (255, 180,  0)
_ERROR     = (255,  80, 60)
_LANG_CLR  = {"java": (255, 160, 0), "python": (70, 130, 255),
               "lua": (180, 60, 200), "unknown": _MUTED}


class GamesTab:
    ROW_H = 62

    def __init__(self, screen: pygame.Surface, fonts, content_y: int, content_h: int, admin_dir: Path):
        self.screen    = screen
        self.f_big, self.f_med, self.f_small = fonts
        self.cy        = content_y
        self.ch        = content_h
        self.admin_dir = admin_dir
        self.W         = screen.get_width()

        self.games: list  = []
        self.selected: int = 0
        self.scroll: int   = 0
        self.visible       = (content_h - 90) // self.ROW_H
        self.statuses: dict[str, str] = {}   # game_name → "[status] message"

    # --- Cycle de vie ---

    def on_enter(self):
        self._scan_games()
        self._refresh_statuses()

    def on_leave(self):
        pass

    def tick(self):
        self._refresh_statuses()

    # --- Données ---

    def _scan_games(self):
        try:
            from core.game_scanner import scan_games
            self.games = scan_games()
        except Exception as e:
            self.games = []
            self.statuses["_err"] = f"Erreur scan : {e}"

    def _refresh_statuses(self):
        status_dir = self.admin_dir / "workers" / "status"
        if not status_dir.exists():
            return
        for f in status_dir.glob("doc_*.json"):
            d = load_status(f)
            if d:
                key = d.get("game", f.stem)
                self.statuses[key] = f"[{d.get('status','')}] {d.get('message','')}"

    def _launch(self, *args: str):
        subprocess.Popen(
            ["python3", str(self.admin_dir / "workers" / "run_task.py"), *args],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # --- Entrées ---

    def handle_key(self, key: int):
        if key == pygame.K_UP:
            self.selected = max(0, self.selected - 1)
            self._fix_scroll()
        elif key == pygame.K_DOWN:
            self.selected = min(len(self.games) - 1, self.selected + 1)
            self._fix_scroll()
        elif key == pygame.K_g and self.games:
            name = self.games[self.selected].name
            self.statuses[name] = "[running] Démarré…"
            self._launch("doc", name)
        elif key == pygame.K_t:
            self.statuses["_all"] = "[running] Génération de tous les jeux…"
            self._launch("doc_all")
        elif key == pygame.K_r:
            self._refresh_statuses()

    def _fix_scroll(self):
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + self.visible:
            self.scroll = self.selected - self.visible + 1

    # --- Rendu ---

    def draw(self):
        if not self.games:
            self.screen.blit(
                self.f_med.render("Aucun jeu trouvé dans projet/", True, _MUTED),
                (40, self.cy + 20),
            )
            self._draw_hints()
            return

        self._draw_header()
        for i, game in enumerate(self.games[self.scroll: self.scroll + self.visible]):
            self._draw_row(game, self.scroll + i, self.cy + 52 + i * self.ROW_H)
        self._draw_hints()

    def _draw_header(self):
        y = self.cy + 8
        for label, x in [("NOM", 30), ("LANG", 310), ("DOC", 460), ("STATUT", 620)]:
            self.screen.blit(self.f_small.render(label, True, _ACCENT), (x, y))
        pygame.draw.line(self.screen, _BORDER, (20, self.cy + 40), (self.W - 20, self.cy + 40), 1)

    def _draw_row(self, game, idx: int, y: int):
        sel = idx == self.selected
        bg = _SELECTED if sel else (_ROW_ALT if idx % 2 == 0 else _BG)
        pygame.draw.rect(self.screen, bg, (20, y, self.W - 40, self.ROW_H - 4), border_radius=5)

        # Nom
        self.screen.blit(self.f_med.render(game.name[:28], True, _TEXT), (30, y + 18))

        # Langage
        lc = _LANG_CLR.get(game.language, _MUTED)
        self.screen.blit(self.f_small.render(game.language.upper(), True, lc), (310, y + 22))

        # Statut doc
        if game.has_doc:
            ds, dc = "javadoc ✓", _SUCCESS
        elif game.has_readme:
            ds, dc = "README ✓", _WARNING
        else:
            ds, dc = "aucune", _ERROR
        self.screen.blit(self.f_small.render(ds, True, dc), (460, y + 22))

        # Statut worker
        msg = self.statuses.get(game.name, "")
        if msg:
            mc = _SUCCESS if "done" in msg else _WARNING if "running" in msg else _ERROR
            self.screen.blit(self.f_small.render(msg[:50], True, mc), (620, y + 22))

    def _draw_hints(self):
        y = self.cy + self.ch - 40
        pygame.draw.line(self.screen, _BORDER, (20, y), (self.W - 20, y), 1)
        hints = [("G", "Générer doc sélectionné"), ("T", "Générer tout"), ("R", "Rafraîchir statuts")]
        x = 30
        for k, d in hints:
            ks = self.f_small.render(f"[{k}]", True, _ACCENT)
            ds = self.f_small.render(d, True, _MUTED)
            self.screen.blit(ks, (x, y + 12)); x += ks.get_width() + 4
            self.screen.blit(ds, (x, y + 12)); x += ds.get_width() + 28
