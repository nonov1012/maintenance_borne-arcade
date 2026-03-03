"""
Publication des docs générées sur GitHub Pages.

Après une génération réussie :
  - Copie la doc dans docs/<jeu>/ (HTML API ou README.md Ollama)
  - Régénère docs/index.html
  - git add docs/ → commit → push

L'IA ne touche jamais au code source.
"""
from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .game_scanner import GameInfo

ADMIN_DIR = Path(__file__).parent.parent
REPO_ROOT  = ADMIN_DIR.parent
DOCS_DIR   = REPO_ROOT / "docs"


# ---------------------------------------------------------------------------
# Copie locale
# ---------------------------------------------------------------------------

def copy_game_doc(game: GameInfo, result: dict) -> bool:
    """
    Copie la doc générée dans docs/<jeu>/.
    Retourne True si quelque chose a été copié.
    """
    method = result.get("method")
    game_docs = DOCS_DIR / game.name
    game_docs.mkdir(parents=True, exist_ok=True)

    if method in ("javadoc", "pydoc"):
        src = game.path / "doc"
        if src.exists() and any(src.iterdir()):
            dst = game_docs / "api"
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            return True

    elif method == "ollama":
        src = game.path / "README.draft.md"
        if src.exists():
            shutil.copy2(src, game_docs / "README.md")
            return True

    return False


# ---------------------------------------------------------------------------
# Index HTML
# ---------------------------------------------------------------------------

def regenerate_index() -> None:
    """Met à jour docs/index.html avec la liste de tous les jeux documentés."""
    DOCS_DIR.mkdir(exist_ok=True)

    games = sorted(
        d.name for d in DOCS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )

    rows = []
    for g in games:
        g_dir = DOCS_DIR / g
        links = []
        if (g_dir / "api" / "index.html").exists():
            links.append(f'<a href="{g}/api/index.html">Documentation API</a>')
        if (g_dir / "README.md").exists():
            links.append(f'<a href="{g}/README.md">README (IA)</a>')
        if links:
            rows.append(f'    <li><strong>{g}</strong> &mdash; {" | ".join(links)}</li>')

    items_html = "\n".join(rows) if rows else \
        "    <li><em>Aucune documentation disponible pour l'instant.</em></li>"

    now = datetime.now().strftime("%Y-%m-%d à %H:%M")
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Documentation Borne Arcade</title>
  <style>
    body  {{ font-family: sans-serif; max-width: 800px; margin: 2em auto; padding: 0 1em; color: #222; }}
    h1   {{ border-bottom: 2px solid #0969da; padding-bottom: .3em; color: #0969da; }}
    li   {{ margin: .5em 0; }}
    a    {{ color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    footer {{ margin-top: 2em; font-size: .85em; color: #888; border-top: 1px solid #ddd; padding-top: .5em; }}
  </style>
</head>
<body>
  <h1>Documentation Borne Arcade</h1>
  <ul>
{items_html}
  </ul>
  <footer>Générée automatiquement le {now}</footer>
</body>
</html>
"""
    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Git push
# ---------------------------------------------------------------------------

def git_push_docs(label: str) -> dict:
    """
    git add docs/ → commit → push.
    Retourne dict{success: bool, output/error: str}.
    """
    try:
        subprocess.run(
            ["git", "add", "docs/"],
            cwd=str(REPO_ROOT), check=True, capture_output=True, text=True,
        )

        msg = f"doc: {label} — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        commit = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(REPO_ROOT), capture_output=True, text=True,
        )

        if commit.returncode != 0:
            combined = commit.stdout + commit.stderr
            if "nothing to commit" in combined:
                return {"success": True, "output": "Rien à commiter"}
            return {"success": False, "error": commit.stderr.strip() or commit.stdout.strip()}

        push = subprocess.run(
            ["git", "push"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=60,
        )
        if push.returncode != 0:
            return {"success": False, "error": push.stderr.strip() or push.stdout.strip()}

        return {"success": True, "output": push.stdout.strip() or "Publié."}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "git push timeout (60s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
