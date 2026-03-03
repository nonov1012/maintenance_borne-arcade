<!-- Généré automatiquement par Ollama (qwen3:8b) le 2026-03-03_16-51 -->
<!-- À relire et valider avant usage -->

## Description  
Columns est un jeu de puzzle 2D inspiré des jeux de type "match-3", où le joueur doit échanger des gemmes dans des colonnes pour créer des combinaisons de 3 ou plus. Le but est de supprimer les lignes pleines pour gagner des points et de survivre aussi longtemps que possible. Le jeu propose des modes solo et multijoueur, avec des contrôles personnalisés pour les joueurs.  

## Gameplay  
- **Mécanique de base** : Le joueur peut déplacer des gemmes en les échangeant entre colonnes adjacentes. Lorsqu'une combinaison de 3 ou plus est formée, les gemmes sont éliminées, et des nouvelles apparaissent en haut.  
- **Score et vies** : Le joueur gagne des points en supprimant des lignes. Le jeu se termine si le nombre de vies est atteint.  
- **Mode multijoueur** : Deux joueurs peuvent jouer simultanément, chacun contrôlant une colonne.  
- **Contrôles** : Utilise des manettes virtuelles pour les mouvements et des boutons d'action pour les échanges.  

## Architecture technique  
- **Classes principales** :  
  - `Main` : Gère la boucle principale, les entrées utilisateur et l'état global du jeu.  
  - `Colone` : Représente une colonne de gemmes avec des méthodes pour échanger, descendre et afficher les gemmes.  
  - `Gemme` : Modélise une gemme individuelle avec des attributs de couleur et des textures.  
  - `Puits` : Gère la grille de jeu (grille de colonnes et de lignes).  
  - `Partie` : Contrôle le flux de jeu, les transitions entre états (menu, partie, fin de jeu).  
  - `Menu` : Gère l'interface de sélection des modes de jeu (solo/multijoueur).  
- **Flux de jeu** : Le jeu commence par un menu, puis entre en mode partie (solo ou multijoueur), avec des mécanismes de détection de combinaisons et de suppression de lignes.  

## Dépendances  
- **Librairies** :  
  - `MG2D` : Pour la gestion des fenêtres, graphismes 2D et entrées utilisateur.  
  - `ClavierBorneArcade` : Contrôles personnalisés pour les manettes virtuelles.  
- **Environnement** :  
  - Java 8+ (compatibilité avec les classes `FenetrePleinEcran` et `Clavier`).  
  - JDK nécessaire pour compiler et exécuter le code.  

## Notes développeur  
- **Documentation** : Ajoutez des commentaires Javadoc pour toutes les classes et méthodes pour faciliter la maintenance.  
- **Corrections** :  
  - Ajoutez des descriptions aux constructeurs et méthodes manquantes (ex. `Colone`, `Gemme`).  
  - Vérifiez la cohérence des constantes (ex. `Gemme.COTE`, `Puits.LIGNEVIE`).  
- **Optimisations** :  
  - Structurez le code en packages (ex. `mg2d`, `game`, `ui`) pour une meilleure organisation.  
  - Implémentez un système de gestion d'erreurs pour les cas de figure inattendus (ex. `NullPointerException`).  
- **Tests** : Ajoutez des tests unitaires pour les méthodes critiques (ex. `descendre()`, `intervertir()`).