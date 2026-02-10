#!/bin/bash

echo "Compilation du menu de la borne d'arcade"
echo "Veuillez patienter"
javac -cp .:. *.java

cd projet


#PENSER A REMETTRE COMPILATION JEUX!!!
for i in *
do
    cd $i
    echo "Compilation du jeu "$i
    echo "Veuillez patienter"
    javac -cp .:../.. *.java 2>/dev/null || true
    cd ..
done

cd ..
