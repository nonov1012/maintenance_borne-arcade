"""
Test de compatibilité des jeux Python après mise à jour d'une dépendance.

Stratégie :
  1. py_compile sur tous les fichiers .py de chaque jeu (détecte les erreurs
     de syntaxe et les changements d'API visibles à la compilation).
  2. Tentative d'import du package mis à jour pour s'assurer qu'il est
     utilisable (certaines dépendances cassent à l'import après update).

Le résultat est sérialisable en JSON via to_dict().
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

PROJECT_DIR = Path(__file__).parent.parent.parent / "projet"


@dataclass
class CompatResult:
    game_name: str
    ok: bool
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"game": self.game_name, "ok": self.ok, "errors": self.errors}


def test_python_game(game_path: Path) -> CompatResult:
    """
    Vérifie la syntaxe de tous les fichiers .py d'un jeu.
    Retourne un CompatResult avec la liste des erreurs.
    """
    errors: List[str] = []

    for py_file in sorted(game_path.rglob("*.py")):
        r = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            rel = str(py_file.relative_to(game_path))
            errors.append(f"{rel}: {r.stderr.strip()[:300]}")

    return CompatResult(game_path.name, ok=len(errors) == 0, errors=errors)


def test_package_import(package: str) -> tuple:
    """
    Tente d'importer le package via un sous-processus.
    Retourne (success: bool, error_msg: str).
    """
    r = subprocess.run(
        [sys.executable, "-c", f"import {package}"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return False, r.stderr.strip()[:400]
    return True, ""


def test_all_games(project_dir: Path = PROJECT_DIR) -> List[CompatResult]:
    """
    Teste tous les jeux Python trouvés dans project_dir.
    Retourne la liste des résultats (un par jeu).
    """
    results: List[CompatResult] = []
    if not project_dir.exists():
        return results

    for game_dir in sorted(project_dir.iterdir()):
        if game_dir.is_dir() and list(game_dir.rglob("*.py")):
            results.append(test_python_game(game_dir))

    return results


def build_error_report(package: str, old_v: str, new_v: str,
                        results: List[CompatResult]) -> str:
    """
    Construit un rapport textuel des erreurs de compatibilité.
    Ce texte est envoyé à Ollama ET sauvegardé dans reports/.
    """
    failed = [r for r in results if not r.ok]
    lines = [
        f"=== RAPPORT DE COMPATIBILITÉ ===",
        f"Package : {package}  {old_v} → {new_v}",
        f"Jeux en erreur : {len(failed)} / {len(results)}",
        "",
    ]
    for r in failed:
        lines.append(f"[{r.game_name}]")
        for e in r.errors:
            lines.append(f"  • {e}")
        lines.append("")
    return "\n".join(lines)
