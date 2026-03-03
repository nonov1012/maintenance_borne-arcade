"""
Onglet MISES À JOUR : vérification des packages Python via PyPI.

Touches :
  T   lancer la vérification (arrière-plan)
  R   rafraîchir l'affichage depuis le fichier status
  ↑↓  naviguer dans la liste
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

_BG       = (15,  15,  40)
_ROW_ALT  = (20,  20,  55)
_SELECTED = (0,   60, 140)
_TEXT     = (220, 220, 220)
_MUTED    = (120, 120, 160)
_ACCENT   = (0,  180, 255)
_BORDER   = (0,   80, 160)
_SUCCESS  = (0,  200, 100)
_WARNING  = (255, 180,  0)
_ERROR    = (255,  80, 60)


class UpdatesTab:
    ROW_H = 56

    def __init__(self, screen: pygame.Surface, fonts, content_y: int, content_h: int, admin_dir: Path):
        self.screen    = screen
        self.f_big, self.f_med, self.f_small = fonts
        self.cy        = content_y
        self.ch        = content_h
        self.admin_dir = admin_dir
        self.W         = screen.get_width()

        self.updates: list = []
        self.selected: int = 0
        self.scroll: int   = 0
        self.visible       = (content_h - 110) // self.ROW_H
        self.status_msg    = "Appuyez sur [T] pour vérifier les mises à jour."
        self.check_status: str | None = None

    def on_enter(self):
        self._load_cache()

    def on_leave(self):
        pass

    def tick(self):
        self._load_cache()

    def _load_cache(self):
        path = self.admin_dir / "workers" / "status" / "update_check.json"
        d = load_status(path)
        if d is None:
            self.status_msg = "Pas de données. [T] pour vérifier."
            return
        self.check_status = d.get("status")
        if self.check_status == "done":
            self.updates = d.get("updates", [])
            n = sum(1 for u in self.updates if u.get("has_update"))
            self.status_msg = f"{n} mise(s) à jour disponible(s) sur {len(self.updates)} packages"
        elif self.check_status == "running":
            self.status_msg = "Vérification en cours… [R] pour actualiser"
        elif self.check_status == "error":
            self.status_msg = f"Erreur : {d.get('message', '?')}"
        else:
            self.status_msg = d.get("message", "Statut inconnu")

    def _launch(self, *args: str):
        subprocess.Popen(
            ["python3", str(self.admin_dir / "workers" / "run_task.py"), *args],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def handle_key(self, key: int):
        if key == pygame.K_UP:
            self.selected = max(0, self.selected - 1)
            self._fix_scroll()
        elif key == pygame.K_DOWN:
            self.selected = min(max(0, len(self.updates) - 1), self.selected + 1)
            self._fix_scroll()
        elif key == pygame.K_t:
            self.status_msg = "Vérification lancée en arrière-plan… [R] pour actualiser"
            self._launch("update_check")
        elif key == pygame.K_r:
            self._load_cache()

    def _fix_scroll(self):
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + self.visible:
            self.scroll = self.selected - self.visible + 1

    def draw(self):
        # Barre de statut
        sc = _WARNING if "cours" in self.status_msg else _SUCCESS if "disponible" in self.status_msg else _MUTED
        self.screen.blit(self.f_small.render(self.status_msg[:90], True, sc), (30, self.cy + 8))

        if not self.updates:
            self.screen.blit(
                self.f_med.render("Aucune donnée. [T] pour vérifier.", True, _MUTED),
                (40, self.cy + 55),
            )
            self._draw_hints()
            return

        self._draw_header()
        for i, u in enumerate(self.updates[self.scroll: self.scroll + self.visible]):
            self._draw_row(u, self.scroll + i, self.cy + 80 + i * self.ROW_H)
        self._draw_hints()

    def _draw_header(self):
        y = self.cy + 38
        for label, x in [("JEU", 30), ("PACKAGE", 200), ("ACTUEL", 450), ("DISPO", 620), ("STATUT", 800)]:
            self.screen.blit(self.f_small.render(label, True, _ACCENT), (x, y))
        pygame.draw.line(self.screen, _BORDER, (20, y + 22), (self.W - 20, y + 22), 1)

    def _draw_row(self, u: dict, idx: int, y: int):
        sel = idx == self.selected
        bg = _SELECTED if sel else (_ROW_ALT if idx % 2 == 0 else _BG)
        pygame.draw.rect(self.screen, bg, (20, y, self.W - 40, self.ROW_H - 4), border_radius=5)

        self.screen.blit(self.f_small.render(u.get("game", "")[:18], True, _MUTED), (30, y + 18))
        self.screen.blit(self.f_med.render(u.get("package", "")[:22], True, _TEXT), (200, y + 14))
        self.screen.blit(self.f_small.render(u.get("current", "?"), True, _MUTED), (450, y + 18))

        has_upd = u.get("has_update", False)
        lc = _SUCCESS if has_upd else _MUTED
        self.screen.blit(self.f_small.render(u.get("latest", "?"), True, lc), (620, y + 18))

        label, lcolor = ("MAJ DISPO", _WARNING) if has_upd else ("à jour", _SUCCESS)
        self.screen.blit(self.f_small.render(label, True, lcolor), (800, y + 18))

    def _draw_hints(self):
        y = self.cy + self.ch - 40
        pygame.draw.line(self.screen, _BORDER, (20, y), (self.W - 20, y), 1)
        hints = [("T", "Vérifier les MAJ"), ("R", "Rafraîchir")]
        x = 30
        for k, d in hints:
            ks = self.f_small.render(f"[{k}]", True, _ACCENT)
            ds = self.f_small.render(d, True, _MUTED)
            self.screen.blit(ks, (x, y + 12)); x += ks.get_width() + 4
            self.screen.blit(ds, (x, y + 12)); x += ds.get_width() + 28
