#!/bin/bash

setxkbmap borne 2>/dev/null || true

# Forcer la sortie audio sur le jack 3.5mm (0=auto, 1=jack, 2=HDMI)
amixer cset numid=3 1 2>/dev/null || true

cd "$HOME/borne_arcade"

echo "nettoyage des répertoires"
./clean.sh

echo "Compilation... Veuillez patienter"
./compilation.sh

echo "Lancement du Menu"

# Boucle de redémarrage : si le menu plante, il redémarre automatiquement
# On sort de la boucle seulement avec un code de sortie 0 (quitter volontairement)
while true; do
    java -Dprism.forceGPU=true -Dsun.java2d.opengl=true -cp .:$HOME/MG2D Main
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        break
    fi
    echo "Le menu a planté (code $EXIT_CODE), redémarrage dans 2 secondes..."
    sleep 2
done

./clean.sh

for i in {30..1}
do
    echo "Extinction de la borne dans $i secondes"
    sleep 1
done

sudo halt
