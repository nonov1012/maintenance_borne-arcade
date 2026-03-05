#!/usr/bin/env python3
"""
Worker arrière-plan. Lancé via subprocess.Popen(start_new_session=True).
Continue de tourner même après fermeture de l'appli admin.

Usage :
  run_task.py doc <nom_jeu>
  run_task.py doc_all
  run_task.py update_check
  run_task.py git_status
  run_task.py git_pull <repo_name>
  run_task.py dep_apply <package> <version> [current_version]
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


def task_git_status():
    """Vérifie le statut (fetch + ahead/behind) de tous les dépôts configurés."""
    task_id = "git_status"
    write_status(task_id, "running", "Fetch des dépôts en cours…")
    try:
        from core.git_manager import check_all_repos
        repos = check_all_repos()
        repos_data = [r.to_dict() for r in repos]
        n_behind = sum(1 for r in repos if not r.is_up_to_date)
        msg = (f"{n_behind} dépôt(s) en retard sur {len(repos)}"
               if n_behind else f"{len(repos)} dépôt(s) à jour")
        write_status(task_id, "done", msg, {"repos": repos_data})
    except Exception as exc:
        write_status(task_id, "error", str(exc))


def task_git_pull(repo_name: str):
    """Effectue un git pull sur le dépôt identifié par son nom configuré."""
    task_id = f"git_pull_{repo_name}"
    write_status(task_id, "running", f"Pull de '{repo_name}'…", {"repo": repo_name})
    try:
        from pathlib import Path as _Path
        from core.git_manager import get_configured_repos, git_pull

        repos = get_configured_repos()
        target = next((r for r in repos if r["name"] == repo_name), None)
        if target is None:
            write_status(task_id, "error",
                         f"Dépôt '{repo_name}' introuvable dans config.json",
                         {"repo": repo_name})
            return

        success, msg = git_pull(_Path(target["path"]))
        write_status(task_id, "done" if success else "error",
                     msg[:300], {"repo": repo_name})

    except Exception as exc:
        write_status(task_id, "error", str(exc)[:300], {"repo": repo_name})


def task_dep_apply(package: str, version: str, current_version: str = "?"):
    """
    Met à jour un package pip avec test de compatibilité et rollback si nécessaire.
    Flux :
      1. Snapshot git
      2. pip install package==version
      3. Test import du package
      4. py_compile tous les jeux Python
      5a. OK  → patch requirements.txt → status "done"
      5b. KO  → analyse Ollama → rapport dans reports/ → rollback → status "incompatible"
    """
    task_id = f"dep_apply_{package}"
    extra_base = {"package": package, "from_version": current_version, "to_version": version}

    def _status(st, msg):
        write_status(task_id, st, msg, extra_base)

    _status("running", "Snapshot git…")
    try:
        import subprocess as _sp
        from core.update_checker import git_snapshot, git_rollback, _patch_requirements, PackageUpdate
        from core.compat_tester import test_all_games, build_error_report, test_package_import

        # 1. Snapshot
        snap_ok, snap_msg = git_snapshot()
        if not snap_ok:
            _status("error", f"Snapshot git échoué : {snap_msg[:200]}")
            return

        # 2. pip install
        _status("running", f"Installation de {package}=={version}…")
        pip = _sp.run(
            [sys.executable, "-m", "pip", "install", f"{package}=={version}"],
            capture_output=True, text=True,
        )
        if pip.returncode != 0:
            _status("error", f"pip échoué : {pip.stderr.strip()[:300]}")
            return

        # 3. Test import
        imp_ok, imp_err = test_package_import(package)
        if not imp_ok:
            _rollback_and_report(task_id, package, current_version, version,
                                 [], f"Import de '{package}' échoué : {imp_err}")
            return

        # 4. Compat test
        _status("running", "Test de compatibilité des jeux Python…")
        results = test_all_games()
        failed  = [r for r in results if not r.ok]

        if failed:
            report = build_error_report(package, current_version, version, results)
            _rollback_and_report(task_id, package, current_version, version,
                                 results, report)
            return

        # 5. Succès
        upd = PackageUpdate("", package, current_version, version, True)
        _patch_requirements(upd)
        _status("done", f"{package} mis à jour {current_version} → {version}")

    except Exception as exc:
        write_status(task_id, "error", str(exc)[:300], extra_base)


def _rollback_and_report(task_id: str, package: str, old_v: str, new_v: str,
                          results, report_text: str):
    """Analyse Ollama, écrit le rapport, rollback git, met à jour le statut."""
    cfg      = _load_config()
    extra    = {"package": package, "from_version": old_v, "to_version": new_v}
    rep_dir  = ADMIN_DIR / "reports"
    rep_dir.mkdir(exist_ok=True)

    # Analyse Ollama (facultatif)
    ollama_section = ""
    try:
        from core.ollama_client import OllamaWrapper
        client = OllamaWrapper(
            base_url  = cfg.get("ollama_url",   "http://10.22.28.190:11434"),
            timeout_s = 60,
        )
        if client.is_server_running():
            write_status(task_id, "running", "Analyse IA en cours…", extra)
            prompt = (
                f"Tu es un assistant de maintenance pour une borne d'arcade.\n"
                f"Après la mise à jour du package '{package}' ({old_v} → {new_v}), "
                f"des erreurs ont été détectées :\n\n{report_text}\n\n"
                f"1. Pourquoi cette mise à jour cause-t-elle ces erreurs ?\n"
                f"2. Comment les corriger ?\n"
                f"3. Faut-il éviter cette mise à jour ?\n"
                f"Réponds en français, de façon concise."
            )
            res = client.generate_text(
                model  = cfg.get("ollama_model", "qwen3:8b"),
                prompt = prompt,
            )
            ollama_section = "\n\n=== ANALYSE IA ===\n" + res.response
    except Exception:
        pass

    # Écriture rapport
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = rep_dir / f"dep_apply_{package}_{ts}.txt"
    report_file.write_text(report_text + ollama_section, encoding="utf-8")

    # Rollback pip : réinstalle l'ANCIENNE version du package
    # (git ne gère pas les packages installés sur le système)
    write_status(task_id, "running", f"Rollback pip : reinstallation de {package}=={old_v}…", extra)
    import subprocess as _sp
    if old_v and old_v != "?":
        _sp.run(
            [sys.executable, "-m", "pip", "install", f"{package}=={old_v}"],
            capture_output=True, text=True,
        )
    # Rollback git : reverte les fichiers du dépôt (requirements.txt, etc.)
    # Note : git ne peut PAS annuler les paquets apt/système — uniquement les fichiers trackés.
    write_status(task_id, "running", "Rollback git (fichiers du depot)…", extra)
    git_rollback()

    write_status(task_id, "incompatible",
                 "Mise a jour incompatible — rollback pip + git effectue. Voir rapport.",
                 {**extra, "report_file": str(report_file)})


# --- Point d'entrée ---

def main():
    if len(sys.argv) < 2:
        print("Usage: run_task.py <doc|doc_all|update_check|git_status|git_pull|dep_apply> [args]")
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

    elif command == "git_status":
        task_git_status()

    elif command == "git_pull":
        if len(sys.argv) < 3:
            print("Usage: run_task.py git_pull <repo_name>")
            sys.exit(1)
        task_git_pull(sys.argv[2])

    elif command == "dep_apply":
        if len(sys.argv) < 4:
            print("Usage: run_task.py dep_apply <package> <version> [current_version]")
            sys.exit(1)
        current = sys.argv[4] if len(sys.argv) >= 5 else "?"
        task_dep_apply(sys.argv[2], sys.argv[3], current)

    else:
        print(f"Commande inconnue : {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
