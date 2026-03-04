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

    private ProcessBuilder buildGameProcess(String gameDir, String gameName) {
	File dir = new File(gameDir);

	// Love2D
	if (new File(dir, "main.lua").exists()) {
	    return new ProcessBuilder("love", ".");
	}

	// Python: app/game.py
	if (new File(dir, "app/game.py").exists()) {
	    return new ProcessBuilder("python3", "app/game.py");
	}

	// Python: main.py
	if (new File(dir, "main.py").exists()) {
	    return new ProcessBuilder("python3", "main.py");
	}

	// Python: src/ directory (pas de .java à la racine)
	File srcDir = new File(dir, "src");
	if (srcDir.exists() && srcDir.isDirectory()
		&& !new File(dir, gameName + ".java").exists()
		&& !new File(dir, "Main.java").exists()) {
	    return new ProcessBuilder("python3", "./src");
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

    public void lancerJeu(ClavierBorneArcade clavier){
	if(clavier.getBoutonJ1ATape()){
	    try {
		Graphique.stopMusiqueFond();

		// Déplacer la souris hors de l'écran de jeu (ignoré si xdotool absent)
		try { new ProcessBuilder("xdotool", "mousemove", "1280", "1024").start(); } catch (IOException ignored) {}

		String gameDir = Graphique.tableau[getValue()].getChemin();
		String gameName = Graphique.tableau[getValue()].getNom();
		ProcessBuilder pb = buildGameProcess(gameDir, gameName);
		pb.directory(new File(gameDir));
		Process process = pb.start();
		process.waitFor();	// attendre la fin du jeu pour reprendre le contrôle sur le menu
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
