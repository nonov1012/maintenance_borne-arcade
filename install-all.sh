sudo apt update
sudo apt upgrade -y

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


# MG2D
MG2D_DIR="$HOME/MG2D"
MG2D_TMP=$(mktemp -d)

if [ -d "$MG2D_DIR" ]; then
    echo "MG2D existe déjà"
else 
    git clone https://github.com/synave/MG2D.git "$MG2D_TMP"
    rm -rf "$MG2D_DIR"
    mv "$MG2D_TMP/MG2D/" "$MG2D_DIR"
    rm -rf "$MG2D_TMP"
fi

# Classpath
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

cd $HOME
javac ./MG2D/*.java

# Bind clavier
sudo cp "$BORNE_DIR/borne" /usr/share/X11/xkb/symbols/borne


# Installe dependace python
REQ_COUNT=0
for req in "$BORNE_DIR"/projet/*/requirements.txt; do
    [ -f "$req" ] || continue
    GAME=$(basename "$(dirname "$req")")
    info "  → $GAME"
    pip3 install -r "$req" --user --break-system-packages \
        || warn "  Certaines dépendances de $GAME n'ont pas pu être installées."
    REQ_COUNT=$((REQ_COUNT + 1))
done
[ "$REQ_COUNT" -eq 0 ] && info "Aucun requirements.txt trouvé dans les jeux."

mkdir -p ~/.config/autostart
mv borne.desktop ~/.config/autostart/




# Lancer borne
./lancerBorne.sh