import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

/**
 * Détecte une séquence de touches (combo) configurée dans admin/config.json.
 * Fonctionne comme un KeyListener indépendant, sans consommer les événements
 * du reste de l'application (ClavierBorneArcade).
 *
 * Format attendu dans config.json :
 *   "shortcut": ["UP", "UP", "DOWN", "F"]
 *
 * Touches supportées : UP, DOWN, LEFT, RIGHT, F, G, H, R, T, Y
 */
public class ComboDetecteur implements KeyListener {

    private final int[] combo;
    private final Deque<Integer> historique;
    private volatile boolean comboDetecte;

    public ComboDetecteur() {
        this.combo = lireComboConfig();
        this.historique = new ArrayDeque<>();
        this.comboDetecte = false;
    }

    /**
     * Retourne true si le combo vient d'être déclenché, puis réinitialise le flag.
     */
    public boolean isComboDetecte() {
        if (comboDetecte) {
            comboDetecte = false;
            return true;
        }
        return false;
    }

    // --- KeyListener ---

    @Override
    public void keyReleased(KeyEvent e) {
        historique.addLast(e.getKeyCode());
        // Garde uniquement les N dernières touches (N = longueur du combo)
        while (historique.size() > combo.length) {
            historique.pollFirst();
        }
        if (historique.size() == combo.length && comboConcorde()) {
            comboDetecte = true;
            historique.clear();
        }
    }

    @Override public void keyPressed(KeyEvent e) {}
    @Override public void keyTyped(KeyEvent e)   {}

    // --- Vérification du combo ---

    private boolean comboConcorde() {
        int i = 0;
        for (int code : historique) {
            if (code != combo[i++]) return false;
        }
        return true;
    }

    // --- Lecture de config.json ---

    private static int[] lireComboConfig() {
        try {
            String content = new String(Files.readAllBytes(Paths.get("admin/config.json")));

            int debut = content.indexOf("\"shortcut\"");
            if (debut < 0) return comboParDefaut();

            int ouv = content.indexOf('[', debut);
            int ferm = content.indexOf(']', ouv);
            if (ouv < 0 || ferm < 0) return comboParDefaut();

            String tableau = content.substring(ouv + 1, ferm);
            List<Integer> codes = new ArrayList<>();
            for (String part : tableau.split(",")) {
                String nom = part.trim().replace("\"", "").toUpperCase();
                int code = nomVersKeyCode(nom);
                if (code >= 0) codes.add(code);
            }
            if (codes.isEmpty()) return comboParDefaut();

            return codes.stream().mapToInt(Integer::intValue).toArray();

        } catch (IOException e) {
            return comboParDefaut();
        }
    }

    private static int nomVersKeyCode(String nom) {
        switch (nom) {
            case "UP":    return KeyEvent.VK_UP;
            case "DOWN":  return KeyEvent.VK_DOWN;
            case "LEFT":  return KeyEvent.VK_LEFT;
            case "RIGHT": return KeyEvent.VK_RIGHT;
            case "F":     return KeyEvent.VK_F;
            case "G":     return KeyEvent.VK_G;
            case "H":     return KeyEvent.VK_H;
            case "R":     return KeyEvent.VK_R;
            case "T":     return KeyEvent.VK_T;
            case "Y":     return KeyEvent.VK_Y;
            default:      return -1;
        }
    }

    /** Combo par défaut si config.json est absent ou mal formé : UP UP DOWN F */
    private static int[] comboParDefaut() {
        return new int[]{KeyEvent.VK_UP, KeyEvent.VK_UP, KeyEvent.VK_DOWN, KeyEvent.VK_F};
    }
}
