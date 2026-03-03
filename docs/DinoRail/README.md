<!-- Généré automatiquement par Ollama (qwen3:8b) le 2026-03-03_16-32 -->
<!-- À relire et valider avant usage -->

## Description  
DinoRail est un jeu de type *platformer* développé en Java, inspiré des jeux de course en 2D. Le joueur contrôle un personnage qui doit sauter et éviter des obstacles (cactus et oiseaux) en descendant vers le bas d'une piste. Le jeu se termine lors d'une collision avec un obstacle, et le joueur accumule un score au fil du temps. Le projet utilise une bibliothèque graphique personnalisée (MG2D) pour la gestion des affichages et des interactions.

---

## Gameplay  
- **Contrôle du joueur** : Le joueur peut sauter en appuyant sur le joystick haut, se baisser en appuyant sur le joystick bas.  
- **Obstacles** : Des cactus et des oiseaux apparaissent aléatoirement sur la piste. Leur déplacement est géré par une animation horizontale.  
- **Collision** : Si le joueur entre en collision avec un obstacle, le jeu s'arrête avec un message "Game over".  
- **Score** : Le score augmente automatiquement au fil du temps, et est affiché en bas de l'écran.  
- **Fin de partie** : Après la collision, le joueur peut quitter le jeu après un délai de 1 seconde.  

---

## Architecture technique  
- **Classe principale** : `DinoRail` gère la boucle principale du jeu, la logique de collision, le déplacement des obstacles, et la gestion du score.  
- **Obstacles** : La classe `Obstacle` hérite de `Texture` pour gérer l'affichage et vérifie si un obstacle est hors de l'écran (`isOffScreen`).  
- **Gestion d'input** : La classe `ClavierBorneArcade` (tronquée dans le code) gère les actions des joysticks et des boutons de la borne d'arcade.  
- **Gestion graphique** : Utilise la bibliothèque `MG2D` pour les primitives graphiques (rectangles, textes) et la gestion des événements clavier.  

---

## Dépendances  
- **MG2D** : Bibliothèque graphique personnalisée pour la gestion des affichages, des textures, et des interactions.  
- **Java AWT / Swing** : Utilisée pour la gestion des fenêtres et des événements clavier.  
- **Java Utilitaire** : Pour la gestion des threads et des listes.  

---

## Notes développeur  
1. **Javadoc manquant** :  
   - Ajouter des commentaires Javadoc pour la classe `DinoRail`, ses méthodes, et le constructeur.  
   - Compléter les commentaires pour la classe `Obstacle` et son constructeur.  
   - Documenter les méthodes `isOffScreen()` et `intersectionRapide()` pour clarifier leur fonction.  

2. **Code à améliorer** :  
   - Le code de `ClavierBorneArcade` est tronqué : compléter la gestion des événements clavier (ex. : touche "A", "B", etc.).  
   - Ajouter des gestionnaires d'exception pour les cas de `InterruptedException` dans les appels à `Thread.sleep()`.  
   - Optimiser la gestion des collisions et des obstacles pour une meilleure performance.  

3. **Expérience utilisateur** :  
   - Ajouter des sons (via la classe `Bruitage`) pour les sauts et les collisions.  
   - Implémenter un système de niveaux ou de difficulté progressive.  
   - Ajouter un menu de démarrage et une gestion des scores sauvegardés.