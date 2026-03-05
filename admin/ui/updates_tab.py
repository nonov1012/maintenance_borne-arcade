"""
Onglet MAJ — deux sections verticales :

  ┌─ DEPOTS GIT ──────────────────────────────────────────────────────┐
  │  Nom           Branche   Statut          Action                   │
  │  repo 1        main      A JOUR                                   │
  │  repo 2        main      3 en retard     [G] PULL                 │
  └────────────────────────────────────────────────────────────────────┘
  ┌─ DEPENDANCES PYTHON ───────────────────────────────────────────────┐
  │  Package       Actuel    Dispo     Statut                          │
  │  pygame        2.5.2     2.6.0     MAJ DISPO  [G] METTRE A JOUR   │
  │  numpy         1.24.0    1.24.0    A JOUR                         │
  └────────────────────────────────────────────────────────────────────┘

Navigation :
  UP/DOWN  naviguer dans la section active
  F        basculer la section active (Git <-> Deps)
  G        appliquer l'action sur l'element selectionne (pull / mettre a jour)
  T        lancer la verification complete (git fetch + PyPI)
  R        rafraichir l'affichage depuis les fichiers de statut
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

import pygame

ADMIN_DIR = Path(__file__).parent.parent
if str(ADMIN_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_DIR))

from core.status_utils import load_status

# --- Palette ---
_BG          = (15,  15,  40)
_ROW_ALT     = (20,  20,  55)
_SEL_ACTIVE  = (0,   70, 160)   # selection dans la section active
_SEL_IDLE    = (20,  35,  70)   # selection dans la section inactive
_TEXT        = (220, 220, 220)
_MUTED       = (120, 120, 160)
_ACCENT      = (0,  180, 255)
_BORDER      = (0,   80, 160)
_BORDER_ACT  = (0,  160, 255)   # bordure section active
_SUCCESS     = (0,  200, 100)
_WARNING     = (255, 180,   0)
_ERROR       = (255,  80,  60)
_INCOMP      = (200,  50, 200)  # incompatible

# --- Constantes de mise en page ---
_GIT_ROW_H   = 46
_DEP_ROW_H   = 44
_HEADER_H    = 32   # hauteur en-tete de section
_COL_H       = 24   # hauteur ligne des noms de colonnes
_HINTS_H     = 44   # barre d'aide en bas
_SEP_H       = 14   # separateur entre les deux sections
_GIT_MAX_VIS = 4    # max lignes git visibles


class UpdatesTab:

    def __init__(self, screen: pygame.Surface, fonts,
                 content_y: int, content_h: int, admin_dir: Path,
                 key_imgs: dict | None = None):
        self.screen    = screen
        self.f_big, self.f_med, self.f_small = fonts
        self.cy        = content_y
        self.ch        = content_h
        self.admin_dir = admin_dir
        self.W         = screen.get_width()
        self._key_imgs = key_imgs or {}

        # -- Geometrie verticale ----------------------------------------
        self._git_sec_y  = self.cy
        self._git_col_y  = self._git_sec_y + _HEADER_H
        self._git_rows_y = self._git_col_y  + _COL_H

        git_sec_bottom   = self._git_rows_y + _GIT_MAX_VIS * _GIT_ROW_H + 4

        self._sep_y      = git_sec_bottom
        self._dep_sec_y  = self._sep_y + _SEP_H
        self._dep_col_y  = self._dep_sec_y + _HEADER_H
        self._dep_rows_y = self._dep_col_y  + _COL_H

        hints_y          = self.cy + self.ch - _HINTS_H
        self._hints_y    = hints_y
        dep_area_h       = hints_y - self._dep_rows_y - 4
        self._dep_vis    = max(1, dep_area_h // _DEP_ROW_H)

        # -- Etat ---------------------------------------------------------
        self.section = 0        # 0 = git, 1 = deps

        # Section Git
        self.git_repos: List[dict] = []
        self.git_sel               = 0
        self.git_pull_st: dict     = {}   # name → statut pull

        # Section Deps
        self.updates: List[dict]   = []
        self.dep_sel               = 0
        self.dep_scroll            = 0
        self.dep_apply_st: dict    = {}   # package → statut apply

        self.status_msg = "Appuyez sur [T] pour verifier git + dependances."

    # ------------------------------------------------------------------ #
    #  Cycle de vie                                                        #
    # ------------------------------------------------------------------ #

    def on_enter(self):
        self._load_cache()

    def on_leave(self):
        pass

    def tick(self):
        self._load_cache()

    # ------------------------------------------------------------------ #
    #  Chargement des donnees                                              #
    # ------------------------------------------------------------------ #

    def _load_cache(self):
        status_dir = self.admin_dir / "workers" / "status"

        # -- Git repos --
        git_d = load_status(status_dir / "git_status.json")
        if git_d:
            if git_d.get("status") == "done":
                self.git_repos = git_d.get("repos", [])
            elif git_d.get("status") == "running":
                pass  # on garde l'ancienne liste, le message global l'indique

        # Statuts de pull individuels
        for f in status_dir.glob("git_pull_*.json"):
            d = load_status(f)
            if d:
                repo = d.get("repo") or f.stem.replace("git_pull_", "")
                self.git_pull_st[repo] = d

        # -- Dependances --
        dep_d = load_status(status_dir / "update_check.json")
        if dep_d:
            if dep_d.get("status") == "done":
                self.updates = dep_d.get("updates", [])

        # Statuts d'apply
        for f in status_dir.glob("dep_apply_*.json"):
            d = load_status(f)
            if d:
                pkg = d.get("package") or f.stem.replace("dep_apply_", "")
                self.dep_apply_st[pkg] = d

        # Message global
        n_behind = sum(1 for r in self.git_repos if r.get("behind", 0) > 0)
        n_upd    = sum(1 for u in self.updates  if u.get("has_update"))
        if git_d and git_d.get("status") == "running":
            self.status_msg = "Verification git en cours... [R] pour actualiser"
        elif dep_d and dep_d.get("status") == "running":
            self.status_msg = "Verification PyPI en cours... [R] pour actualiser"
        elif self.git_repos or self.updates:
            parts = []
            if self.git_repos:
                parts.append(f"{n_behind} depot(s) en retard" if n_behind
                             else f"{len(self.git_repos)} depot(s) a jour")
            if self.updates:
                parts.append(f"{n_upd} dep(s) a mettre a jour" if n_upd
                             else f"{len(self.updates)} deps a jour")
            self.status_msg = "  |  ".join(parts)
        else:
            self.status_msg = "Appuyez sur [T] pour verifier git + dependances."

    # ------------------------------------------------------------------ #
    #  Lancement workers                                                   #
    # ------------------------------------------------------------------ #

    def _launch(self, *args: str):
        subprocess.Popen(
            ["python3", str(self.admin_dir / "workers" / "run_task.py"), *args],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # ------------------------------------------------------------------ #
    #  Gestion des touches                                                 #
    # ------------------------------------------------------------------ #

    def handle_key(self, key: int):
        if key == pygame.K_f:
            self.section = 1 - self.section
            return
        if key == pygame.K_r:
            self._load_cache()
            return
        if key == pygame.K_t:
            self.status_msg = "Verification lancee... [R] pour actualiser"
            self._launch("git_status")
            self._launch("update_check")
            return

        if self.section == 0:
            self._key_git(key)
        else:
            self._key_dep(key)

    def _key_git(self, key: int):
        n = len(self.git_repos)
        if key == pygame.K_UP:
            self.git_sel = max(0, self.git_sel - 1)
        elif key == pygame.K_DOWN:
            self.git_sel = min(max(0, n - 1), self.git_sel + 1)
        elif key == pygame.K_g and self.git_repos:
            repo = self.git_repos[self.git_sel]
            name = repo.get("name", "")
            self.git_pull_st[name] = {"status": "running", "message": "Pull en cours..."}
            self._launch("git_pull", name)

    def _key_dep(self, key: int):
        n = len(self.updates)
        if key == pygame.K_UP:
            self.dep_sel = max(0, self.dep_sel - 1)
            self._fix_dep_scroll()
        elif key == pygame.K_DOWN:
            self.dep_sel = min(max(0, n - 1), self.dep_sel + 1)
            self._fix_dep_scroll()
        elif key == pygame.K_g and self.updates:
            u = self.updates[self.dep_sel]
            pkg = u.get("package", "")
            if u.get("has_update") and pkg:
                latest  = u.get("latest", "")
                current = u.get("current", "?")
                self.dep_apply_st[pkg] = {
                    "status":  "running",
                    "message": f"Installation {pkg}=={latest}...",
                }
                self._launch("dep_apply", pkg, latest, current)

    def _fix_dep_scroll(self):
        if self.dep_sel < self.dep_scroll:
            self.dep_scroll = self.dep_sel
        elif self.dep_sel >= self.dep_scroll + self._dep_vis:
            self.dep_scroll = self.dep_sel - self._dep_vis + 1

    # ------------------------------------------------------------------ #
    #  Rendu                                                               #
    # ------------------------------------------------------------------ #

    def draw(self):
        # Message d'etat global au-dessus des sections
        sc = (_WARNING if "cours" in self.status_msg
              else _SUCCESS if "a jour" in self.status_msg.lower()
              else _MUTED)
        self.screen.blit(
            self.f_small.render(self.status_msg[:100], True, sc),
            (30, self.cy - 22),
        )
        self._draw_git_section()
        self._draw_separator()
        self._draw_dep_section()
        self._draw_hints()

    # -- Section Git --------------------------------------------------- #

    def _draw_git_section(self):
        active   = self.section == 0
        border   = _BORDER_ACT if active else _BORDER
        sec_h    = _HEADER_H + _COL_H + _GIT_MAX_VIS * _GIT_ROW_H + 4
        sec_rect = pygame.Rect(12, self._git_sec_y, self.W - 24, sec_h)

        pygame.draw.rect(self.screen, (18, 18, 48), sec_rect, border_radius=6)
        pygame.draw.rect(self.screen, border, sec_rect, 2, border_radius=6)

        # En-tete de section
        icon  = ">" if active else " "
        tc    = _ACCENT if active else _MUTED
        self.screen.blit(
            self.f_small.render(f" {icon} DEPOTS GIT", True, tc),
            (26, self._git_sec_y + 8),
        )

        # Compteur a droite
        if self.git_repos:
            n_ok  = sum(1 for r in self.git_repos
                        if not r.get("error") and r.get("behind", 0) == 0)
            cnt   = f"{n_ok}/{len(self.git_repos)} a jour"
            cnt_c = _SUCCESS if n_ok == len(self.git_repos) else _WARNING
            cw    = self.f_small.size(cnt)[0]
            self.screen.blit(self.f_small.render(cnt, True, cnt_c),
                             (self.W - 30 - cw, self._git_sec_y + 8))

        # Colonnes
        y_col = self._git_col_y + 4
        for lbl, x in [("NOM", 28), ("BRANCHE", 330), ("STATUT", 510), ("ACTION", 790)]:
            self.screen.blit(self.f_small.render(lbl, True, _ACCENT), (x, y_col))
        pygame.draw.line(self.screen, _BORDER,
                         (20, y_col + 18), (self.W - 20, y_col + 18), 1)

        # Lignes
        if not self.git_repos:
            self.screen.blit(
                self.f_small.render("Aucun depot. [T] pour verifier.", True, _MUTED),
                (30, self._git_rows_y + 10),
            )
        else:
            for i, repo in enumerate(self.git_repos[:_GIT_MAX_VIS]):
                self._draw_git_row(repo, i,
                                   self._git_rows_y + i * _GIT_ROW_H, active)

    def _draw_git_row(self, repo: dict, idx: int, y: int, sec_active: bool):
        name   = repo.get("name",   "?")
        branch = repo.get("branch", "?")
        behind = repo.get("behind",  0)
        error  = repo.get("error")
        sel    = sec_active and idx == self.git_sel

        bg = (_SEL_ACTIVE if sel else
              _SEL_IDLE   if (not sec_active and idx == self.git_sel) else
              (_ROW_ALT if idx % 2 == 0 else _BG))
        pygame.draw.rect(self.screen, bg,
                         (20, y + 2, self.W - 40, _GIT_ROW_H - 4), border_radius=4)

        # Nom
        self.screen.blit(self.f_med.render(name[:28], True, _TEXT), (28, y + 12))
        # Branche
        self.screen.blit(self.f_small.render(branch, True, _MUTED), (330, y + 14))

        # Statut (pull ou git status)
        pull_d  = self.git_pull_st.get(name, {})
        pull_st = pull_d.get("status", "")
        if pull_st == "running":
            st_lbl, st_clr = "Pull en cours...", _WARNING
        elif pull_st == "done":
            st_lbl, st_clr = "Pull OK", _SUCCESS
        elif pull_st == "error":
            st_lbl, st_clr = "Erreur pull", _ERROR
        elif error:
            st_lbl, st_clr = "ERREUR", _ERROR
        elif behind == 0:
            st_lbl, st_clr = "A JOUR", _SUCCESS
        else:
            st_lbl, st_clr = f"{behind} commit(s) en retard", _WARNING
        self.screen.blit(self.f_small.render(st_lbl, True, st_clr), (510, y + 14))

        # Bouton
        if behind > 0 and not error and pull_st not in ("running",):
            btn_clr = _ACCENT if sel else _MUTED
            bx = 790
            bx += self._blit_key("g", bx, y, _GIT_ROW_H) + 6
            self.screen.blit(self.f_small.render("PULL", True, btn_clr),
                             (bx, y + (_GIT_ROW_H - self.f_small.get_height()) // 2))

    # -- Separateur ---------------------------------------------------- #

    def _draw_separator(self):
        y = self._sep_y + _SEP_H // 2
        pygame.draw.line(self.screen, _BORDER, (20, y), (self.W - 20, y), 1)

    # -- Section Deps -------------------------------------------------- #

    def _draw_dep_section(self):
        active   = self.section == 1
        border   = _BORDER_ACT if active else _BORDER
        dep_rows = self._dep_vis * _DEP_ROW_H
        sec_h    = _HEADER_H + _COL_H + dep_rows + 4
        sec_rect = pygame.Rect(12, self._dep_sec_y, self.W - 24, sec_h)

        pygame.draw.rect(self.screen, (18, 18, 48), sec_rect, border_radius=6)
        pygame.draw.rect(self.screen, border, sec_rect, 2, border_radius=6)

        # En-tete de section
        icon = ">" if active else " "
        tc   = _ACCENT if active else _MUTED
        self.screen.blit(
            self.f_small.render(f" {icon} DEPENDANCES PYTHON", True, tc),
            (26, self._dep_sec_y + 8),
        )

        # Compteur a droite
        if self.updates:
            n_upd = sum(1 for u in self.updates if u.get("has_update"))
            cnt   = f"{n_upd} maj / {len(self.updates)} packages"
            cnt_c = _WARNING if n_upd else _SUCCESS
            cw    = self.f_small.size(cnt)[0]
            self.screen.blit(self.f_small.render(cnt, True, cnt_c),
                             (self.W - 30 - cw, self._dep_sec_y + 8))

        # Colonnes
        y_col = self._dep_col_y + 4
        for lbl, x in [("PACKAGE", 28), ("ACTUEL", 320), ("DISPO", 470),
                        ("STATUT", 630), ("ACTION", 930)]:
            self.screen.blit(self.f_small.render(lbl, True, _ACCENT), (x, y_col))
        pygame.draw.line(self.screen, _BORDER,
                         (20, y_col + 18), (self.W - 20, y_col + 18), 1)

        if not self.updates:
            self.screen.blit(
                self.f_small.render("Aucune donnee. [T] pour verifier.", True, _MUTED),
                (30, self._dep_rows_y + 10),
            )
            return

        for i, u in enumerate(self.updates[self.dep_scroll: self.dep_scroll + self._dep_vis]):
            self._draw_dep_row(u, self.dep_scroll + i,
                               self._dep_rows_y + i * _DEP_ROW_H, active)

        if len(self.updates) > self._dep_vis:
            self._draw_dep_scrollbar()

    def _draw_dep_row(self, u: dict, idx: int, y: int, sec_active: bool):
        pkg     = u.get("package", "?")
        current = u.get("current", "?")
        latest  = u.get("latest",  "?")
        has_upd = u.get("has_update", False)
        sel     = sec_active and idx == self.dep_sel
        apply_d = self.dep_apply_st.get(pkg, {})
        apply_s = apply_d.get("status", "")

        bg = (_SEL_ACTIVE if sel else
              _SEL_IDLE   if (not sec_active and idx == self.dep_sel) else
              (_ROW_ALT if idx % 2 == 0 else _BG))
        pygame.draw.rect(self.screen, bg,
                         (20, y + 2, self.W - 40, _DEP_ROW_H - 4), border_radius=4)

        # Package
        self.screen.blit(self.f_med.render(pkg[:24], True, _TEXT), (28, y + 10))
        # Actuel
        self.screen.blit(self.f_small.render(current, True, _MUTED), (320, y + 12))
        # Dispo
        dispo_c = _WARNING if has_upd else _MUTED
        self.screen.blit(self.f_small.render(latest, True, dispo_c), (470, y + 12))

        # Statut
        if apply_s == "running":
            st_lbl = (apply_d.get("message") or "En cours...")[:36]
            st_clr = _WARNING
        elif apply_s == "done":
            old = apply_d.get("from_version", "?")
            new = apply_d.get("to_version",   "?")
            st_lbl, st_clr = f"Mis a jour {old} -> {new}", _SUCCESS
        elif apply_s == "incompatible":
            st_lbl, st_clr = "INCOMPATIBLE - rollback", _INCOMP
        elif apply_s == "error":
            st_lbl = f"Erreur: {apply_d.get('message','?')[:28]}"
            st_clr = _ERROR
        elif has_upd:
            st_lbl, st_clr = "MAJ DISPONIBLE", _WARNING
        else:
            st_lbl, st_clr = "a jour", _SUCCESS
        self.screen.blit(self.f_small.render(st_lbl, True, st_clr), (630, y + 12))

        # Action
        if has_upd and apply_s not in ("running", "done"):
            btn_clr = _ACCENT if sel else _MUTED
            bx = 930
            bx += self._blit_key("g", bx, y, _DEP_ROW_H) + 6
            self.screen.blit(
                self.f_small.render("METTRE A JOUR", True, btn_clr),
                (bx, y + (_DEP_ROW_H - self.f_small.get_height()) // 2),
            )
        elif apply_s == "incompatible":
            self.screen.blit(
                self.f_small.render("rapport -> [RAPPORTS]", True, _INCOMP),
                (930, y + 12),
            )

    def _draw_dep_scrollbar(self):
        total   = len(self.updates)
        bar_x   = self.W - 16
        bar_y   = self._dep_rows_y
        bar_h   = self._dep_vis * _DEP_ROW_H
        thumb_h = max(16, bar_h * self._dep_vis // total)
        prog    = self.dep_scroll / max(1, total - self._dep_vis)
        thumb_y = bar_y + int((bar_h - thumb_h) * prog)
        pygame.draw.rect(self.screen, _BORDER, (bar_x, bar_y, 6, bar_h), border_radius=3)
        pygame.draw.rect(self.screen, _ACCENT, (bar_x, thumb_y, 6, thumb_h), border_radius=3)

    # -- Barre d'aide -------------------------------------------------- #

    def _blit_key(self, key: str, x: int, y: int, cy: int = _HINTS_H) -> int:
        """Blitte l'image du bouton (ou texte de repli). Retourne la largeur."""
        img = self._key_imgs.get(key.lower())
        if img:
            ih = img.get_height()
            self.screen.blit(img, (x, y + (cy - ih) // 2))
            return img.get_width()
        surf = self.f_small.render(f"[{key.upper()}]", True, _ACCENT)
        self.screen.blit(surf, (x, y + (cy - self.f_small.get_height()) // 2))
        return surf.get_width()

    def _draw_hints(self):
        y = self._hints_y
        pygame.draw.line(self.screen, _BORDER, (20, y), (self.W - 20, y), 1)
        hints = [
            ("f", "Changer section"),
            ("g", "Appliquer action"),
            ("t", "Verifier tout"),
            ("r", "Rafraichir"),
        ]
        x = 30
        for k, d in hints:
            x += self._blit_key(k, x, y) + 6
            ds = self.f_small.render(d, True, _MUTED)
            self.screen.blit(ds, (x, y + (_HINTS_H - self.f_small.get_height()) // 2))
            x += ds.get_width() + 30
