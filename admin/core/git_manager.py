"""
Gestion des dépôts git pour l'admin de la borne arcade.

Vérifie le statut de chaque dépôt (fetch + ahead/behind) et permet
d'effectuer un git pull. Les dépôts sont configurés dans config.json :

  "repos": [
    {"name": "main", "path": ".."},
    {"name": "autre", "path": "../chemin/vers/repo"}
  ]

Si la clé "repos" est absente, utilise la racine du projet.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

ADMIN_DIR    = Path(__file__).parent.parent
PROJECT_ROOT = ADMIN_DIR.parent


@dataclass
class RepoStatus:
    name:       str
    path:       str        # str pour faciliter la sérialisation JSON
    branch:     str
    behind:     int        # commits derrière origin
    ahead:      int        # commits en avance sur origin
    has_remote: bool
    error:      Optional[str] = None

    @property
    def is_up_to_date(self) -> bool:
        return self.behind == 0 and self.error is None

    @property
    def status_label(self) -> str:
        if self.error:
            return "ERREUR"
        if not self.has_remote:
            return "pas de remote"
        if self.behind == 0:
            return "A JOUR"
        return f"{self.behind} en retard"

    def to_dict(self) -> dict:
        return {
            "name":       self.name,
            "path":       self.path,
            "branch":     self.branch,
            "behind":     self.behind,
            "ahead":      self.ahead,
            "has_remote": self.has_remote,
            "error":      self.error,
        }


def _run(cmd: List[str], cwd: Path, timeout: int = 30) -> tuple:
    try:
        r = subprocess.run(
            cmd, cwd=str(cwd),
            capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except Exception as exc:
        return 1, "", str(exc)


def check_repo(path: Path, name: Optional[str] = None) -> RepoStatus:
    """Vérifie le statut d'un dépôt git (fetch inclus)."""
    n = name or path.name

    rc, branch, err = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], path)
    if rc != 0:
        return RepoStatus(n, str(path), "?", 0, 0, False, error="Pas un dépôt git")

    # Fetch silencieux — peut échouer si pas de réseau (on ignore l'erreur)
    _run(["git", "fetch", "--quiet", "--prune"], path, timeout=20)

    rc2, remote_out, _ = _run(["git", "remote"], path)
    has_remote = bool(remote_out)

    behind = ahead = 0
    if has_remote:
        rc3, counts, _ = _run(
            ["git", "rev-list", "--left-right", "--count", f"HEAD...origin/{branch}"],
            path,
        )
        if rc3 == 0 and counts:
            parts = counts.split()
            if len(parts) == 2:
                ahead, behind = int(parts[0]), int(parts[1])

    return RepoStatus(n, str(path), branch, behind, ahead, has_remote)


def get_configured_repos() -> List[dict]:
    """
    Retourne la liste des dépôts à surveiller, depuis config.json.
    Chaque entrée : {"name": str, "path": Path}.
    """
    try:
        cfg = json.loads((ADMIN_DIR / "config.json").read_text())
        repos_cfg = cfg.get("repos")
        if repos_cfg:
            result = []
            for r in repos_cfg:
                raw = r["path"]
                # Supporte ~ (home) et chemins relatifs à ADMIN_DIR
                if raw.startswith("~"):
                    p = Path(raw).expanduser().resolve()
                else:
                    p = (ADMIN_DIR / raw).resolve()
                result.append({"name": r.get("name", p.name), "path": p})
            return result
    except Exception:
        pass
    return [{"name": PROJECT_ROOT.name, "path": PROJECT_ROOT}]


def check_all_repos() -> List[RepoStatus]:
    """Vérifie tous les dépôts configurés et retourne leurs statuts."""
    return [check_repo(r["path"], r["name"]) for r in get_configured_repos()]


def git_pull(path: Path) -> tuple:
    """
    Effectue un git pull sur le dépôt indiqué.
    Retourne (success: bool, message: str).
    """
    rc, out, err = _run(["git", "pull"], path)
    msg = (out + ("\n" + err if err else "")).strip()
    return rc == 0, msg
