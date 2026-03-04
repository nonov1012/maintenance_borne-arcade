#!/bin/bash

# Script d'installation automatique pour la borne d'arcade
# Usage: curl -sSL https://raw.githubusercontent.com/nonov1012/maintenance_borne-arcade/main/install_borne.sh | bash

set -euo pipefail  # Arrêter en cas d'erreur, variable non définie, ou erreur dans un pipe

echo "=========================================="
echo "Installation de la borne d'arcade"
echo "=========================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Prérequis ───────────────────────────────────────────────────────────────

# Vérifier que dpkg est disponible (système Debian/Ubuntu/Raspberry Pi OS)
if ! command -v dpkg &>/dev/null; then
    error "dpkg introuvable. Ce script est réservé aux systèmes Debian/Ubuntu/Raspberry Pi OS."
    exit 1
fi

# Vérifier que sudo est disponible
if ! command -v sudo &>/dev/null; then
    error "sudo est introuvable. Installez-le ou lancez le script en tant que root."
    exit 1
fi

# ─── Architecture ────────────────────────────────────────────────────────────

info "Vérification de l'architecture..."
ARCH=$(dpkg --print-architecture)
IS_64BIT=false
if [ "$ARCH" = "amd64" ] || [ "$ARCH" = "arm64" ]; then
    IS_64BIT=true
    info "Architecture 64-bit détectée ($ARCH). Tous les jeux sont supportés."
else
    warn "Architecture 32-bit détectée ($ARCH)."
    warn "CursedWare (LÖVE) et PianoTile (librosa) ne fonctionneront pas."
    warn "Il est recommandé d'utiliser Raspberry Pi OS 64-bit."
    read -rp "Continuer quand même ? (y/N) " REPLY
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ─── Mise à jour du système ───────────────────────────────────────────────────

info "Mise à jour du système..."
sudo apt-get update -q
sudo apt-get upgrade -y -q

# ─── Dépendances système ──────────────────────────────────────────────────────

info "Installation des dépendances de base..."
sudo apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    default-jdk \
    python3 \
    python3-pip \
    python3-pygame \
    xdotool \
    love

info "Installation des dépendances Python scientifiques..."
sudo apt-get install -y \
    python3-numpy \
    python3-scipy \
    python3-sklearn \
    python3-joblib

# ─── Installation de MG2D ─────────────────────────────────────────────────────

MG2D_DIR="$HOME/MG2D"
MG2D_TMP=$(mktemp -d)

info "Installation/mise à jour de MG2D dans $MG2D_DIR..."
if [ -d "$MG2D_DIR" ]; then
    warn "MG2D existe déjà"
else 
    # On clone toujours dans un dossier temporaire, puis on déplace le
    # sous-dossier MG2D/ (contenu du repo, pas le repo lui-même)
    git clone https://github.com/synave/MG2D.git "$MG2D_TMP"
    rm -rf "$MG2D_DIR"
    mv "$MG2D_TMP/MG2D/" "$MG2D_DIR"
    rm -rf "$MG2D_TMP"
fi


# ─── Configuration du CLASSPATH ──────────────────────────────────────────────

info "Configuration du CLASSPATH..."
# On écrit la variable littérale (non expansée) dans .bashrc
# afin qu'elle soit résolue correctement à chaque ouverture de shell.
CLASSPATH_LINE='export CLASSPATH=$CLASSPATH:.:$HOME/MG2D'
if grep -qF "$CLASSPATH_LINE" "$HOME/.bashrc"; then
    info "CLASSPATH déjà configuré dans ~/.bashrc"
else
    {
        echo ""
        echo "# Classpath pour MG2D (ajouté par install_borne.sh)"
        echo "$CLASSPATH_LINE"
    } >> "$HOME/.bashrc"
    info "CLASSPATH ajouté à ~/.bashrc"
fi
# Appliquer pour la session courante
export CLASSPATH="${CLASSPATH:+$CLASSPATH:}.:$HOME/MG2D"

# ─── Compilation de MG2D ─────────────────────────────────────────────────────

info "Compilation de MG2D..."
cd $HOME
javac ./MG2D/*.java

# ─── Installation de la borne d'arcade ───────────────────────────────────────

BORNE_DIR="$HOME/borne_arcade"

info "Installation du programme de la borne dans $BORNE_DIR..."
if [ -d "$BORNE_DIR/.git" ]; then
    warn "borne_arcade existe déjà, mise à jour..."
    git -C "$BORNE_DIR" pull
else
    git clone https://github.com/nonov1012/maintenance_borne-arcade.git "$BORNE_DIR"
fi

cd "$BORNE_DIR"

info "Configuration des permissions des scripts..."
chmod +x ./*.sh

# ─── Installation du layout clavier XKB ──────────────────────────────────────

info "Installation du layout clavier XKB..."
sudo cp "$BORNE_DIR/borne" /usr/share/X11/xkb/symbols/borne

info "Compilation des jeux Java..."
bash compilation.sh

# ─── Dépendances Python spécifiques aux jeux ─────────────────────────────────

if [ "$IS_64BIT" = true ]; then
    info "Installation de librosa pour PianoTile (peut prendre quelques minutes)..."
    # --break-system-packages est requis sur Debian Bookworm+ (PEP 668)
    pip3 install librosa --user --break-system-packages \
        || warn "Échec de l'installation de librosa. PianoTile ne fonctionnera pas."
else
    warn "Architecture 32-bit : librosa ne sera pas installé. PianoTile ne fonctionnera pas."
fi

# ─── Vérification de l'installation ──────────────────────────────────────────

info "Vérification de l'installation..."
MISSING=0

check_file() {
    if [ ! -e "$1" ]; then
        error "Manquant : $1"
        MISSING=$((MISSING + 1))
    fi
}

check_file "$BORNE_DIR/Main.java"
check_file "$BORNE_DIR/projet"
check_file "$MG2D_DIR"

if [ "$MISSING" -gt 0 ]; then
    error "$MISSING élément(s) manquant(s). Vérifiez les erreurs ci-dessus."
    exit 1
fi

info "Tous les fichiers nécessaires sont présents."

# ─── Configuration GitHub Pages (documentation en ligne) ─────────────────────

echo ""
info "Configuration optionnelle : publication automatique de la doc sur GitHub Pages"
echo ""
echo "  URL cible : https://nonov1012.github.io/maintenance_borne-arcade/"
echo ""
echo "  Prérequis : un Personal Access Token (PAT) GitHub avec le scope 'repo'"
echo "  Créer sur : github.com → Settings → Developer settings → Personal access tokens"
echo ""
# Lire depuis /dev/tty pour fonctionner même si stdin est un pipe (curl | bash)
GITHUB_PAT=""
read -rsp "  GitHub PAT (Entrée pour ignorer) : " GITHUB_PAT < /dev/tty
echo ""

if [ -n "$GITHUB_PAT" ]; then
    # Extraire le nom d'utilisateur depuis l'URL du remote
    GITHUB_USER=$(git -C "$BORNE_DIR" remote get-url origin \
        | sed 's|https://github.com/\([^/]*\)/.*|\1|')

    # Configurer credential.helper store
    git config --global credential.helper store

    # Écrire les credentials dans ~/.git-credentials (format standard)
    touch ~/.git-credentials
    chmod 600 ~/.git-credentials
    # Supprimer l'entrée github.com existante et réécrire proprement
    grep -v "@github.com" ~/.git-credentials > /tmp/.git-creds-tmp 2>/dev/null || true
    echo "https://${GITHUB_USER}:${GITHUB_PAT}@github.com" >> /tmp/.git-creds-tmp
    mv /tmp/.git-creds-tmp ~/.git-credentials

    # Activer github_pages dans admin/config.json
    if [ -f "$BORNE_DIR/admin/config.json" ]; then
        python3 - << PYEOF
import json
path = "$BORNE_DIR/admin/config.json"
cfg = json.loads(open(path).read())
cfg["github_pages"] = True
open(path, "w").write(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
PYEOF
        info "github_pages activé dans admin/config.json"
    fi

    # Commit initial du dossier docs/ et push
    git -C "$BORNE_DIR" add docs/
    git -C "$BORNE_DIR" commit -m "init: dossier docs/ pour GitHub Pages" \
        2>/dev/null || true   # rien à commiter si déjà présent
    git -C "$BORNE_DIR" push \
        && info "docs/ poussé sur GitHub" \
        || warn "Push initial échoué — vérifiez que le PAT a le scope 'repo'"

    echo ""
    info "PAT configuré. La doc sera publiée automatiquement après chaque génération."
    info "Dernière étape manuelle sur github.com :"
    info "  Repository > Settings > Pages > Source : branche 'main', dossier '/docs'"
    info "  URL : https://${GITHUB_USER}.github.io/maintenance_borne-arcade/"
else
    warn "PAT non renseigné — publication automatique désactivée."
    warn "Configurable plus tard : admin/config.json → github_pages: true"
    warn "  + git config --global credential.helper store  +  git push (saisir PAT)"
fi

# ─── Start auto ───────────────────────────────────────────────────────────────

info "lancement automatique de la borne au démarrage"
mv borne.desktop ~/.config/autostart/

# ─── Remapping des touches ───────────────────────────────────────────────────────────────

info "Configuration des bouton de la borne"
sudo cp ~/borne_arcade/borne /usr/share/X11/xkb/symbols/borne

# ─── Résumé ───────────────────────────────────────────────────────────────────

echo ""
echo "=========================================="
echo -e "${GREEN}Installation terminée avec succès !${NC}"
echo "=========================================="
echo ""
echo "Pour lancer la borne d'arcade :"
echo ""
echo "  cd ~/borne_arcade"
echo "  java -cp .:~/MG2D Main"
echo ""
echo "Notes :"
if [ "$IS_64BIT" = false ]; then
    echo "  ⚠  Architecture 32-bit détectée ($ARCH)"
    echo "     - CursedWare ne fonctionnera pas (bug LÖVE sur 32-bit)"
    echo "     - PianoTile ne fonctionnera pas (librosa nécessite 64-bit)"
    echo "     - Les jeux Java fonctionneront normalement"
    echo "     → Pour résoudre ces problèmes, installez Raspberry Pi OS 64-bit"
else
    echo "  ✓  Tous les jeux devraient fonctionner correctement"
fi
echo ""
echo "  N'oubliez pas d'appliquer le nouveau CLASSPATH :"
echo "  source ~/.bashrc"
echo ""
echo "=========================================="

# ─── Compilation du launcher principal ───────────────────────────────────────

echo -e "${GREEN}Lancement de la borne"
echo "=========================================="

./lancerBorne.sh
