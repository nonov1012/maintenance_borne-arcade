# Automatisation — Borne Arcade

Ce document récapitule les deux systèmes d'automatisation développés pour la borne arcade :
la **génération de documentation** et la **mise à jour automatique des dépendances**.

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Génération de documentation](#génération-de-documentation)
3. [Mise à jour automatique](#mise-à-jour-automatique)
4. [Panneau d'administration](#panneau-dadministration)
5. [Schéma global](#schéma-global)

---

## Vue d'ensemble

```
admin/
├── main.py                    # Panneau admin Pygame (interface sans souris)
├── core/
│   ├── doc_generator.py       # Génération doc (Javadoc / pydoc / Ollama)
│   ├── doc_publisher.py       # Publication GitHub Pages
│   ├── update_checker.py      # Vérification et application des mises à jour
│   ├── ollama_client.py       # Client HTTP vers le LLM local (Ollama)
│   ├── git_manager.py         # Snapshots et rollback Git
│   └── game_scanner.py        # Détection des jeux dans projet/
├── ui/
│   ├── games_tab.py           # Onglet jeux
│   ├── updates_tab.py         # Onglet mises à jour
│   └── reports_tab.py         # Onglet rapports/documentation
└── workers/
    ├── run_task.py             # Worker subprocess en arrière-plan
    └── status/                # Fichiers JSON de statut des tâches
```

---

## Génération de documentation

### Pipeline général

```
projet/<jeu>/
    │
    ├── *.java  →  javadoc  →  HTML  ──────────────────────────────┐
    │                          (si erreur ou pas de commentaires)  │
    │                          → Ollama (README.md généré par LLM) │
    │                                                              │
    ├── *.py    →  pydoc    →  HTML  ──────────────────────────────┤
    │                          (si pas de docstrings)              │
    │                          → Ollama (README.md généré par LLM) │
    │                                                              │
    └── *.lua   →  Ollama directement (README.md généré par LLM)  ─┘
                                                                   │
                                                    doc_publisher.py
                                                           │
                                                   docs/index.html
                                                   (site multi-onglets)
                                                           │
                                                    git push → GitHub Pages
```

### `doc_generator.py`

| Langage | Outil primaire | Fallback LLM |
|---------|---------------|--------------|
| Java    | `javadoc`     | Ollama si erreur ou commentaires absents |
| Python  | `pydoc -w`    | Ollama si aucun docstring détecté |
| Lua     | _(aucun)_     | Ollama systématiquement |

Le prompt envoyé à Ollama contient jusqu'à **6 000 caractères** du code source et demande un README structuré en 5 sections :
- Description générale
- Fonctionnalités
- Contrôles / utilisation
- Architecture du code
- Dépendances

### `doc_publisher.py`

1. Scanne tous les dossiers dans `projet/`
2. Détecte le langage dominant (`.java` / `.py` / `.lua`)
3. Génère des **cartes HTML** pour chaque jeu avec liens vers leur doc
4. Assemble `docs/index.html` — site à onglets, style arcade
5. Lance :
   ```
   git add docs/
   git commit -m "docs: mise à jour [timestamp]"
   git push
   ```
   → Publication automatique sur **GitHub Pages**

### Capture d'écran — Site de documentation

![Site GitHub Pages généré automatiquement](docs/screenshots/doc_site.png)

> _Remplacer par une capture de `https://<user>.github.io/<repo>`_

---

## Mise à jour automatique

### Pipeline

```
requirements.txt (tous les jeux Python)
        │
        ▼
  PyPI JSON API
  pypi.org/pypi/<pkg>/json
        │
        ▼
  Versions disponibles comparées aux versions installées
        │
   ┌────┴────────────────────┐
   │ Mise à jour disponible? │
   └────┬────────────────────┘
        │ OUI
        ▼
  Git snapshot (commit de sauvegarde)
        │
        ▼
  pip install <pkg>==<nouvelle_version>
        │
   ┌────┴────────────────────────────┐
   │ Succès ?                        │
   └────┬──────────────────┬─────────┘
        │ OUI              │ NON
        ▼                  ▼
  _patch_requirements()  git_rollback()
  (màj du fichier)       (revert --no-edit HEAD)
        │
        ▼
  Ollama analyse de compatibilité
  (si conflit détecté entre paquets)
```

### `update_checker.py` — fonctions clés

| Fonction | Rôle |
|----------|------|
| `check_updates()` | Lit tous les `requirements.txt`, interroge l'API PyPI |
| `apply_update(pkg, version)` | Crée snapshot Git → `pip install` → patch fichier |
| `_patch_requirements(path, pkg, version)` | Écrit la nouvelle version dans le fichier |
| `git_rollback()` | `git revert --no-edit HEAD` en cas d'échec |

### Analyse des incompatibilités par Ollama

Quand une mise à jour provoque un conflit, le contenu du `requirements.txt` et les erreurs pip sont envoyés au LLM local (`qwen3:8b` sur `http://10.22.28.190:11434`). Ollama produit un rapport lisible expliquant le conflit et proposant une résolution.

### Capture d'écran — Onglet mises à jour

![Onglet mises à jour du panneau admin](docs/screenshots/updates_tab.png)

> _Remplacer par une capture de l'onglet Updates du panneau admin_

---

## Panneau d'administration

Interface **Pygame sans souris**, navigable uniquement au clavier (conçu pour la borne arcade).

### Onglets

| Onglet | Touche | Contenu |
|--------|--------|---------|
| Jeux   | `1`    | Liste des jeux détectés, statut, lancement |
| Mises à jour | `2` | Paquets Python outdated, appliquer/refuser |
| Rapports | `3`  | Générer doc, publier, voir logs |

### Tâches en arrière-plan

Les opérations longues (génération doc, pip install, git push…) tournent dans des **sous-processus séparés** via `admin/workers/run_task.py`. Le statut est écrit dans des fichiers JSON dans `admin/workers/status/` et lu en temps réel par l'interface.

```
admin/workers/status/
├── doc_gen.json       # {"status": "running"|"done"|"error", "log": "..."}
├── doc_pub.json
└── update_<pkg>.json
```

### Capture d'écran — Panneau admin

![Panneau d'administration](docs/screenshots/admin_panel.png)

> _Remplacer par une capture de l'interface admin en fonctionnement_

---

## Schéma global

```
┌──────────────────────────────────────────────────────┐
│                  Panneau Admin (Pygame)               │
│                                                      │
│  [Onglet Jeux]  [Onglet MàJ]  [Onglet Rapports]     │
└────────────┬──────────────┬───────────────┬──────────┘
             │              │               │
             ▼              ▼               ▼
       game_scanner   update_checker   doc_generator
             │              │               │
             │         PyPI API        javadoc/pydoc
             │              │               │
             │         git_manager     ollama_client
             │         (snapshot/      (qwen3:8b)
             │          rollback)           │
             │                             ▼
             │                       doc_publisher
             │                             │
             └─────────────────────────────▼
                                    GitHub Pages
                                  docs/index.html
```

---

## Modèle LLM utilisé

- **Serveur** : Ollama local — `http://10.22.28.190:11434`
- **Modèle** : `qwen3:8b`
- **Usages** :
  - Génération de README pour les jeux (Lua systématiquement, Java/Python en fallback)
  - Analyse de compatibilité lors des mises à jour en échec
