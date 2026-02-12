#!/bin/bash

# Script d'installation automatique pour la borne d'arcade
# Usage: curl -sSL https://raw.githubusercontent.com/nonov1012/maintenance_borne-arcade/main/install_borne.sh | bash

set -e  # Arrêter en cas d'erreur

echo "=========================================="
echo "Installation de la borne d'arcade"
echo "=========================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si on est sur un système 64-bit
info "Vérification de l'architecture..."
ARCH=$(dpkg --print-architecture)
if [ "$ARCH" != "amd64" ] && [ "$ARCH" != "arm64" ]; then
    warn "Architecture 32-bit détectée ($ARCH). Certains jeux (CursedWare, PianoTile) ne fonctionneront pas."
    warn "Il est recommandé d'utiliser Raspberry Pi OS 64-bit."
    read -p "Continuer quand même ? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Mise à jour du système
info "Mise à jour du système..."
sudo apt-get update
sudo apt-get upgrade -y

# Installation des dépendances de base
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

# Installation des dépendances Python scientifiques (pour les jeux Python)
info "Installation des dépendances Python..."
sudo apt-get install -y \
    python3-numpy \
    python3-scipy \
    python3-sklearn \
    python3-joblib

# Installation de MG2D
info "Installation de MG2D..."
cd ~
if [ -d "MG2D" ]; then
    warn "MG2D existe déjà, mise à jour..."
else
    mkdir -p git/MG2D
    cd git/MG2D
    git clone https://github.com/synave/MG2D.git
    mv MG2D/ ../../MG2D
fi

# Compilation de MG2D
info "Compilation de MG2D..."
cd ~/MG2D
javac *.java

# Ajout du classpath dans .bashrc si pas déjà présent
info "Configuration du classpath..."
if ! grep -q "export CLASSPATH=$CLASSPATH:.:~" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Classpath pour MG2D" >> ~/.bashrc
    echo "export CLASSPATH=$CLASSPATH:.:~" >> ~/.bashrc
    info "Classpath ajouté à ~/.bashrc"
else
    info "Classpath déjà configuré dans ~/.bashrc"
fi

# Charger le nouveau classpath
export export CLASSPATH=$CLASSPATH:.:~

# Installation du programme de la borne
info "Installation du programme de la borne..."
cd ~
if [ -d "borne_arcade" ]; then
    warn "borne_arcade existe déjà, mise à jour..."
    cd borne_arcade
    git pull
else
    git clone https://github.com/nonov1012/maintenance_borne-arcade.git borne_arcade
    cd borne_arcade
fi

# Rendre tous les scripts .sh exécutables
info "Configuration des permissions..."
chmod +x *.sh

# Compilation de tous les jeux Java
info "Compilation des jeux Java..."
bash compilation.sh

# Installation des dépendances Python pour les jeux spécifiques
info "Installation des dépendances Python pour les jeux..."

# Vérifier si on est en 64-bit pour installer librosa
if [ "$ARCH" = "amd64" ] || [ "$ARCH" = "arm64" ]; then
    info "Installation de librosa pour PianoTile (peut prendre quelques minutes)..."
    pip3 install librosa --user || warn "Échec de l'installation de librosa. PianoTile ne fonctionnera pas."
else
    warn "Architecture 32-bit: librosa ne sera pas installé. PianoTile ne fonctionnera pas."
fi

# Vérifier que tous les fichiers nécessaires existent
info "Vérification de l'installation..."
MISSING_FILES=0

if [ ! -f "Main.java" ]; then
    error "Main.java manquant!"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ ! -d "projet" ]; then
    error "Dossier projet/ manquant!"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ ! -d ~/MG2D ]; then
    error "MG2D non installé!"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ $MISSING_FILES -eq 0 ]; then
    info "Tous les fichiers nécessaires sont présents."
else
    error "$MISSING_FILES fichier(s) manquant(s)!"
    exit 1
fi

# Compilation du launcher
info "Compilation du launcher principal..."
cd ~/borne_arcade
javac -cp .:~/MG2D *.java

echo ""
echo "=========================================="
echo -e "${GREEN}Installation terminée !${NC}"
echo "=========================================="
echo ""
echo "Pour lancer la borne d'arcade :"
echo "  cd ~/borne_arcade"
echo "  java -cp .:~/MG2D Main"
echo ""
echo "Notes importantes :"
if [ "$ARCH" != "amd64" ] && [ "$ARCH" != "arm64" ]; then
    echo "  - Architecture 32-bit détectée"
    echo "  - CursedWare ne fonctionnera pas (bug LÖVE sur 32-bit)"
    echo "  - PianoTile ne fonctionnera pas (librosa nécessite 64-bit)"
    echo "  - Les jeux Java fonctionneront normalement"
    echo ""
    echo "  Pour résoudre ces problèmes, installez Raspberry Pi OS 64-bit"
else
    echo "  - Tous les jeux devraient fonctionner correctement"
fi
echo ""
echo "  N'oubliez pas de sourcer votre .bashrc :"
echo "  source ~/.bashrc"
echo ""
echo "=========================================="

