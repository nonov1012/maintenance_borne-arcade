"""
Génération de documentation par jeu.

Stratégie :
  Java   → on tente javadoc ; si exit != 0, Ollama génère README.draft.md
            (les erreurs javadoc sont transmises à Ollama pour un meilleur rapport)
  Python → on tente pydoc  ; si exit != 0 ou aucun docstring trouvé, Ollama
  Lua/? → toujours Ollama

L'IA ne touche jamais au code source : elle produit uniquement un brouillon README
à valider par un humain.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

from .game_scanner import GameInfo
from .ollama_client import OllamaWrapper, OllamaConnectionError, OllamaResponseError

ADMIN_DIR = Path(__file__).parent.parent
StatusFn = Callable[[str, str, str], None]  # (status, message, output_file)

# Patterns javadoc indiquant des commentaires manquants (exit 0 mais doc incomplète)
_JAVADOC_MISSING_PATTERNS = [
    "no comment",          # "warning: no comment"
    "no @param",           # paramètre non documenté
    "no @return",          # valeur de retour non documentée
    "no @throws",          # exception non documentée
    "missing comment",
]


def _javadoc_has_missing_comments(stderr: str) -> bool:
    """Retourne True si javadoc a émis des warnings de commentaires manquants."""
    lower = stderr.lower()
    return any(pattern in lower for pattern in _JAVADOC_MISSING_PATTERNS)


def _load_config() -> dict:
    return json.loads((ADMIN_DIR / "config.json").read_text())


def generate_doc_for_game(game: GameInfo, status_fn: Optional[StatusFn] = None) -> Dict:
    """Point d'entrée. Retourne dict{success, method, output/error}."""
    config = _load_config()
    reports_dir = ADMIN_DIR / config.get("reports_dir", "reports")
    reports_dir.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")

    def status(s: str, msg: str, out: str = ""):
        if status_fn:
            status_fn(s, msg, out)

    status("running", "Démarrage…")

    if game.language == "java":
        return _java_strategy(game, reports_dir, date_str, config, status)
    if game.language == "python":
        return _python_strategy(game, reports_dir, date_str, config, status)
    # lua / unknown
    return _ollama_readme(game, reports_dir, date_str, config, status)


# ---------------------------------------------------------------------------
# Stratégies par langage
# ---------------------------------------------------------------------------

def _java_strategy(game, reports_dir, date_str, config, status) -> Dict:
    """Tente javadoc. Si ça échoue → Ollama avec les erreurs comme contexte."""
    result = _javadoc(game, reports_dir, date_str, status)
    if result["success"]:
        return result
    # Javadoc a échoué : on transmet les erreurs à Ollama
    javadoc_errors = result.get("error", "")
    return _ollama_readme(
        game, reports_dir, date_str, config, status,
        extra_context=f"Erreurs javadoc (ce qui manque dans le code) :\n{javadoc_errors}",
    )


def _python_strategy(game, reports_dir, date_str, config, status) -> Dict:
    """Tente pydoc. Si échec ou aucun docstring → Ollama."""
    result = _pydoc(game, reports_dir, date_str, status)
    if result["success"] and _has_any_docstring(game):
        return result
    return _ollama_readme(game, reports_dir, date_str, config, status)


def _has_any_docstring(game: GameInfo) -> bool:
    """Retourne True si au moins un fichier source contient un docstring."""
    for src in game.source_files:
        try:
            content = src.read_text(errors="replace")
            if '"""' in content or "'''" in content:
                return True
        except Exception:
            pass
    return False


# ---------------------------------------------------------------------------
# Méthodes de génération
# ---------------------------------------------------------------------------

def _javadoc(game: GameInfo, reports_dir: Path, date_str: str, status: StatusFn) -> Dict:
    status("running", "Génération Javadoc…")

    out_dir = game.path / "doc"
    out_dir.mkdir(exist_ok=True)

    java_files = [str(f) for f in game.source_files]
    cmd = ["javadoc", "-cp", ".:../../..", "-d", str(out_dir), "-quiet"] + java_files

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(game.path))

    report = reports_dir / f"{date_str}_javadoc_{game.name}.txt"
    report.write_text(
        f"Javadoc – {game.name} – {date_str}\n"
        f"Fichiers sources : {len(game.source_files)}\n"
        f"Code retour : {result.returncode}\n\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}\n"
    )

    missing_docs = _javadoc_has_missing_comments(result.stderr)

    if result.returncode == 0 and not missing_docs:
        status("done", f"Javadoc générée dans {out_dir.name}/", str(report))
        return {"success": True, "method": "javadoc", "output": str(report)}
    else:
        reason = f"code {result.returncode}" if result.returncode != 0 else "commentaires manquants"
        status("running", f"Javadoc KO ({reason}), appel Ollama…")
        return {
            "success": False,
            "method": "javadoc",
            "error": result.stderr,
            "report": str(report),
        }


def _pydoc(game: GameInfo, reports_dir: Path, date_str: str, status: StatusFn) -> Dict:
    status("running", "Génération pydoc…")

    out_dir = game.path / "doc"
    out_dir.mkdir(exist_ok=True)

    generated = []
    errors = []
    for src in game.source_files[:8]:
        cmd = ["python3", "-m", "pydoc", "-w", str(src.resolve())]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(out_dir))
        if result.returncode == 0:
            generated.append(src.name)
        else:
            errors.append(f"{src.name}: {result.stderr.strip()}")

    report = reports_dir / f"{date_str}_pydoc_{game.name}.txt"
    report.write_text(
        f"Pydoc – {game.name} – {date_str}\n"
        f"Générés : {', '.join(generated) or 'aucun'}\n"
        f"Erreurs : {'; '.join(errors) or 'aucune'}\n"
    )

    if generated:
        status("done", f"Pydoc OK ({len(generated)} fichiers)", str(report))
        return {"success": True, "method": "pydoc", "output": str(report)}
    else:
        status("running", "Pydoc KO, appel Ollama…")
        return {"success": False, "method": "pydoc", "error": "; ".join(errors)}


def _ollama_readme(
    game: GameInfo,
    reports_dir: Path,
    date_str: str,
    config: dict,
    status: StatusFn,
    extra_context: str = "",
) -> Dict:
    status("running", "Envoi du code à Ollama…")

    # Collecte du code source (limite pour ne pas dépasser le contexte du LLM)
    MAX_CHARS = 6_000
    parts = []
    total = 0
    for src in game.source_files:
        try:
            content = src.read_text(errors="replace")
            if total + len(content) > MAX_CHARS:
                content = content[: MAX_CHARS - total]
                parts.append(f"// {src.name} (tronqué)\n{content}")
                break
            parts.append(f"// {src.name}\n{content}")
            total += len(content)
        except Exception:
            pass

    code_str = "\n\n".join(parts) if parts else "(aucun fichier source lisible)"

    context_block = f"\n\n{extra_context}" if extra_context else ""
    prompt = (
        f'Tu es un développeur technique. Analyse ce code source du jeu "{game.name}" '
        f"(langage : {game.language}, {len(game.source_files)} fichier(s))."
        f"{context_block}\n\n"
        "Génère un README.md professionnel avec ces sections :\n"
        "## Description\n## Gameplay\n## Architecture technique\n## Dépendances\n## Notes développeur\n\n"
        "Réponds UNIQUEMENT avec le contenu Markdown du README.\n\n"
        f"Code source :\n{code_str}"
    )

    client = OllamaWrapper(
        base_url=config.get("ollama_url", "http://10.22.28.190:11434"),
        timeout_s=300.0,
    )
    model = config.get("ollama_model", "qwen3:8b")

    try:
        status("running", f"Ollama ({model}) en cours…")
        result = client.generate_text(model=model, prompt=prompt)

        draft = game.path / "README.draft.md"
        draft.write_text(
            f"<!-- Généré automatiquement par Ollama ({model}) le {date_str} -->\n"
            f"<!-- À relire et valider avant usage -->\n\n"
            + result.response
        )

        report = reports_dir / f"{date_str}_ollama_{game.name}.md"
        report.write_text(draft.read_text())

        status("done", "README.draft.md généré par Ollama", str(draft))
        return {"success": True, "method": "ollama", "output": str(draft)}

    except (OllamaConnectionError, OllamaResponseError) as e:
        status("error", f"Erreur Ollama : {e}")
        return {"success": False, "method": "ollama", "error": str(e)}
