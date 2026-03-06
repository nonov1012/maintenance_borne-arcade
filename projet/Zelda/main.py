import subprocess
import sys
import os

# Lance Main.py depuis le sous-dossier Code/ (les chemins relatifs du jeu partent de là)
subprocess.run(
    [sys.executable, "Main.py"],
    cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "Code")
)
