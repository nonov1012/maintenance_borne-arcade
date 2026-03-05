-- Mappings clavier borne arcade
-- J1: joystick = flèches | boutons bas = f g h | boutons haut = r t y
-- J2: joystick = o k l m | boutons bas = q s d | boutons haut = a z e

return {
    P1 = {
        left  = "left",
        right = "right",
        up    = "up",
        down  = "down",
        lp    = "f",   -- poing léger   (bas gauche)
        mp    = "g",   -- poing moyen   (bas milieu)
        hp    = "h",   -- poing fort    (bas droite)
        lk    = "r",   -- pied léger    (haut gauche)
        mk    = "t",   -- pied moyen    (haut milieu)
        block = "y",   -- parade        (haut droite)
    },
    P2 = {
        left  = "k",
        right = "m",
        up    = "o",
        down  = "l",
        lp    = "q",   -- poing léger
        mp    = "s",   -- poing moyen
        hp    = "d",   -- poing fort
        lk    = "a",   -- pied léger
        mk    = "z",   -- pied moyen
        block = "e",   -- parade
    },
}
