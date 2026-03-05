-- main.lua : IUT FIGHT - jeu de combat 2 joueurs pour borne arcade

local Fighter = require("fighter")
local Input   = require("input")

-- ── Constantes ────────────────────────────────────────────────────────────────
local W, H          -- dimensions réelles (récupérées dans love.load)
local GROUND_Y      -- calculé à partir de H
local ROUNDS_TO_WIN = 2
local TIMER_MAX     = 99

-- ── État global ───────────────────────────────────────────────────────────────
local scene         -- "countdown" | "fight" | "roundend" | "matchend"
local fighters
local timer
local roundsWon     -- { [1]=0, [2]=0 }
local currentRound
local roundWinner   -- 1 | 2 | "draw"
local matchWinner   -- 1 | 2 | nil
local sceneTimer

-- ── Fonts ─────────────────────────────────────────────────────────────────────
local fBig, fMed, fSml

-- ── Helpers ───────────────────────────────────────────────────────────────────
local function tryFont(size)
    -- Tente de charger PrStart depuis le dossier fonts du projet
    local ok, f = pcall(love.graphics.newFont, "../../fonts/PrStart.ttf", size)
    if ok then return f end
    return love.graphics.newFont(size)
end

local function centerX(text, font)
    return math.floor(W / 2 - font:getWidth(text) / 2)
end

local function printCenter(text, y, font, r, g, b, a)
    love.graphics.setFont(font)
    love.graphics.setColor(r or 1, g or 1, b or 1, a or 1)
    love.graphics.print(text, centerX(text, font), y)
end

-- ── Initialisation d'un round ─────────────────────────────────────────────────
local function startRound()
    GROUND_Y = math.floor(H * 0.82)
    fighters = {
        Fighter.new(math.floor(W * 0.25), GROUND_Y,  1, Input.P1, {0.25, 0.55, 1.0}, "P1"),
        Fighter.new(math.floor(W * 0.75), GROUND_Y, -1, Input.P2, {1.0,  0.30, 0.22}, "P2"),
    }
    timer      = TIMER_MAX
    roundWinner = nil
    scene      = "countdown"
    sceneTimer = 2.2   -- "ROUND X" + "FIGHT!"
end

-- ── love.load ─────────────────────────────────────────────────────────────────
function love.load()
    W, H = love.graphics.getDimensions()
    fBig = tryFont(math.floor(H * 0.09))
    fMed = tryFont(math.floor(H * 0.045))
    fSml = tryFont(math.floor(H * 0.025))

    love.graphics.setLineWidth(1)

    roundsWon    = { 0, 0 }
    currentRound = 1
    matchWinner  = nil
    startRound()
end

-- ── Collision détection ───────────────────────────────────────────────────────
local function rectsOverlap(ax, ay, aw, ah, bx, by, bw, bh)
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by
end

local function checkHit(atk, def)
    if atk.hitDone then return end
    local ax, ay, aw, ah = atk:atkRect()
    if not ax then return end
    local dx, dy, dw, dh = def:rect()
    if rectsOverlap(ax, ay, aw, ah, dx, dy, dw, dh) then
        atk.hitDone = true
        local a = atk.atk
        def:receiveHit(a.dmg, atk.facing, a.kb, def.isBlocking)
    end
end

-- Empêche les deux fighters de se chevaucher (pushbox)
local function pushbox()
    local f1, f2 = fighters[1], fighters[2]
    local minDist = f1.w / 2 + f2.w / 2 - 4
    local dist = f2.x - f1.x
    if math.abs(dist) < minDist then
        local push = (minDist - math.abs(dist)) / 2 + 1
        if dist >= 0 then
            f1.x = f1.x - push
            f2.x = f2.x + push
        else
            f1.x = f1.x + push
            f2.x = f2.x - push
        end
    end
end

-- Met à jour le facing (regarder l'adversaire) sauf pendant attaque/hurt/dead
local function updateFacing()
    local f1, f2 = fighters[1], fighters[2]
    local function canFace(f)
        return f.state ~= "attack" and f.state ~= "hurt" and f.state ~= "dead"
    end
    if canFace(f1) then f1.facing = f2.x > f1.x and 1 or -1 end
    if canFace(f2) then f2.facing = f1.x > f2.x and 1 or -1 end
end

-- Vérifie la fin du round
local function checkRoundEnd()
    local f1, f2 = fighters[1], fighters[2]
    if f1.hp > 0 and f2.hp > 0 and timer > 0 then return end

    if f1.hp <= 0 and f2.hp <= 0 then
        roundWinner = "draw"
    elseif f1.hp <= 0 then
        roundWinner = 2
    elseif f2.hp <= 0 then
        roundWinner = 1
    else
        -- Timeout
        if   f1.hp > f2.hp then roundWinner = 1
        elseif f2.hp > f1.hp then roundWinner = 2
        else roundWinner = "draw" end
    end

    if roundWinner ~= "draw" then
        roundsWon[roundWinner] = roundsWon[roundWinner] + 1
    end

    if     roundsWon[1] >= ROUNDS_TO_WIN then matchWinner = 1
    elseif roundsWon[2] >= ROUNDS_TO_WIN then matchWinner = 2 end

    currentRound = currentRound + 1
    scene      = "roundend"
    sceneTimer = 2.8
end

-- ── love.update ───────────────────────────────────────────────────────────────
function love.update(dt)
    dt = math.min(dt, 0.05)
    sceneTimer = sceneTimer - dt

    if scene == "countdown" then
        if sceneTimer <= 0 then
            scene      = "fight"
            sceneTimer = 0
        end
        -- Les fighters sont déjà créés mais on ne les met pas à jour
        return
    end

    if scene == "roundend" then
        if sceneTimer <= 0 then
            if matchWinner then
                scene      = "matchend"
                sceneTimer = 999
            else
                startRound()
            end
        end
        -- Petite physique de mort (chute)
        for _, f in ipairs(fighters) do
            if f.state == "dead" then
                f.vy = f.vy + 1700 * dt
                f.y  = f.y + f.vy * dt
                if f.y >= f.groundY then f.y = f.groundY ; f.vy = 0 end
            end
        end
        return
    end

    if scene == "matchend" then return end

    -- ── fight ──
    timer = math.max(0, timer - dt)

    for _, f in ipairs(fighters) do
        f:update(dt, W)
    end

    updateFacing()
    pushbox()

    -- Clamp à l'écran après pushbox
    for _, f in ipairs(fighters) do
        local hw = f.w / 2
        f.x = math.max(hw, math.min(W - hw, f.x))
    end

    checkHit(fighters[1], fighters[2])
    checkHit(fighters[2], fighters[1])
    checkRoundEnd()
end

-- ── love.keypressed ───────────────────────────────────────────────────────────
function love.keypressed(key)
    if key == "escape" then love.event.quit() end

    if scene == "matchend" then
        -- N'importe quelle touche joueur relance
        if key == "f" or key == "q" or key == "return" then
            roundsWon    = { 0, 0 }
            currentRound = 1
            matchWinner  = nil
            startRound()
        end
        return
    end

    for _, f in ipairs(fighters or {}) do
        f:keypressed(key)
    end
end

-- ── Dessin ────────────────────────────────────────────────────────────────────

local function drawBackground()
    -- Ciel nuit
    love.graphics.setColor(0.04, 0.04, 0.14)
    love.graphics.rectangle("fill", 0, 0, W, H)

    -- Lune
    love.graphics.setColor(0.92, 0.88, 0.60, 0.7)
    love.graphics.circle("fill", W * 0.5, H * 0.18, math.floor(H * 0.06))
    love.graphics.setColor(0.04, 0.04, 0.14)
    love.graphics.circle("fill", W * 0.5 + H * 0.04, H * 0.18 - H * 0.01, math.floor(H * 0.055))

    -- Étoiles décoratives
    math.randomseed(42)
    love.graphics.setColor(1, 1, 1, 0.5)
    for _ = 1, 40 do
        local sx = math.random(W)
        local sy = math.random(math.floor(H * 0.55))
        love.graphics.circle("fill", sx, sy, 1.5)
    end

    -- Sol
    love.graphics.setColor(0.28, 0.20, 0.12)
    love.graphics.rectangle("fill", 0, GROUND_Y, W, H - GROUND_Y)

    -- Ligne de sol
    love.graphics.setColor(0.48, 0.34, 0.18)
    love.graphics.rectangle("fill", 0, GROUND_Y, W, 4)

    -- Briques décoratives
    love.graphics.setColor(0.22, 0.16, 0.10)
    local brickW, brickH = 80, 20
    for row = 0, 2 do
        local offX = (row % 2) * (brickW / 2)
        for col = -1, math.ceil(W / brickW) + 1 do
            local bx = col * brickW + offX
            local by = GROUND_Y + 8 + row * (brickH + 3)
            love.graphics.rectangle("line", bx, by, brickW - 2, brickH)
        end
    end
end

local function drawHPBar(x, y, w, h, hp, maxhp, flipped, name, color)
    -- Fond sombre
    love.graphics.setColor(0.12, 0.04, 0.04)
    love.graphics.rectangle("fill", x, y, w, h, 4, 4)

    -- Barre HP
    local ratio = hp / maxhp
    local barW  = math.floor((w - 4) * ratio)
    local barX  = flipped and (x + 2 + (w - 4) - barW) or (x + 2)

    if     ratio > 0.5 then love.graphics.setColor(0.15, color[2] * 0.9 + 0.1, color[3] * 0.3)
    elseif ratio > 0.25 then love.graphics.setColor(0.85, 0.65, 0.08)
    else                     love.graphics.setColor(0.9,  0.08, 0.08) end

    if barW > 0 then
        love.graphics.rectangle("fill", barX, y + 2, barW, h - 4, 3, 3)
    end

    -- Contour
    love.graphics.setColor(0.75, 0.75, 0.75)
    love.graphics.rectangle("line", x, y, w, h, 4, 4)

    -- Nom
    love.graphics.setFont(fSml)
    love.graphics.setColor(1, 1, 1)
    local nx = flipped and (x + w - fSml:getWidth(name) - 8) or (x + 8)
    love.graphics.print(name, nx, y - fSml:getHeight() - 2)
end

local function drawRoundPips(cx, y, won, total, color)
    local spacing = 22
    local startX  = cx - (total - 1) * spacing / 2
    for i = 1, total do
        local px = startX + (i - 1) * spacing
        if i <= won then
            love.graphics.setColor(color[1], color[2], color[3], 1)
            love.graphics.circle("fill", px, y, 8)
        else
            love.graphics.setColor(0.28, 0.28, 0.28)
            love.graphics.circle("line", px, y, 8)
        end
    end
end

local function drawHUD()
    local barW = math.floor(W * 0.36)
    local barH = math.floor(H * 0.034)
    local barY = math.floor(H * 0.025)
    local pad  = math.floor(W * 0.016)

    drawHPBar(pad, barY, barW, barH,
              fighters[1].hp, fighters[1].maxhp, false, "P1", fighters[1].color)
    drawHPBar(W - pad - barW, barY, barW, barH,
              fighters[2].hp, fighters[2].maxhp, true,  "P2", fighters[2].color)

    -- Timer
    local ts = string.format("%02d", math.ceil(timer))
    love.graphics.setFont(fMed)
    local tc = timer <= 10 and {1, 0.18, 0.18} or {1, 1, 1}
    love.graphics.setColor(tc[1], tc[2], tc[3])
    love.graphics.print(ts, centerX(ts, fMed), barY)

    -- Pips ronde (sous le timer)
    local pipY = barY + barH + math.floor(H * 0.025)
    drawRoundPips(W / 2 - 28, pipY, roundsWon[1], ROUNDS_TO_WIN, fighters[1].color)
    drawRoundPips(W / 2 + 28, pipY, roundsWon[2], ROUNDS_TO_WIN, fighters[2].color)
end

local function drawCountdown()
    if sceneTimer > 1.0 then
        -- "ROUND X"
        local label = "ROUND " .. currentRound
        printCenter(label, H * 0.35, fBig, 1, 0.82, 0.12)
        printCenter("READY?", H * 0.52, fMed, 0.9, 0.9, 0.9)
    else
        -- "FIGHT!"
        local scale = 1 + (1 - sceneTimer / 1.0) * 0.3
        love.graphics.push()
        love.graphics.translate(W / 2, H * 0.46)
        love.graphics.scale(scale, scale)
        local txt = "FIGHT!"
        love.graphics.setFont(fBig)
        love.graphics.setColor(0.12, 1, 0.25)
        love.graphics.print(txt, -fBig:getWidth(txt) / 2, -fBig:getHeight() / 2)
        love.graphics.pop()
    end
end

local function drawRoundEnd()
    love.graphics.setColor(0, 0, 0, 0.45)
    love.graphics.rectangle("fill", 0, H * 0.32, W, H * 0.36)

    if roundWinner == "draw" then
        printCenter("DRAW!", H * 0.38, fBig, 0.85, 0.85, 0.15)
    else
        local wname = "PLAYER " .. roundWinner
        local wc    = fighters[roundWinner] and fighters[roundWinner].color or {1,1,1}
        printCenter("K.O.", H * 0.35, fBig, 1, 0.12, 0.12)
        printCenter(wname .. " WINS", H * 0.52, fMed, wc[1], wc[2], wc[3])
    end
end

local function drawMatchEnd()
    love.graphics.setColor(0, 0, 0, 0.72)
    love.graphics.rectangle("fill", 0, 0, W, H)

    if matchWinner then
        local wc = fighters and fighters[matchWinner] and fighters[matchWinner].color or {1,1,1}
        printCenter("PLAYER " .. matchWinner, H * 0.28, fBig, wc[1], wc[2], wc[3])
        printCenter("WINS THE MATCH!", H * 0.44, fMed, 1, 0.88, 0.1)
    end

    -- Clignotement "appuyez pour rejouer"
    if math.floor(love.timer.getTime() * 2) % 2 == 0 then
        printCenter("PRESS F (P1) OR Q (P2) TO PLAY AGAIN", H * 0.65, fSml, 0.65, 0.65, 0.65)
    end
end

function love.draw()
    drawBackground()

    if fighters then
        for _, f in ipairs(fighters) do f:draw() end
        if scene == "fight" or scene == "roundend" then
            drawHUD()
        end
    end

    if     scene == "countdown" then drawCountdown()
    elseif scene == "roundend"  then drawRoundEnd()
    elseif scene == "matchend"  then drawMatchEnd()
    end

    love.graphics.setColor(1, 1, 1)
end
