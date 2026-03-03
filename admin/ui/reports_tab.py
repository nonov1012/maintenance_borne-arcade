"""
Onglet RAPPORTS : liste et visionneuse des fichiers générés dans reports/.

Touches (liste) :
  ↑↓  naviguer
  F   ouvrir le rapport sélectionné
  R   rafraîchir la liste

Touches (visionneuse) :
  ↑↓  scroller
  R   fermer
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pygame

_BG       = (15,  15,  40)
_VIEWER   = (8,    8,  25)
_ROW_ALT  = (20,  20,  55)
_SELECTED = (0,   60, 140)
_TEXT     = (220, 220, 220)
_MUTED    = (120, 120, 160)
_ACCENT   = (0,  180, 255)
_BORDER   = (0,   80, 160)


class ReportsTab:
    ROW_H    = 50
    LINE_H   = 18

    def __init__(self, screen: pygame.Surface, fonts, content_y: int, content_h: int, admin_dir: Path):
        self.screen    = screen
        self.f_big, self.f_med, self.f_small = fonts
        self.cy        = content_y
        self.ch        = content_h
        self.admin_dir = admin_dir
        self.W         = screen.get_width()

        self.reports: List[Path] = []
        self.selected: int = 0
        self.scroll: int   = 0
        self.visible       = (content_h - 90) // self.ROW_H

        # Visionneuse
        self.viewing: Optional[Path] = None
        self.view_lines: List[str]   = []
        self.view_scroll: int        = 0
        self.view_visible = (content_h - 70) // self.LINE_H

    def on_enter(self):
        self._refresh()

    def on_leave(self):
        self.viewing = None

    def tick(self):
        if not self.viewing:   # ne pas perturber la lecture en cours
            self._refresh()

    def _refresh(self):
        d = self.admin_dir / "reports"
        d.mkdir(exist_ok=True)
        self.reports = sorted(
            (p for p in d.iterdir() if p.is_file()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def handle_key(self, key: int):
        if self.viewing:
            if key == pygame.K_UP:
                self.view_scroll = max(0, self.view_scroll - 3)
            elif key == pygame.K_DOWN:
                max_s = max(0, len(self.view_lines) - self.view_visible)
                self.view_scroll = min(max_s, self.view_scroll + 3)
            elif key == pygame.K_r:
                self.viewing = None
        else:
            if key == pygame.K_UP:
                self.selected = max(0, self.selected - 1)
                self._fix_scroll()
            elif key == pygame.K_DOWN:
                self.selected = min(max(0, len(self.reports) - 1), self.selected + 1)
                self._fix_scroll()
            elif key == pygame.K_f and self.reports:
                self._open(self.reports[self.selected])
            elif key == pygame.K_r:
                self._refresh()

    def _fix_scroll(self):
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + self.visible:
            self.scroll = self.selected - self.visible + 1

    def _open(self, path: Path):
        try:
            self.view_lines = path.read_text(errors="replace").splitlines()
        except Exception as e:
            self.view_lines = [f"Erreur : {e}"]
        self.view_scroll = 0
        self.viewing = path

    # --- Rendu ---

    def draw(self):
        if self.viewing:
            self._draw_viewer()
        else:
            self._draw_list()

    def _draw_list(self):
        if not self.reports:
            self.screen.blit(
                self.f_med.render("Aucun rapport généré.", True, _MUTED),
                (40, self.cy + 20),
            )
            self._draw_hints_list()
            return

        # En-tête
        y = self.cy + 8
        self.screen.blit(self.f_small.render("FICHIER", True, _ACCENT), (30, y))
        self.screen.blit(self.f_small.render("TAILLE", True, _ACCENT), (900, y))
        pygame.draw.line(self.screen, _BORDER, (20, y + 24), (self.W - 20, y + 24), 1)

        for i, rpt in enumerate(self.reports[self.scroll: self.scroll + self.visible]):
            ri = self.scroll + i
            ry = self.cy + 38 + i * self.ROW_H
            sel = ri == self.selected
            bg = _SELECTED if sel else (_ROW_ALT if ri % 2 == 0 else _BG)
            pygame.draw.rect(self.screen, bg, (20, ry, self.W - 40, self.ROW_H - 4), border_radius=5)

            self.screen.blit(self.f_small.render(rpt.name[:65], True, _TEXT), (30, ry + 16))
            try:
                sz = rpt.stat().st_size
                label = f"{sz // 1024} Ko" if sz >= 1024 else f"{sz} o"
            except Exception:
                label = "?"
            self.screen.blit(self.f_small.render(label, True, _MUTED), (900, ry + 16))

        self._draw_hints_list()

    def _draw_hints_list(self):
        y = self.cy + self.ch - 40
        pygame.draw.line(self.screen, _BORDER, (20, y), (self.W - 20, y), 1)
        hints = [("F", "Ouvrir"), ("R", "Rafraîchir")]
        x = 30
        for k, d in hints:
            ks = self.f_small.render(f"[{k}]", True, _ACCENT)
            ds = self.f_small.render(d, True, _MUTED)
            self.screen.blit(ks, (x, y + 12)); x += ks.get_width() + 4
            self.screen.blit(ds, (x, y + 12)); x += ds.get_width() + 28

    def _draw_viewer(self):
        # Fond
        pygame.draw.rect(self.screen, _VIEWER, (0, self.cy, self.W, self.ch))

        # Titre
        self.screen.blit(
            self.f_small.render(f"  {self.viewing.name}", True, _ACCENT),
            (20, self.cy + 6),
        )
        pygame.draw.line(self.screen, _BORDER, (0, self.cy + 28), (self.W, self.cy + 28), 1)

        # Contenu
        for i, line in enumerate(self.view_lines[self.view_scroll: self.view_scroll + self.view_visible]):
            y = self.cy + 34 + i * self.LINE_H
            self.screen.blit(self.f_small.render(line[:130], True, _TEXT), (12, y))

        # Scrollbar
        total = len(self.view_lines)
        if total > self.view_visible:
            bar_h   = self.ch - 55
            thumb_h = max(20, int(bar_h * self.view_visible / total))
            progress = self.view_scroll / max(1, total - self.view_visible)
            thumb_y  = self.cy + 32 + int((bar_h - thumb_h) * progress)
            pygame.draw.rect(self.screen, _BORDER,  (self.W - 12, self.cy + 32, 8, bar_h), border_radius=4)
            pygame.draw.rect(self.screen, _ACCENT,  (self.W - 12, thumb_y,       8, thumb_h), border_radius=4)

        # Bas
        y = self.cy + self.ch - 30
        pygame.draw.line(self.screen, _BORDER, (0, y), (self.W, y), 1)
        self.screen.blit(self.f_small.render("[R] Fermer    [↑↓] Scroller", True, _MUTED), (20, y + 8))
