"""
Détecte automatiquement les jeux dans projet/ et analyse leur code source.
Aucun jeu n'est hardcodé : tout est découvert dynamiquement.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

ADMIN_DIR = Path(__file__).parent.parent
PROJECT_DIR = ADMIN_DIR.parent / "projet"


@dataclass
class GameInfo:
    name: str
    path: Path
    language: str          # "java", "python", "lua", "unknown"
    source_files: List[Path] = field(default_factory=list)
    comment_ratio: float = 0.0
    has_readme: bool = False
    has_doc: bool = False
    requirements: List[str] = field(default_factory=list)

    @property
    def doc_status(self) -> str:
        if self.has_doc:
            return "doc"
        if self.has_readme:
            return "readme"
        return "none"


# --- Comptage de commentaires ---

def _ratio_java(files: List[Path]) -> float:
    total = comment = 0
    in_block = False
    for f in files:
        try:
            for line in f.read_text(errors="replace").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                total += 1
                if in_block:
                    comment += 1
                    if "*/" in stripped:
                        in_block = False
                elif stripped.startswith("//") or stripped.startswith("*"):
                    comment += 1
                elif "/*" in stripped:
                    comment += 1
                    after = stripped[stripped.index("/*") + 2:]
                    if "*/" not in after:
                        in_block = True
        except Exception:
            pass
    return comment / total if total else 0.0


def _ratio_python(files: List[Path]) -> float:
    total = comment = 0
    in_docstring = False
    delim = None
    for f in files:
        try:
            for line in f.read_text(errors="replace").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                total += 1
                if in_docstring:
                    comment += 1
                    if delim in stripped:
                        in_docstring = False
                        delim = None
                elif stripped.startswith("#"):
                    comment += 1
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    delim = stripped[:3]
                    comment += 1
                    if stripped.count(delim) >= 2:  # opens and closes same line
                        delim = None
                    else:
                        in_docstring = True
        except Exception:
            pass
    return comment / total if total else 0.0


def _ratio_lua(files: List[Path]) -> float:
    total = comment = 0
    for f in files:
        try:
            for line in f.read_text(errors="replace").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                total += 1
                if stripped.startswith("--"):
                    comment += 1
        except Exception:
            pass
    return comment / total if total else 0.0


# --- Scanner principal ---

def scan_games(project_dir: Optional[Path] = None) -> List[GameInfo]:
    """Retourne la liste de tous les jeux détectés dans projet/."""
    root = project_dir or PROJECT_DIR
    if not root.exists():
        return []

    games: List[GameInfo] = []

    for game_dir in sorted(root.iterdir()):
        if not game_dir.is_dir():
            continue

        java_files   = list(game_dir.rglob("*.java"))
        python_files = list(game_dir.rglob("*.py"))
        lua_files    = list(game_dir.rglob("*.lua"))

        if java_files:
            lang, sources, ratio = "java",   java_files,   _ratio_java(java_files)
        elif python_files:
            lang, sources, ratio = "python", python_files, _ratio_python(python_files)
        elif lua_files:
            lang, sources, ratio = "lua",    lua_files,    _ratio_lua(lua_files)
        else:
            lang, sources, ratio = "unknown", [], 0.0

        has_readme = any(
            (game_dir / n).exists()
            for n in ("README.md", "README.txt", "readme.md", "README.draft.md")
        )
        has_doc = (game_dir / "doc").is_dir() or (game_dir / "docs").is_dir()

        requirements: List[str] = []
        req = game_dir / "requirements.txt"
        if req.exists():
            for line in req.read_text(errors="replace").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    requirements.append(line)

        games.append(GameInfo(
            name=game_dir.name,
            path=game_dir,
            language=lang,
            source_files=sources,
            comment_ratio=ratio,
            has_readme=has_readme,
            has_doc=has_doc,
            requirements=requirements,
        ))

    return games
