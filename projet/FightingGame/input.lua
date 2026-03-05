-- Mappings clavier borne arcade
-- Double mapping P1 : {"scancode_azerty_brut", "keysym_apres_xkb"}
-- Boutons P1 physiques = touches numériques 1-6 (AZERTY)
-- Après XKB borne : 1→f  2→g  3→h  4→r  5→t  6→y
-- P2 : touches lettres directement (pas de remapping nécessaire)

return {
    P1 = {
        left  = "left",
        right = "right",
        up    = "up",
        down  = "down",
        lp    = {"1", "f"},   -- bas-gauche
        mp    = {"2", "g"},   -- bas-milieu
        hp    = {"3", "h"},   -- bas-droite
        lk    = {"4", "r"},   -- haut-gauche
        dodge = {"5", "t"},   -- haut-milieu
        -- pause = {"6","y"} géré dans main.lua
    },
    P2 = {
        left  = "k",
        right = "m",
        up    = "o",
        down  = "l",
        lp    = "q",          -- bas-gauche
        mp    = "s",          -- bas-milieu
        hp    = "d",          -- bas-droite
        lk    = "a",          -- haut-gauche
        dodge = "z",          -- haut-milieu
        -- pause = "e" géré dans main.lua
    },
}
