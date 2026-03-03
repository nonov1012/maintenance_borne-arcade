"""
Vérification des mises à jour des dépendances Python (pip + PyPI).

Principe :
  - Lit requirements.txt de chaque jeu Python
  - Interroge l'API PyPI pour la dernière version disponible
  - Génère un rapport lisible par un humain
  - Peut appliquer la mise à jour après snapshot git
  - Rollback via git revert si nécessaire

Java (MG2D + JavaLayer) : pas de package manager → rapport informatif seulement.
Lua (LÖVE) : runtime système → hors scope.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .game_scanner import GameInfo

ADMIN_DIR = Path(__file__).parent.parent
PROJECT_ROOT = ADMIN_DIR.parent


@dataclass
class PackageUpdate:
    game: str
    package: str
    current_version: str    # version dans requirements.txt (peut être "unknown")
    latest_version: str
    has_update: bool
    compatible: Optional[bool] = None   # None = pas encore vérifié


def parse_requirement(spec: str) -> Tuple[str, str]:
    """Extrait (nom, version) depuis une ligne requirements.txt."""
    m = re.match(r"^([A-Za-z0-9_\-]+)([><=!]+)?(.+)?$", spec.strip())
    if m:
        return m.group(1), (m.group(3) or "unknown").strip()
    return spec.strip(), "unknown"


def fetch_pypi_latest(package: str) -> Optional[str]:
    """Récupère la dernière version stable depuis pypi.org."""
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("info", {}).get("version")
    except Exception:
        return None


def check_updates(games: List[GameInfo]) -> List[PackageUpdate]:
    """Vérifie les mises à jour pour tous les jeux Python."""
    updates: List[PackageUpdate] = []
    seen: Dict[str, str] = {}  # package → version courante (dédup)

    for game in games:
        if game.language != "python" or not game.requirements:
            continue
        for req in game.requirements:
            name, current = parse_requirement(req)
            if name in seen:
                continue
            seen[name] = current

            latest = fetch_pypi_latest(name)
            if latest is None:
                continue

            has_update = (latest != current) and (current != "unknown")
            updates.append(PackageUpdate(
                game=game.name,
                package=name,
                current_version=current,
                latest_version=latest,
                has_update=has_update,
            ))

    return updates


# --- Rollback git ---

def git_snapshot(project_root: Path = PROJECT_ROOT) -> Tuple[bool, str]:
    """Crée un commit 'pre-update snapshot' avant toute modification."""
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    result = subprocess.run(
        ["git", "commit", "-am", f"pre-update snapshot {date_str}"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


def git_rollback(project_root: Path = PROJECT_ROOT) -> Tuple[bool, str]:
    """Annule le dernier commit (rollback après mise à jour ratée)."""
    result = subprocess.run(
        ["git", "revert", "--no-edit", "HEAD"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


# --- Application d'une mise à jour ---

def apply_update(update: PackageUpdate, project_root: Path = PROJECT_ROOT) -> Dict:
    """
    Applique une mise à jour pip.
    Snapshot git si git_auto_snapshot=true dans config.
    Retourne un rapport dict.
    """
    config = json.loads((ADMIN_DIR / "config.json").read_text())

    if config.get("git_auto_snapshot", True):
        ok, msg = git_snapshot(project_root)
        snapshot_info = f"Snapshot git : {'OK' if ok else 'ÉCHEC – ' + msg}"
    else:
        snapshot_info = "Snapshot git désactivé"

    cmd = ["pip", "install", f"{update.package}=={update.latest_version}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return {
            "success": False,
            "package": update.package,
            "error": result.stderr,
            "snapshot": snapshot_info,
        }

    # Met à jour requirements.txt
    _patch_requirements(update, project_root)

    return {
        "success": True,
        "package": update.package,
        "from": update.current_version,
        "to": update.latest_version,
        "snapshot": snapshot_info,
    }


def _patch_requirements(update: PackageUpdate, project_root: Path):
    for req_file in (project_root / "projet").rglob("requirements.txt"):
        content = req_file.read_text()
        new_content = re.sub(
            rf"^{re.escape(update.package)}[><=!]+\S+",
            f"{update.package}=={update.latest_version}",
            content,
            flags=re.MULTILINE,
        )
        req_file.write_text(new_content)
