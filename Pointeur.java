import java.io.IOException;
import java.io.File;

import MG2D.geometrie.Texture;
import MG2D.Couleur;
import MG2D.geometrie.Point;
import MG2D.geometrie.Triangle;
import MG2D.Clavier;


public class Pointeur {
    private int value;
    private Texture triangleGauche;
    private Texture triangleDroite;
    private Texture rectangleCentre;

    public Pointeur(){
	this.triangleGauche = new Texture("img/star.png", new Point(30, 492), 40,40);
	// this.triangleDroite = new Triangle(Couleur .ROUGE, new Point(550, 560), new Point(520, 510), new Point(550, 460), true);
	this.triangleDroite = new Texture("img/star.png", new Point(530, 492), 40,40);
	this.rectangleCentre = new Texture("img/select2.png", new Point(80, 460), 440, 100);
	this.value = Graphique.tableau.length-1;
    }

    /**
     * Retourne un ProcessBuilder qui applique le mapping clavier borne puis exécute la commande.
     * Utilisé pour les jeux non-Java (Python, Love2D) qui ne bénéficient pas du ClavierBorneArcade.
     *
     * NOTE: xmodmap ne fonctionne PAS pour pygame/SDL2 car SDL2 lit le keymap via l'extension
     * XKB du serveur X, pas l'ancien protocole X11 core que xmodmap modifie.
     * setxkbmap est la seule solution car il modifie directement le XKB state.
     */
    private static ProcessBuilder withKeymap(String command) {
	// Copier le fichier borne dans /usr/share si nécessaire, puis appliquer setxkbmap
	String borneFile = new File(System.getProperty("user.dir"), "borne").getAbsolutePath();
	String setupKeymap =
	    "[ -f /usr/share/X11/xkb/symbols/borne ] || " +
	    "sudo cp \"" + borneFile + "\" /usr/share/X11/xkb/symbols/borne 2>/dev/null || true; " +
	    // -symbols bypasse la base de règles evdev (plus fiable qu'un simple setxkbmap borne)
	    "setxkbmap -symbols 'pc+borne(basic)+inet(evdev)' 2>/dev/null || " +
	    "setxkbmap -symbols 'pc+borne(basic)' 2>/dev/null || " +
	    "setxkbmap borne 2>/dev/null || true";
	// Forcer la sortie audio jack (numid=3 val=1 sur RPi: 0=auto, 1=jack, 2=HDMI)
	String setupAudio = "amixer cset numid=3 1 2>/dev/null || true";
	ProcessBuilder pb = new ProcessBuilder("bash", "-c", setupKeymap + "; " + setupAudio + "; " + command);
	// SDL_AUDIODRIVER=alsa force pygame à utiliser ALSA plutôt que PulseAudio/auto
	pb.environment().put("SDL_AUDIODRIVER", "alsa");
	return pb;
    }

    private ProcessBuilder buildGameProcess(String gameDir, String gameName) {
	File dir = new File(gameDir);

	// Love2D
	if (new File(dir, "main.lua").exists()) {
	    return withKeymap("love .");
	}

	// Python: app/game.py
	if (new File(dir, "app/game.py").exists()) {
	    return withKeymap("python3 app/game.py");
	}

	// Python: main.py
	if (new File(dir, "main.py").exists()) {
	    return withKeymap("python3 main.py");
	}

	// Python: src/ directory (pas de .java à la racine)
	File srcDir = new File(dir, "src");
	if (srcDir.exists() && srcDir.isDirectory()
		&& !new File(dir, gameName + ".java").exists()
		&& !new File(dir, "Main.java").exists()) {
	    return withKeymap("python3 ./src");
	}

	// Java : créer highscore si absent
	try { new File(dir, "highscore").createNewFile(); } catch (IOException e) {}

	// Java : classe principale = gameName si le .java existe, sinon Main
	String mainClass = new File(dir, gameName + ".java").exists() ? gameName : "Main";
	return new ProcessBuilder("java",
	    "-Dprism.forceGPU=true", "-Dsun.java2d.opengl=true",
	    "-cp", ".:..:../..",
	    mainClass);
    }

    /** Récupère l'ID de la fenêtre active via xdotool, ou "" si indisponible. */
    private String getFocusedWindowId() {
	try {
	    Process p = new ProcessBuilder("xdotool", "getactivewindow").start();
	    String id = new String(p.getInputStream().readAllBytes()).trim();
	    p.waitFor();
	    return id;
	} catch (Exception e) {
	    return "";
	}
    }

    /** Donne le focus à une fenêtre via son ID xdotool. */
    private void focusWindow(String windowId) {
	if (windowId == null || windowId.isEmpty()) return;
	try {
	    new ProcessBuilder("xdotool", "windowfocus", "--sync", windowId).start().waitFor();
	    // Clic pour s'assurer que les événements clavier arrivent bien
	    new ProcessBuilder("xdotool", "windowactivate", "--sync", windowId).start().waitFor();
	} catch (Exception ignored) {}
    }

    /** Clique au centre de l'écran pour donner le focus à la fenêtre au premier plan. */
    private void clickCenter() {
	try {
	    new ProcessBuilder("xdotool", "mousemove", "640", "512", "click", "1").start();
	} catch (Exception ignored) {}
    }

    public void lancerJeu(ClavierBorneArcade clavier){
	if(clavier.getBoutonJ1ATape()){
	    try {
		Graphique.stopMusiqueFond();

		// Mémoriser la fenêtre du menu pour y revenir après le jeu
		String menuWindowId = getFocusedWindowId();

		String gameDir = Graphique.tableau[getValue()].getChemin();
		String gameName = Graphique.tableau[getValue()].getNom();
		ProcessBuilder pb = buildGameProcess(gameDir, gameName);
		pb.directory(new File(gameDir));
		Process process = pb.start();

		// Attendre que la fenêtre du jeu s'ouvre puis lui donner le focus
		Thread.sleep(800);
		clickCenter();

		process.waitFor();	// attendre la fin du jeu pour reprendre le contrôle sur le menu

		// Redonner le focus au menu
		focusWindow(menuWindowId);

		Graphique.lectureMusiqueFond();
	    } catch (IOException e) {
		e.printStackTrace();
	    } catch(Exception e){	// on catche toutes les exceptions, nécessaire pour le waitFor()
		e.printStackTrace();
	    }
	}
    }

    public int getValue() {
	return value;
    }

    public void setValue(int value) {
	this.value = value;
    }

    public Texture getTriangleGauche() {
	return triangleGauche;
    }

    public void setTriangleGauche(Texture triangleGauche) {
	this.triangleGauche = triangleGauche;
    }

    public Texture getTriangleDroite() {
	return triangleDroite;
    }

    public void setTriangleDroite(Texture triangleDroite) {
	this.triangleDroite = triangleDroite;
    }

    public Texture getRectangleCentre() {
	return rectangleCentre;
    }

    public void setRectangleCentre(Texture rectangleCentre) {
	this.rectangleCentre = rectangleCentre;
    }

}
