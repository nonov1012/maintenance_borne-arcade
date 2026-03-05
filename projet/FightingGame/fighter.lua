-- fighter.lua : classe Fighter

local GRAVITY   = 1700
local JUMP_VY   = -620
local WALK_SPD  = 240

-- Dodge
local DODGE_DUR     = 20   -- frames totales
local DODGE_INV_S   = 2    -- début invincibilité (frames)
local DODGE_INV_E   = 16   -- fin invincibilité
local DODGE_VX      = 380  -- vitesse initiale (px/s)

-- Données attaques : startup/active/recovery en frames (base 60fps)
local ATTACKS = {
    lp = { su=3,  ac=5,  re=9,  dmg=5,  rng=72,  kb=55,  type="p" },
    mp = { su=5,  ac=5,  re=13, dmg=10, rng=88,  kb=95,  type="p" },
    hp = { su=8,  ac=6,  re=19, dmg=15, rng=100, kb=150, type="p" },
    lk = { su=4,  ac=5,  re=11, dmg=8,  rng=86,  kb=85,  type="k" },
}

local ATK_ORDER = { "lp", "mp", "hp", "lk" }

-- Vérifie si une touche (string ou table de strings) est dans le dict pressed
local function isPressed(pressed, key)
    if type(key) == "table" then
        for _, k in ipairs(key) do
            if pressed[k] then return true end
        end
        return false
    end
    return pressed[key] == true
end

local Fighter = {}
Fighter.__index = Fighter

function Fighter.new(x, groundY, facing, keys, color, name)
    return setmetatable({
        x = x, y = groundY,
        vx = 0, vy = 0,
        groundY = groundY,
        facing = facing,
        keys = keys,
        color = color,
        name = name,
        w = 56, h = 112,
        hp = 100, maxhp = 100,
        state = "idle",   -- idle walk jump crouch attack dodge hurt dead
        stateT = 0,       -- timer en frames (x60)
        atk = nil,
        hitDone = false,
        pressed = {},
        animT = 0,
    }, Fighter)
end

function Fighter:onGround()
    return self.y >= self.groundY - 0.5
end

function Fighter:isInvincible()
    return self.state == "dodge"
       and self.stateT >= DODGE_INV_S
       and self.stateT <  DODGE_INV_E
end

-- Hurtbox
function Fighter:rect()
    local h = self.state == "crouch" and math.floor(self.h * 0.6) or self.h
    return self.x - self.w / 2, self.y - h, self.w, h
end

-- Hitbox attaque active
function Fighter:atkRect()
    if self.state ~= "attack" or not self.atk then return nil end
    local a = self.atk
    if self.stateT < a.su or self.stateT >= a.su + a.ac then return nil end
    local ax = self.facing == 1 and self.x + 6 or self.x - 6 - a.rng
    local offY = a.type == "k" and 0.15 or 0.25
    return ax, self.y - self.h + math.floor(self.h * offY), a.rng, math.floor(self.h * 0.5)
end

function Fighter:canAct()
    return self.state == "idle" or self.state == "walk" or self.state == "crouch"
end

function Fighter:update(dt, screenW)
    self.stateT = self.stateT + dt * 60
    self.animT  = self.animT  + dt

    local k     = self.keys
    local left  = love.keyboard.isDown(k.left)
    local right = love.keyboard.isDown(k.right)
    local down  = love.keyboard.isDown(k.down)

    -- ── Mort ──────────────────────────────────────────────────────────────
    if self.state == "dead" then
        self.vx = self.vx * 0.88
        self:_physics(dt)
        self.pressed = {}
        return
    end

    -- ── Hurt ──────────────────────────────────────────────────────────────
    if self.state == "hurt" then
        if self.stateT >= 24 then self.state = "idle" ; self.stateT = 0 end
        self.vx = self.vx * 0.80
        self:_physics(dt)
        self.pressed = {}
        return
    end

    -- ── Attaque en cours ──────────────────────────────────────────────────
    if self.state == "attack" then
        local a = self.atk
        if self.stateT >= a.su + a.ac + a.re then
            self.state = "idle" ; self.stateT = 0 ; self.hitDone = false
        end
        self.vx = 0
        self:_physics(dt)
        self.pressed = {}
        return
    end

    -- ── Esquive en cours ──────────────────────────────────────────────────
    if self.state == "dodge" then
        if self.stateT >= DODGE_DUR then
            self.state = "idle" ; self.stateT = 0 ; self.vx = 0
        else
            self.vx = self.vx * 0.84   -- décélération progressive
        end
        self:_physics(dt)
        self.pressed = {}
        return
    end

    -- ── Démarrer une esquive ──────────────────────────────────────────────
    if isPressed(self.pressed, k.dodge) and self:canAct() and self:onGround() then
        -- Direction : joystick gauche/droite, sinon en arrière
        local dir
        if left  then dir = -1
        elseif right then dir = 1
        else dir = -self.facing end   -- arrière par défaut
        self.state  = "dodge"
        self.stateT = 0
        self.vx     = dir * DODGE_VX
        self.pressed = {}
        self:_physics(dt)
        return
    end

    -- ── Démarrer une attaque ──────────────────────────────────────────────
    if self:canAct() or self.state == "jump" then
        for _, an in ipairs(ATK_ORDER) do
            if isPressed(self.pressed, k[an]) then
                self.state   = "attack"
                self.stateT  = 0
                self.atk     = ATTACKS[an]
                self.hitDone = false
                self.vx      = 0
                self.pressed = {}
                self:_physics(dt)
                return
            end
        end
    end

    -- ── Saut ──────────────────────────────────────────────────────────────
    if isPressed(self.pressed, k.up) and self:onGround() then
        self.vy    = JUMP_VY
        self.state = "jump" ; self.stateT = 0
        self.vx    = left and -WALK_SPD * 0.8 or (right and WALK_SPD * 0.8 or 0)
        self.pressed = {}
        self:_physics(dt)
        return
    end

    -- ── Mouvement au sol ──────────────────────────────────────────────────
    if self.state ~= "jump" then
        if down then
            self.state = "crouch" ; self.vx = 0
        elseif left then
            self.state = "walk"   ; self.vx = -WALK_SPD
        elseif right then
            self.state = "walk"   ; self.vx = WALK_SPD
        else
            self.state = "idle"   ; self.vx = 0
        end
    end

    self:_physics(dt)
    self.pressed = {}

    local hw = self.w / 2
    self.x = math.max(hw, math.min(screenW - hw, self.x))
end

function Fighter:_physics(dt)
    if not self:onGround() or self.vy < 0 then
        self.vy = self.vy + GRAVITY * dt
    end
    self.x = self.x + self.vx * dt
    self.y = self.y + self.vy * dt
    if self.y >= self.groundY then
        self.y = self.groundY ; self.vy = 0
        if self.state == "jump" then self.state = "idle" ; self.stateT = 0 end
    end
end

function Fighter:receiveHit(damage, kbDir, kbForce)
    if self.state == "dead" then return end
    self.vx     = kbDir * kbForce
    self.vy     = -80
    self.state  = "hurt"
    self.stateT = 0
    self.hp = math.max(0, self.hp - damage)
    if self.hp <= 0 then
        self.state = "dead"
        self.vy    = -220
        self.vx    = kbDir * kbForce * 0.6
    end
end

function Fighter:keypressed(key)
    self.pressed[key] = true
end

-- ── Dessin ────────────────────────────────────────────────────────────────────

local function lerp(a, b, t) return a + (b - a) * t end

function Fighter:draw()
    local bx, by, bw, bh = self:rect()
    local c = self.color
    local flash = math.floor(self.animT * 14) % 2 == 0
    local inv   = self:isInvincible()

    -- Afterimage pendant esquive invincible (copie décalée derrière)
    if self.state == "dodge" then
        local offX = -self.vx * 0.04
        love.graphics.setColor(c[1], c[2], c[3], 0.22)
        love.graphics.rectangle("fill", bx + offX, by, bw, bh, 10, 10)
        love.graphics.circle("fill", self.x + offX, by - 22, 21)
    end

    -- Ombre au sol
    local shadowAlpha = inv and 0.1 or 0.22
    love.graphics.setColor(0, 0, 0, shadowAlpha)
    love.graphics.ellipse("fill", self.x, self.groundY + 5, bw * 0.65, 9)

    -- Couleur corps
    local alpha = inv and (flash and 0.35 or 0.7) or 1.0
    if self.state == "dead" then
        love.graphics.setColor(c[1]*0.28, c[2]*0.28, c[3]*0.28, 1)
    elseif self.state == "hurt" and flash then
        love.graphics.setColor(1, 0.12, 0.12, 1)
    elseif self.state == "dodge" then
        -- Cyan pendant esquive
        love.graphics.setColor(lerp(c[1],0.2,0.6), lerp(c[2],0.9,0.6), lerp(c[3],1.0,0.6), alpha)
    elseif self.state == "attack" then
        local a = self.atk
        local active = self.stateT >= a.su and self.stateT < a.su + a.ac
        if active then love.graphics.setColor(1, 0.75, 0.1, 1)
        else love.graphics.setColor(lerp(c[1],1,0.25), lerp(c[2],0.8,0.25), c[3], 1) end
    else
        love.graphics.setColor(c[1], c[2], c[3], 1)
    end

    love.graphics.rectangle("fill", bx, by, bw, bh, 10, 10)
    love.graphics.setColor(0, 0, 0, 0.35)
    love.graphics.rectangle("line", bx, by, bw, bh, 10, 10)

    -- Tête
    local headY = by - 22
    love.graphics.setColor(lerp(c[1],1,0.28), lerp(c[2],1,0.28), lerp(c[3],1,0.28), alpha)
    love.graphics.circle("fill", self.x, headY, 21)
    love.graphics.setColor(0, 0, 0, 0.3)
    love.graphics.circle("line", self.x, headY, 21)

    -- Yeux
    local ex1 = self.x + self.facing * 4
    local ex2 = self.x + self.facing * 12
    love.graphics.setColor(0.06, 0.06, 0.06, alpha)
    love.graphics.circle("fill", ex1, headY - 2, 4)
    love.graphics.circle("fill", ex2, headY - 2, 4)

    if self.state == "attack" then
        love.graphics.setColor(0, 0, 0, 0.8)
        love.graphics.setLineWidth(2)
        love.graphics.line(ex1 - 5*self.facing, headY-9, ex1+3, headY-6)
        love.graphics.line(ex2 - 3*self.facing, headY-9, ex2+3*self.facing, headY-7)
        love.graphics.setLineWidth(1)
    end

    if self.state == "dead" then
        love.graphics.setColor(0.9, 0.1, 0.1, 0.9)
        love.graphics.setLineWidth(2)
        love.graphics.line(ex1-4, headY-6, ex1+4, headY+2)
        love.graphics.line(ex1+4, headY-6, ex1-4, headY+2)
        love.graphics.line(ex2-4, headY-6, ex2+4, headY+2)
        love.graphics.line(ex2+4, headY-6, ex2-4, headY+2)
        love.graphics.setLineWidth(1)
    end

    -- Aura cyan si invincible
    if inv then
        love.graphics.setColor(0.2, 0.9, 1, 0.5)
        love.graphics.setLineWidth(3)
        love.graphics.rectangle("line", bx - 3, by - 3, bw + 6, bh + 6, 12, 12)
        love.graphics.circle("line", self.x, headY, 24)
        love.graphics.setLineWidth(1)
    end

    -- Hitbox attaque
    local ax, ay, aw, ah = self:atkRect()
    if ax then
        love.graphics.setColor(1, 0.95, 0.1, 0.28)
        love.graphics.rectangle("fill", ax, ay, aw, ah, 4, 4)
        love.graphics.setColor(1, 0.9, 0, 0.9)
        love.graphics.rectangle("line", ax, ay, aw, ah, 4, 4)
    end

    love.graphics.setColor(1, 1, 1)
end

return Fighter
