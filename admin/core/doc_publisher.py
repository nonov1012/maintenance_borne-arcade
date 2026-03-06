"""
Publication des docs générées sur GitHub Pages.

Après une génération réussie :
  - Copie la doc dans docs/<jeu>/ (HTML API ou README.md Ollama)
  - Régénère docs/index.html
  - git add docs/ → commit → push

L'IA ne touche jamais au code source.
"""
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

ADMIN_DIR = Path(__file__).parent.parent
REPO_ROOT  = ADMIN_DIR.parent
DOCS_DIR   = REPO_ROOT / "docs"


# ---------------------------------------------------------------------------
# Helpers index
# ---------------------------------------------------------------------------

def _detect_language(game_dir: Path) -> str:
    if list(game_dir.glob("*.java")):
        return "java"
    if list(game_dir.glob("*.py")):
        return "python"
    if list(game_dir.glob("*.lua")):
        return "lua"
    return "?"


def _build_game_cards() -> str:
    projet_dir = REPO_ROOT / "projet"
    if not projet_dir.exists():
        return "<p>Dossier projet introuvable.</p>"

    games = sorted(d for d in projet_dir.iterdir() if d.is_dir() and not d.name.startswith("."))
    cards = []
    for g in games:
        name  = g.name
        lang  = _detect_language(g)
        has_api    = (DOCS_DIR / name / "api" / "index.html").exists()
        has_readme = (DOCS_DIR / name / "README.md").exists()

        badge_cls = {"java": "badge-java", "python": "badge-py", "lua": "badge-lua"}.get(lang, "badge-unk")
        badge_lbl = {"java": "Java", "python": "Python", "lua": "Lua"}.get(lang, "?")

        links = []
        if has_api:
            links.append(f'<a href="{name}/api/index.html" class="cbtn cbtn-api">Javadoc</a>')
        if has_readme:
            links.append(f'<a href="{name}/README.md" class="cbtn cbtn-readme">README</a>')
        links_html = "".join(links) if links else '<span class="nodoc">Pas encore de doc</span>'

        cards.append(
            f'<div class="card{"" if (has_api or has_readme) else " card-dim"}">'
            f'<div class="card-head"><span class="badge {badge_cls}">{badge_lbl}</span>'
            f'<span class="card-name">{name}</span></div>'
            f'<div class="card-links">{links_html}</div></div>'
        )
    return "\n".join(cards)


# ---------------------------------------------------------------------------
# Index HTML principal
# ---------------------------------------------------------------------------

def regenerate_index() -> None:
    """Génère docs/index.html — site multi-onglets (Accueil / Install / Jeux / Borne / Ajouter)."""
    DOCS_DIR.mkdir(exist_ok=True)

    game_cards   = _build_game_cards()
    borne_api_ok = (DOCS_DIR / "borne" / "api" / "index.html").exists()
    borne_block  = (
        '<a href="borne/api/index.html" class="big-link">Ouvrir la Javadoc de la borne</a>'
        if borne_api_ok else
        '<div class="info-box">Documentation non encore générée.<br>'
        'Lancez la génération depuis le panneau admin (onglet Jeux → bouton G).</div>'
    )
    now = datetime.now().strftime("%Y-%m-%d à %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Borne Arcade — Documentation</title>
  <style>
    :root {{
      --bg:      #0a0e1a;
      --bg2:     #111827;
      --bg3:     #1a2540;
      --accent:  #00bfff;
      --accent2: #7c3aed;
      --text:    #e2e8f0;
      --muted:   #8899aa;
      --border:  #1e3a5f;
      --java:    #f97316;
      --py:      #3b82f6;
      --lua:     #a855f7;
      --unk:     #6b7280;
      --radius:  10px;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}

    /* ── Header ── */
    header {{
      background: linear-gradient(135deg, #0d1b35 0%, #0a0e1a 100%);
      border-bottom: 2px solid var(--accent);
      padding: 2rem 2rem 1.5rem;
      box-shadow: 0 4px 24px #00bfff22;
    }}
    header h1 {{
      font-size: 1.9rem;
      color: var(--accent);
      letter-spacing: .04em;
      text-shadow: 0 0 18px #00bfff66;
    }}
    header p {{ color: var(--muted); margin-top: .4rem; font-size: .95rem; }}

    /* ── Nav tabs ── */
    nav {{
      display: flex;
      gap: .4rem;
      padding: 1rem 2rem 0;
      background: var(--bg2);
      border-bottom: 1px solid var(--border);
      overflow-x: auto;
    }}
    nav button {{
      background: none;
      border: none;
      border-bottom: 3px solid transparent;
      color: var(--muted);
      cursor: pointer;
      font-size: .9rem;
      padding: .65rem 1.1rem;
      white-space: nowrap;
      transition: color .15s, border-color .15s;
    }}
    nav button:hover  {{ color: var(--text); }}
    nav button.active {{ color: var(--accent); border-color: var(--accent); }}

    /* ── Content ── */
    main {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
    .tab {{ display: none; }}
    .tab.active {{ display: block; }}

    h2 {{ font-size: 1.35rem; color: var(--accent); margin-bottom: 1.2rem; }}
    h3 {{ font-size: 1.05rem; color: var(--text); margin: 1.4rem 0 .6rem; }}
    p, li {{ line-height: 1.7; color: #c8d8e8; }}
    ul {{ padding-left: 1.5rem; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* ── Accueil ── */
    .hero {{
      background: var(--bg3);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 2rem;
      margin-bottom: 2rem;
    }}
    .hero h2 {{ margin-bottom: .7rem; }}
    .stack-list {{
      display: flex; flex-wrap: wrap; gap: .6rem; margin-top: 1rem;
    }}
    .stack-pill {{
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: .3rem .9rem;
      font-size: .85rem;
      color: var(--muted);
    }}
    .quick-links {{ display: flex; gap: 1rem; margin-top: 1.5rem; flex-wrap: wrap; }}
    .ql {{ background: var(--accent); color: #000; border-radius: 6px; padding: .55rem 1.2rem;
           font-weight: 600; font-size: .9rem; cursor: pointer; border: none; }}
    .ql:hover {{ opacity: .85; }}

    /* ── Install / Add-game ── */
    .step {{
      background: var(--bg3);
      border-left: 3px solid var(--accent);
      border-radius: 0 var(--radius) var(--radius) 0;
      padding: 1rem 1.4rem;
      margin-bottom: 1rem;
    }}
    .step-num {{
      display: inline-block; background: var(--accent); color: #000;
      border-radius: 50%; width: 1.5rem; height: 1.5rem;
      line-height: 1.5rem; text-align: center; font-weight: 700;
      font-size: .8rem; margin-right: .7rem;
    }}
    pre {{
      background: #060a14;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem 1.2rem;
      font-size: .85rem;
      overflow-x: auto;
      margin: .6rem 0;
      color: #7dd3fc;
    }}
    .info-box {{
      background: #0c1c30;
      border: 1px solid #1e4a7f;
      border-radius: var(--radius);
      padding: 1rem 1.4rem;
      color: var(--muted);
      margin: 1rem 0;
    }}
    .warn-box {{
      background: #1a1000;
      border: 1px solid #f97316;
      border-radius: var(--radius);
      padding: 1rem 1.4rem;
      color: #fdba74;
      margin: 1rem 0;
    }}
    table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
    th {{ background: var(--bg3); color: var(--accent); font-size: .85rem;
          text-align: left; padding: .6rem 1rem; border-bottom: 1px solid var(--border); }}
    td {{ padding: .55rem 1rem; border-bottom: 1px solid #1a2a40; font-size: .9rem; color: #c8d8e8; }}
    code {{ background: #111827; color: #7dd3fc; padding: .1em .4em;
            border-radius: 4px; font-size: .88em; }}

    /* ── Borne ── */
    .big-link {{
      display: inline-block;
      background: var(--accent);
      color: #000;
      font-weight: 700;
      padding: .8rem 2rem;
      border-radius: var(--radius);
      font-size: 1rem;
      margin: 1rem 0;
    }}

    /* ── Game cards ── */
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1rem;
    }}
    .card {{
      background: var(--bg3);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1rem;
      transition: border-color .15s, transform .1s;
    }}
    .card:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
    .card-dim {{ opacity: .5; }}
    .card-head {{
      display: flex; align-items: center; gap: .6rem; margin-bottom: .9rem;
    }}
    .card-name {{ font-weight: 600; font-size: .95rem; color: var(--text); }}
    .badge {{
      border-radius: 4px; padding: .15rem .5rem;
      font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em;
    }}
    .badge-java {{ background: #7c2d12; color: #fdba74; }}
    .badge-py   {{ background: #1e3a8a; color: #93c5fd; }}
    .badge-lua  {{ background: #4c1d95; color: #c4b5fd; }}
    .badge-unk  {{ background: #1f2937; color: #9ca3af; }}
    .card-links {{ display: flex; gap: .5rem; flex-wrap: wrap; }}
    .cbtn {{
      font-size: .78rem; padding: .3rem .75rem;
      border-radius: 5px; font-weight: 600; white-space: nowrap;
    }}
    .cbtn-api    {{ background: #0c2a45; color: #38bdf8; border: 1px solid #1e4a7f; }}
    .cbtn-readme {{ background: #1a0c45; color: #a78bfa; border: 1px solid #3b1f7f; }}
    .cbtn:hover  {{ opacity: .8; }}
    .nodoc {{ font-size: .78rem; color: #4b5563; }}

    /* ── Footer ── */
    footer {{
      text-align: center; padding: 2rem;
      color: #374151; font-size: .8rem;
      border-top: 1px solid var(--border);
      margin-top: 3rem;
    }}
  </style>
</head>
<body>

<header>
  <h1>&#9679; Borne Arcade</h1>
  <p>Documentation technique — {now}</p>
</header>

<nav>
  <button class="active" onclick="tab(this,'accueil')">Accueil</button>
  <button onclick="tab(this,'install')">Installation</button>
  <button onclick="tab(this,'add')">Ajouter un jeu</button>
  <button onclick="tab(this,'borne')">Borne</button>
  <button onclick="tab(this,'games')">Jeux</button>
  <button onclick="tab(this,'admin')">Maintenance</button>
</nav>

<main>

<!-- ═══════════════════════════════════════ ACCUEIL ═══════════════ -->
<div id="tab-accueil" class="tab active">
  <div class="hero">
    <h2>Borne d'arcade multi-jeux</h2>
    <p>
      Système d'arcade complet tournant sur <strong>Raspberry Pi</strong> (ou PC Linux), proposant
      une sélection de jeux développés en Java, Python et Lua, navigable au joystick et aux boutons.
      Un panneau d'administration intégré permet de gérer les jeux, surveiller les dépendances
      et générer cette documentation automatiquement.
    </p>
    <div class="stack-list">
      <span class="stack-pill">Java 11+</span>
      <span class="stack-pill">MG2D</span>
      <span class="stack-pill">Python 3</span>
      <span class="stack-pill">Pygame</span>
      <span class="stack-pill">LÖVE (Lua)</span>
      <span class="stack-pill">Raspberry Pi OS 64-bit</span>
      <span class="stack-pill">Pygame Admin</span>
    </div>
    <div class="quick-links">
      <button class="ql" onclick="tab(document.querySelector('nav button:nth-child(2)'),'install')">Guide d'installation</button>
      <button class="ql" onclick="tab(document.querySelector('nav button:nth-child(5)'),'games')">Voir les jeux</button>
    </div>
  </div>

  <h3>Architecture générale</h3>
  <table>
    <tr><th>Composant</th><th>Description</th></tr>
    <tr><td><code>Main.java</code></td><td>Launcher principal — menu de sélection des jeux, navigation joystick</td></tr>
    <tr><td><code>projet/</code></td><td>Chaque sous-dossier = un jeu indépendant (Java, Python ou Lua)</td></tr>
    <tr><td><code>admin/</code></td><td>Panneau d'administration Pygame (mises à jour, docs, rapports)</td></tr>
    <tr><td><code>MG2D</code></td><td>Bibliothèque graphique Java 2D (fenêtre plein écran, sprites, clavier borne)</td></tr>
    <tr><td><code>docs/</code></td><td>Documentation générée — cette page + Javadoc + README IA par jeu</td></tr>
  </table>

  <h3>Contrôles physiques</h3>
  <table>
    <tr><th>Bouton</th><th>Rôle dans les menus</th></tr>
    <tr><td>Joystick ↑↓</td><td>Naviguer dans la liste des jeux</td></tr>
    <tr><td>R / T / Y (ligne du haut)</td><td>Actions contextuelles (confirmer, retour, quitter)</td></tr>
    <tr><td>F / G / H (ligne du bas)</td><td>Actions contextuelles (admin, action, quitter)</td></tr>
  </table>
</div>

<!-- ═══════════════════════════════════════ INSTALLATION ══════════ -->
<div id="tab-install" class="tab">
  <h2>Guide d'installation</h2>

  <div class="step">
    <span class="step-num">1</span><strong>Prérequis</strong>
    <ul style="margin-top:.6rem">
      <li>Raspberry Pi OS 64-bit (recommandé) ou Debian/Ubuntu amd64</li>
      <li>Connexion Internet active</li>
      <li>Compte avec accès <code>sudo</code></li>
    </ul>
  </div>

  <div class="step">
    <span class="step-num">2</span><strong>Lancer l'installation automatique</strong>
    <pre>curl -sSL https://raw.githubusercontent.com/nonov1012/maintenance_borne-arcade/main/install_borne.sh | tr -d '\\r' | bash</pre>
    <p>Le script installe automatiquement toutes les dépendances, compile les jeux Java,
       configure le CLASSPATH et active le lancement automatique au démarrage.</p>
  </div>

  <div class="step">
    <span class="step-num">3</span><strong>Ce qui est installé</strong>
    <table>
      <tr><th>Paquet</th><th>Usage</th></tr>
      <tr><td><code>default-jdk</code></td><td>Compilation et exécution des jeux Java</td></tr>
      <tr><td><code>python3 + pip + pygame</code></td><td>Jeux Python + panneau admin</td></tr>
      <tr><td><code>love</code></td><td>Runtime LÖVE pour les jeux Lua</td></tr>
      <tr><td><code>xdotool</code></td><td>Gestion fenêtre plein écran</td></tr>
      <tr><td><code>MG2D</code></td><td>Bibliothèque graphique Java (extraite dans <code>~/MG2D</code>)</td></tr>
      <tr><td>Dépôt borne</td><td>Cloné dans <code>~/borne_arcade</code></td></tr>
    </table>
  </div>

  <div class="step">
    <span class="step-num">4</span><strong>Après l'installation</strong>
    <pre>source ~/.bashrc          # Appliquer le CLASSPATH MG2D
cd ~/borne_arcade
java -cp .:~/MG2D Main   # Lancer manuellement</pre>
    <p>Le lancement automatique au démarrage est configuré via <code>~/.config/autostart/borne</code>.</p>
  </div>

  <div class="warn-box">
    &#9888; Sur architecture 32-bit, CursedWare (LÖVE) et PianoTile (librosa) ne fonctionneront pas.
    Utilisez Raspberry Pi OS 64-bit pour une compatibilité complète.
  </div>
</div>

<!-- ═══════════════════════════════════════ AJOUTER UN JEU ════════ -->
<div id="tab-add" class="tab">
  <h2>Ajouter un jeu</h2>

  <p>Chaque jeu est un dossier autonome dans <code>projet/</code>. Le launcher Java le détecte
     automatiquement s'il respecte la structure ci-dessous.</p>

  <h3>Structure minimale</h3>
  <pre>projet/
  MonJeu/
    &#x251C;&#x2500; *.java / *.py / *.lua   ← code source
    &#x251C;&#x2500; bouton.txt              ← layout des touches (obligatoire)
    &#x2514;&#x2500; requirements.txt        ← dépendances Python (si Python)</pre>

  <h3>Fichier <code>bouton.txt</code></h3>
  <p>Décrit les actions de chaque bouton physique de la borne, affiché dans le menu de sélection :</p>
  <pre>R: Sauter
T: Tirer
Y: Pause
F: Gauche
G: Droite
H: Quitter</pre>

  <h3>Jeu Java</h3>
  <div class="step">
    <span class="step-num">1</span>Créer <code>projet/MonJeu/Main.java</code> avec une méthode <code>main(String[] args)</code>
  </div>
  <div class="step">
    <span class="step-num">2</span>Importer MG2D : <code>import mg2d.*;</code> — la lib est dans <code>~/MG2D</code> (CLASSPATH configuré)
  </div>
  <div class="step">
    <span class="step-num">3</span>Ajouter le jeu à <code>compilation.sh</code> pour qu'il soit compilé automatiquement
  </div>

  <h3>Jeu Python</h3>
  <div class="step">
    <span class="step-num">1</span>Créer <code>projet/MonJeu/main.py</code> (point d'entrée)
  </div>
  <div class="step">
    <span class="step-num">2</span>Lister les dépendances dans <code>requirements.txt</code>
  </div>
  <div class="step">
    <span class="step-num">3</span>Le panneau admin installe automatiquement les dépendances et surveille les mises à jour
  </div>

  <h3>Jeu Lua / LÖVE</h3>
  <div class="step">
    <span class="step-num">1</span>Créer <code>projet/MonJeu/main.lua</code> avec la structure LÖVE standard (<code>love.load</code>, <code>love.update</code>, <code>love.draw</code>)
  </div>

  <h3>Générer la documentation</h3>
  <p>Une fois le jeu ajouté, lancez le panneau admin et appuyez sur <code>G</code> (onglet Jeux)
     pour générer automatiquement la Javadoc ou un README via l'IA Ollama.</p>
</div>

<!-- ═══════════════════════════════════════ BORNE ════════════════ -->
<div id="tab-borne" class="tab">
  <h2>Documentation de la borne</h2>
  <p>Javadoc des classes principales du launcher (<code>Main.java</code>, <code>ClavierBorneArcade</code>, etc.).</p>
  {borne_block}

  <h3>Classes principales</h3>
  <table>
    <tr><th>Classe</th><th>Rôle</th></tr>
    <tr><td><code>Main</code></td><td>Launcher — menu de sélection, boucle principale, lancement des jeux</td></tr>
    <tr><td><code>ClavierBorneArcade</code></td><td>Mapping clavier physique de la borne vers les codes jeu</td></tr>
  </table>
</div>

<!-- ═══════════════════════════════════════ JEUX ═════════════════ -->
<div id="tab-games" class="tab">
  <h2>Jeux disponibles</h2>
  <div class="card-grid">
{game_cards}
  </div>
</div>

<!-- ═══════════════════════════════════════ MAINTENANCE ══════════ -->
<div id="tab-admin" class="tab">
  <h2>Panneau d'administration</h2>
  <p>
    Interface de maintenance de la borne, navigable entièrement au <strong>joystick et aux boutons</strong>
    (aucune souris). Lancée depuis le menu principal en appuyant sur <code>F</code>.
    Tourne en plein écran (1280×800) via Pygame.
  </p>

  <h3>Contrôles globaux</h3>
  <table>
    <tr><th>Touche</th><th>Action</th></tr>
    <tr><td><code>←  →</code></td><td>Changer d'onglet</td></tr>
    <tr><td><code>↑  ↓</code></td><td>Naviguer dans la liste</td></tr>
    <tr><td><code>G</code></td><td>Appliquer l'action sur l'élément sélectionné</td></tr>
    <tr><td><code>T</code></td><td>Appliquer l'action sur tous les éléments</td></tr>
    <tr><td><code>F</code></td><td>Ouvrir / confirmer / changer de section</td></tr>
    <tr><td><code>R</code></td><td>Retour / fermer / rafraîchir</td></tr>
    <tr><td><code>H</code></td><td>Quitter le panneau admin (retour au menu principal)</td></tr>
  </table>

  <h3>Onglet Jeux</h3>
  <p>Liste tous les jeux détectés dans <code>projet/</code> avec leur statut de documentation.</p>
  <table>
    <tr><th>Action</th><th>Touche</th><th>Description</th></tr>
    <tr><td>Générer la doc</td><td><code>G</code></td><td>Javadoc (Java), pydoc (Python) ou README via Ollama pour le jeu sélectionné</td></tr>
    <tr><td>Générer tout</td><td><code>T</code></td><td>Lance la génération pour tous les jeux d'un coup</td></tr>
    <tr><td>Rafraîchir</td><td><code>R</code></td><td>Recharge la liste et les statuts depuis le disque</td></tr>
  </table>
  <div class="info-box">
    La génération se fait en arrière-plan (worker subprocess). Le statut se met à jour
    automatiquement toutes les 2 secondes.
  </div>

  <h3>Onglet MAJ (Mises à jour)</h3>
  <p>Deux sections navigables avec <code>F</code> :</p>

  <div class="step">
    <span class="step-num">1</span><strong>Dépôts Git</strong>
    <p style="margin-top:.4rem">
      Affiche le dépôt <code>maintenance-borne-arcade</code> avec son état (à jour / N commits en retard).
      Appuyer sur <code>G</code> pour faire un <code>git pull</code>.
    </p>
  </div>

  <div class="step">
    <span class="step-num">2</span><strong>Dépendances Python</strong>
    <p style="margin-top:.4rem">
      Liste tous les packages pip utilisés par les jeux avec leur version installée et la dernière
      version disponible sur PyPI. Appuyer sur <code>G</code> pour mettre à jour le package sélectionné.
    </p>
    <p style="margin-top:.4rem">Flux d'une mise à jour :</p>
    <pre>pip install pkg==new_version --break-system-packages
→ test import du package
→ py_compile de tous les jeux Python
→ OK  : patch requirements.txt  → statut "done"
→ KO  : analyse Ollama (IA locale) → rapport → pip rollback → statut "incompatible"</pre>
  </div>

  <table>
    <tr><th>Action</th><th>Touche</th><th>Description</th></tr>
    <tr><td>Changer de section</td><td><code>F</code></td><td>Basculer entre Git et Dépendances</td></tr>
    <tr><td>Appliquer</td><td><code>G</code></td><td>Pull git ou mise à jour pip selon la section active</td></tr>
    <tr><td>Vérifier tout</td><td><code>T</code></td><td>Lance une vérification PyPI de toutes les dépendances</td></tr>
    <tr><td>Rafraîchir</td><td><code>R</code></td><td>Recharge les statuts</td></tr>
  </table>

  <h3>Onglet Rapports</h3>
  <p>Liste tous les rapports générés dans <code>admin/reports/</code> (logs javadoc, résultats
     des mises à jour, analyses Ollama, rapports d'incompatibilité).</p>
  <table>
    <tr><th>Action</th><th>Touche</th><th>Description</th></tr>
    <tr><td>Ouvrir</td><td><code>F</code></td><td>Ouvre le rapport sélectionné dans une visionneuse intégrée</td></tr>
    <tr><td>Rafraîchir</td><td><code>R</code></td><td>Recharge la liste / ferme la visionneuse</td></tr>
    <tr><td>Scroller</td><td><code>↑  ↓</code></td><td>Faire défiler le contenu dans la visionneuse</td></tr>
  </table>

  <h3>Architecture technique</h3>
  <table>
    <tr><th>Fichier</th><th>Rôle</th></tr>
    <tr><td><code>admin/main.py</code></td><td>Boucle principale Pygame, gestion des événements, rendu des onglets</td></tr>
    <tr><td><code>admin/ui/games_tab.py</code></td><td>Onglet Jeux — liste + génération de doc</td></tr>
    <tr><td><code>admin/ui/updates_tab.py</code></td><td>Onglet MAJ — git + dépendances pip</td></tr>
    <tr><td><code>admin/ui/reports_tab.py</code></td><td>Onglet Rapports — liste + visionneuse</td></tr>
    <tr><td><code>admin/workers/run_task.py</code></td><td>Worker subprocess — exécute les tâches longues en arrière-plan</td></tr>
    <tr><td><code>admin/core/game_scanner.py</code></td><td>Détection automatique des jeux dans <code>projet/</code></td></tr>
    <tr><td><code>admin/core/doc_generator.py</code></td><td>Génération Javadoc / pydoc / Ollama README</td></tr>
    <tr><td><code>admin/core/update_checker.py</code></td><td>Vérification PyPI, patch <code>requirements.txt</code></td></tr>
    <tr><td><code>admin/core/compat_tester.py</code></td><td>Test de compatibilité des jeux après mise à jour pip</td></tr>
    <tr><td><code>admin/core/ollama_client.py</code></td><td>Client HTTP pour l'IA Ollama locale (analyse d'erreurs)</td></tr>
    <tr><td><code>admin/core/doc_publisher.py</code></td><td>Génération de <code>docs/index.html</code> + git push GitHub Pages</td></tr>
    <tr><td><code>admin/workers/status/</code></td><td>Fichiers JSON de statut des tâches en cours (mis à jour par les workers)</td></tr>
  </table>

  <h3>Ollama (IA locale)</h3>
  <p>Le panneau utilise un serveur Ollama local pour deux usages :</p>
  <ul>
    <li><strong>Génération de README</strong> — quand javadoc ou pydoc est insuffisant</li>
    <li><strong>Analyse d'incompatibilité</strong> — quand une mise à jour pip casse un jeu</li>
  </ul>
  <div class="info-box">
    Configurable dans <code>admin/config.json</code> :<br>
    <code>"ollama_url": "http://10.22.28.190:11434"</code><br>
    <code>"ollama_model": "qwen3:8b"</code>
  </div>
</div>

</main>

<footer>Générée automatiquement le {now}</footer>

<script>
function tab(btn, id) {{
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  var el = document.getElementById('tab-' + id);
  if (el) el.classList.add('active');
}}
</script>

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
