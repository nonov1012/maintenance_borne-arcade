"""
Utilitaires pour la lecture et la correction des fichiers de statut des workers.

Problème : si l'appli admin est fermée puis relancée, un worker qui était "running"
peut en fait être mort. On vérifie le PID et on corrige le fichier si besoin.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def is_pid_alive(pid: int) -> bool:
    """Retourne True si le processus avec ce PID est encore en vie."""
    try:
        os.kill(int(pid), 0)   # signal 0 = juste vérifier l'existence
        return True
    except (OSError, ProcessLookupError, ValueError):
        return False


def check_and_fix(data: dict, path: Path) -> dict:
    """
    Si le statut est 'running' et que le PID est mort, corrige le fichier
    en 'error' avec le message approprié.
    Retourne le dict (potentiellement mis à jour).
    """
    if data.get("status") != "running":
        return data

    pid = data.get("pid")
    if pid and not is_pid_alive(pid):
        data = dict(data)           # copie défensive
        data["status"] = "error"
        data["message"] = "Processus interrompu (relance l'appli admin)"
        try:
            path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    return data


def load_status(path: Path) -> dict | None:
    """Lit un fichier JSON de statut et corrige le PID si nécessaire."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return check_and_fix(data, path)
    except Exception:
        return None
