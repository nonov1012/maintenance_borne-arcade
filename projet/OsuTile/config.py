# config.py

import pygame

# === Fenêtre ===
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 960
FPS = 60
FULLSCREEN = True

# === Affichage ===
BACKGROUND_COLOR = (0, 0, 0)
LANE_COLOR = (200, 200, 200)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (255, 255, 0)

# === Jeu ===
LANE_COUNT = 4
TILE_COLOR = (0, 150, 255)
HIT_LINE_Y = 800
FALL_TIME = 1.5
TILE_HEIGHT = 50
HIT_BOX_PIXEL = 30  # Tolérance

# === Contrôles ===
# Mappage des touches de jeu par colonne

KEY_MAPPING = {0: [pygame.K_t, pygame.K_LEFTPAREN], 1: [pygame.K_y, pygame.K_MINUS], 2: [pygame.K_a], 3: [pygame.K_z]}

PAUSE_KEY = [pygame.K_f, pygame.K_AMPERSAND]

# Contrôles de navigation dans les menus
MENU_UP_KEY = pygame.K_UP
MENU_DOWN_KEY = pygame.K_DOWN
MENU_SELECT_KEY = [pygame.K_g, 233]   # g ou é
MENU_BACK_KEY = [pygame.K_h, pygame.K_QUOTEDBL]

# Contrôles pour les menus (pause, fin)

MENU_RESUME_KEY = [pygame.K_g, 233]   # g ou é
MENU_QUIT_KEY = [pygame.K_h, pygame.K_QUOTEDBL]
MENU_BACK_TO_MENU_KEY = pygame.K_s
MENU_RETRY_KEY = pygame.K_d

# === Fichiers ===
BEATMAP_FOLDER = "beatmaps"
ASSETS_FOLDER = "assets"

# === Textes d'interface ===
MENU_TITLE = "Piano Tile Arcade"
SELECT_PROMPT = "Sélectionne une chanson"
