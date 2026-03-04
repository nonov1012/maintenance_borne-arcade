#!/usr/bin/env python3
"""
Worker arrière-plan. Lancé via subprocess.Popen(start_new_session=True).
Continue de tourner même après fermeture de l'appli admin.

Usage :
  run_task.py doc <nom_jeu>
  run_task.py doc_all
  run_task.py update_check
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Chemin vers admin/ pour les imports
ADMIN_DIR = Path(__file__).parent.parent


def _load_config() -> dict:
    try:
        return json.loads((ADMIN_DIR / "config.json").read_text())
    except Exception:
        return {}
STATUS_DIR = ADMIN_DIR / "workers" / "status"
STATUS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ADMIN_DIR))


# --- Helpers statut ---

def write_status(task_id: str, status: str, message: str, extra: dict | None = None):
    data = {
        "task_id": task_id,
        "status": status,
        "message": message,
        "pid": os.getpid(),
        "updated": datetime.now().isoformat(),
        **(extra or {}),
    }
    (STATUS_DIR / f"{task_id}.json").write_text(json.dumps(data, indent=2))


def make_status_fn(task_id: str):
    """Retourne une fonction status(status, message, output_file) pour doc_generator."""
    def fn(status: str, message: str, output_file: str = ""):
        write_status(task_id, status, message, {"output_file": output_file} if output_file else None)
    return fn


# --- Tâches ---

def task_doc(game_name: str):
    task_id = f"doc_{game_name}"
    write_status(task_id, "running", f"Démarrage pour {game_name}…", {"game": game_name})
    try:
        from core.game_scanner import scan_games
        from core.doc_generator import generate_doc_for_game
        from core.doc_publisher import regenerate_index, git_push_docs

        games = {g.name: g for g in scan_games()}
        if game_name not in games:
            write_status(task_id, "error", f"Jeu introuvable : {game_name}", {"game": game_name})
            return

        result = generate_doc_for_game(games[game_name], make_status_fn(task_id))

        if result.get("success"):
            method = result.get("method")
            write_status(task_id, "done",
                         f"Doc générée via {method}",
                         {"game": game_name, "output": result.get("output", "")})

            if _load_config().get("github_pages"):
                write_status(task_id, "running", "Publication GitHub Pages…", {"game": game_name})
                regenerate_index()
                pub = git_push_docs(game_name)
                if pub.get("success"):
                    write_status(task_id, "done",
                                 f"Publié sur GitHub Pages ({method})",
                                 {"game": game_name, "output": result.get("output", "")})
                else:
                    write_status(task_id, "done",
                                 f"Doc OK — Push échoué : {pub.get('error', '')[:80]}",
                                 {"game": game_name})
        else:
            write_status(task_id, "error",
                         result.get("error", "Erreur inconnue")[:200],
                         {"game": game_name})

    except Exception as e:
        write_status(task_id, "error", str(e), {"game": game_name})


def task_doc_all():
    task_id = "doc_all"
    write_status(task_id, "running", "Génération pour tous les jeux…")
    try:
        from core.game_scanner import scan_games
        from core.doc_generator import generate_doc_for_game
        from core.doc_publisher import regenerate_index, git_push_docs

        games = scan_games()
        results = []
        github_pages = _load_config().get("github_pages", False)

        for i, game in enumerate(games):
            write_status(task_id, "running", f"[{i + 1}/{len(games)}] {game.name}…")
            res = generate_doc_for_game(game)
            results.append({"game": game.name, "success": res.get("success"), "method": res.get("method")})

        done_count = sum(1 for r in results if r["success"])

        if github_pages and done_count > 0:
            write_status(task_id, "running",
                         f"Publication de {done_count} jeux sur GitHub Pages…")
            regenerate_index()
            pub = git_push_docs("all")
            pub_msg = (f", {done_count} publiés" if pub.get("success")
                       else f", push échoué : {pub.get('error', '')[:60]}")
        else:
            pub_msg = ""

        write_status(task_id, "done",
                     f"{done_count}/{len(games)} jeux traités{pub_msg}",
                     {"results": results})

    except Exception as e:
        write_status(task_id, "error", str(e))


def task_update_check():
    task_id = "update_check"
    write_status(task_id, "running", "Interrogation de PyPI…")
    try:
        from core.game_scanner import scan_games
        from core.update_checker import check_updates

        games = scan_games()
        updates = check_updates(games)

        updates_data = [
            {
                "game": u.game,
                "package": u.package,
                "current": u.current_version,
                "latest": u.latest_version,
                "has_update": u.has_update,
            }
            for u in updates
        ]

        n = sum(1 for u in updates if u.has_update)
        write_status(task_id, "done",
                     f"{n} mise(s) à jour disponible(s) sur {len(updates)} packages",
                     {"updates": updates_data})

    except Exception as e:
        write_status(task_id, "error", str(e))


# --- Point d'entrée ---

def main():
    if len(sys.argv) < 2:
        print("Usage: run_task.py <doc|doc_all|update_check> [game_name]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "doc":
        if len(sys.argv) < 3:
            print("Usage: run_task.py doc <game_name>")
            sys.exit(1)
        task_doc(sys.argv[2])

    elif command == "doc_all":
        task_doc_all()

    elif command == "update_check":
        task_update_check()

    else:
        print(f"Commande inconnue : {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
