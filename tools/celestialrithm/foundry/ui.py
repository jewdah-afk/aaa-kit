"""Batch B: Shop + Inventory + Taskbar + currency HUD composed from foundry materials.

    python3 -m tools.celestialrithm.foundry.ui --out media/celestialrithm/frontier/ui-shop-inventory --seconds 10

One purchase story, driven by an explicit event table (the state machine):
idle (selected Legendary card is the only thing animating at full rate)
-> BUY pressed -> currency counts down -> item revealed in its inventory slot
-> bag badge pops -> player opens Inventory (taskbar active state moves) -> settle.

Hierarchy rules applied (HIERARCHY.md): one loud element per panel (s13),
calm frames stay calm (unselected cards run at 0.3x time and 80% exposure),
rarity ladder materials (Epic = glass/gem, Legendary = molten, Mythic = holo
foil), reward sequencing container -> item -> what changed (s14).
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from . import keycap as kc
from . import materials as M
from .board import encode, make_gif, press_curve, probe
from .fields import F32, blur
from .optics import hex_rgb, linear_to_srgb

FONT = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
W, H = 1280, 720

RARITY = {'epic': '#b25cff', 'legendary': '#ffb02e', 'mythic': '#ff3d7f', 'rare': '#5ab4ff', 'common': '#9aa4b2', 'uncommon': '#4fd17a'}

# ---------------------------------------------------------------- the state machine (data, not logic)
EVENTS = [
    {'t': 0.0, 'event': 'idle', 'owner': 'card:legendary'},
    {'t': 2.2, 'event': 'buy_press', 'owner': 'button:buy'},
    {'t': 2.6, 'event': 'currency_debit', 'owner': 'hud:currency', 'from': 12480, 'to': 7480, 'dur': .7},
    {'t': 3.6, 'event': 'item_reveal', 'owner': 'slot:new'},
    {'t': 4.7, 'event': 'badge_pop', 'owner': 'taskbar:bag'},
    {'t': 6.4, 'event': 'tab_switch', 'owner': 'taskbar:bag', 'from': 'shop', 'to': 'bag'},
    {'t': 7.4, 'event': 'settle', 'owner': 'slot:new'},
]


def ev(name):
    return next(e for e in EVENTS if e['event'] == name)


# ---------------------------------------------------------------- icons (vector, painted style)
def icon(kind, size):
    """Draw an icon at 4x and downsample (LANCZOS) -> RGBA. Flat cel shading, black ink."""
    S = 4; n = size * S
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    u = n / 100.0
    ink = (8, 9, 14, 255); lw = int(4.5 * u)

    def P(pts):
        return [(x * u, y * u) for x, y in pts]

    if kind == 'gem':
        outer = P([(50, 8), (86, 32), (74, 80), (50, 94), (26, 80), (14, 32)])
        d.polygon(outer, fill=(255, 128, 196, 255))
        d.polygon(P([(50, 8), (86, 32), (50, 40)]), fill=(255, 196, 228, 255))
        d.polygon(P([(14, 32), (50, 40), (26, 80)]), fill=(214, 70, 150, 255))
        d.polygon(P([(50, 40), (74, 80), (50, 94), (26, 80)]), fill=(176, 40, 120, 255))
        d.polygon(P([(50, 8), (14, 32), (50, 40)]), fill=(255, 160, 214, 255))
        d.line(P([(14, 32), (50, 40), (86, 32)]), fill=ink, width=lw // 2)
        d.line(P([(50, 40), (50, 94)]), fill=ink, width=lw // 2)
        d.polygon(outer, outline=ink, width=lw)
        d.ellipse(P([(36, 18), (46, 26)]), fill=(255, 255, 255, 230))
    elif kind == 'sword':
        blade = P([(50, 6), (60, 18), (58, 64), (42, 64), (40, 18)])
        d.polygon(blade, fill=(214, 226, 240, 255)); d.polygon(P([(50, 6), (60, 18), (58, 64), (50, 64)]), fill=(150, 168, 196, 255))
        d.polygon(blade, outline=ink, width=lw)
        d.rectangle(P([(26, 62), (74, 72)]), fill=(255, 176, 46, 255), outline=ink, width=lw)
        d.rectangle(P([(44, 72), (56, 88)]), fill=(120, 64, 32, 255), outline=ink, width=lw)
        d.ellipse(P([(40, 86), (60, 98)]), fill=(255, 176, 46, 255), outline=ink, width=lw)
    elif kind == 'potion':
        d.ellipse(P([(18, 34), (82, 96)]), fill=(120, 230, 90, 255), outline=ink, width=lw)
        d.chord(P([(18, 34), (82, 96)]), 200, 340, fill=(220, 255, 210, 255))
        d.ellipse(P([(18, 34), (82, 96)]), outline=ink, width=lw)
        d.rectangle(P([(40, 14), (60, 38)]), fill=(200, 220, 230, 255), outline=ink, width=lw)
        d.rectangle(P([(36, 6), (64, 16)]), fill=(150, 90, 50, 255), outline=ink, width=lw)
        d.ellipse(P([(30, 50), (40, 60)]), fill=(255, 255, 255, 230))
    elif kind == 'coin':
        d.ellipse(P([(8, 8), (92, 92)]), fill=(255, 196, 40, 255), outline=ink, width=lw)
        d.ellipse(P([(22, 22), (78, 78)]), fill=(255, 222, 90, 255), outline=(176, 110, 10, 255), width=lw // 2)
        d.rectangle(P([(44, 32), (56, 68)]), fill=(200, 130, 10, 255))
        d.ellipse(P([(20, 16), (34, 26)]), fill=(255, 250, 220, 230))
    elif kind == 'bag':
        d.rounded_rectangle(P([(16, 34), (84, 92)]), radius=10 * u, fill=(176, 110, 60, 255), outline=ink, width=lw)
        d.rectangle(P([(16, 50), (84, 60)]), fill=(140, 82, 40, 255))
        d.rounded_rectangle(P([(16, 34), (84, 92)]), radius=10 * u, outline=ink, width=lw)
        d.arc(P([(32, 10), (68, 50)]), 180, 360, fill=ink, width=lw)
        d.rectangle(P([(44, 50), (56, 66)]), fill=(255, 200, 60, 255), outline=ink, width=lw // 2)
    elif kind == 'shop':
        d.rectangle(P([(16, 44), (84, 92)]), fill=(90, 160, 255, 255), outline=ink, width=lw)
        for i in range(4):
            col = (255, 90, 90, 255) if i % 2 == 0 else (255, 240, 240, 255)
            d.polygon(P([(10 + i * 20, 22), (30 + i * 20, 22), (30 + i * 20, 46), (10 + i * 20, 46)]), fill=col)
        d.polygon(P([(10, 22), (90, 22), (90, 46), (10, 46)]), outline=ink, width=lw)
        d.rectangle(P([(40, 62), (60, 92)]), fill=(40, 60, 110, 255), outline=ink, width=lw)
    elif kind == 'paw':
        d.ellipse(P([(26, 46), (74, 90)]), fill=(255, 170, 200, 255), outline=ink, width=lw)
        for (x, y) in ((18, 30), (36, 14), (58, 14), (76, 30)):
            d.ellipse(P([(x - 10, y - 10), (x + 10, y + 12)]), fill=(255, 170, 200, 255), outline=ink, width=lw)
    elif kind == 'scroll':
        d.rectangle(P([(22, 18), (78, 84)]), fill=(250, 232, 190, 255), outline=ink, width=lw)
        for yy in (34, 48, 62):
            d.line(P([(32, yy), (68, yy)]), fill=(150, 120, 80, 255), width=lw // 2)
        d.ellipse(P([(14, 10), (34, 26)]), fill=(220, 190, 140, 255), outline=ink, width=lw)
        d.ellipse(P([(66, 76), (86, 92)]), fill=(220, 190, 140, 255), outline=ink, width=lw)
    elif kind == 'gear':
        cx = cy = 50 * u
        pts = []
        for k in range(16):
            a = k / 16 * 2 * math.pi; r = (44 if k % 2 == 0 else 34) * u
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=(170, 180, 200, 255), outline=ink, width=lw)
        d.ellipse((cx - 14 * u, cy - 14 * u, cx + 14 * u, cy + 14 * u), fill=(60, 66, 84, 255), outline=ink, width=lw)
    elif kind == 'crown':
        d.polygon(P([(10, 80), (14, 30), (32, 52), (50, 16), (68, 52), (86, 30), (90, 80)]), fill=(255, 196, 40, 255), outline=ink, width=lw)
        d.rectangle(P([(10, 76), (90, 90)]), fill=(220, 150, 20, 255), outline=ink, width=lw)
        for x in (30, 50, 70):
            d.ellipse(P([(x - 5, 78), (x + 5, 88)]), fill=(255, 60, 120, 255))
    return im.resize((size, size), Image.LANCZOS)


def text(draw, xy, s, size, fill=(255, 255, 255), stroke=3, anchor='mm'):
    f = ImageFont.truetype(FONT, size)
    draw.text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(6, 7, 12), anchor=anchor)


# ---------------------------------------------------------------- panels
def panel(canvas, x0, y0, x1, y1, r=18, accent='#4fb4ff'):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    d = kc.sd_round_rect(xx - (x0 + x1) / 2, yy - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r)
    inside = kc.cover(d)
    sh = blur(kc.cover(d - 6, 2), 8) * .6
    canvas *= (1 - sh * (1 - inside))[..., None]
    plate = hex_rgb('#0b1430') * (1 - .4 * np.clip((yy - y0) / (y1 - y0), 0, 1))[..., None]
    canvas[:] = canvas * (1 - inside[..., None]) + plate * inside[..., None]
    rim = kc.cover(d + 2.5) * (1 - kc.cover(d + 7))
    lit = np.clip((y0 + 30 - yy) / 30, 0, 1)
    canvas += rim[..., None] * hex_rgb('#1b2a55') * (.6 + 1.2 * lit)[..., None]
    ink = inside * (1 - kc.cover(d + 3))
    canvas[:] = canvas * (1 - ink[..., None]) + hex_rgb('#010204') * ink[..., None]
    bar = (np.abs(xx - (x0 + x1) / 2) < (x1 - x0) * .18) & (np.abs(yy - (y0 + 4)) < 1.4)
    canvas += blur(bar.astype(F32), 2.5)[..., None] * hex_rgb(accent) * 1.0


def backdrop():
    """Dim, out-of-focus 'world' behind the UI (tier 4 calm), with a scrim."""
    n = M.fl.Noise(5)
    xs, ys = M.fl.grid(W // 8, H // 8)
    f = n.fbm(xs * 1.5, ys * 1.5, .3, 4) * .5 + .5
    from .optics import ramp
    col = ramp(f, [(0, hex_rgb('#030612')), (.6, hex_rgb('#0a1a33')), (1, hex_rgb('#173a5c'))])
    col = M.fl.resize(col, W, H)
    yy = np.linspace(0, 1, H, dtype=F32)[:, None, None]
    return (col * (.55 + .2 * yy)).astype(F32)


# ---------------------------------------------------------------- scene
class Scene:
    def __init__(self, seed=3, hierarchy=True):
        self.hierarchy = hierarchy          # False = the 'everything loud' control for the before/after audit
        self.bg = backdrop()
        L = (28, 78, 812, 560); R = (836, 78, 1252, 560)
        panel(self.bg, *L, accent=RARITY['legendary']); panel(self.bg, *R, accent=RARITY['rare'])
        panel(self.bg, 400, 600, 880, 712, r=16)
        self.L, self.R = L, R
        # shop cards: Epic gem (crystal), Legendary sword (molten), Mythic potion (holo foil)
        self.card_shell = kc.Shell(w=232, h=290, radius=12, ink=4, bezel=8, inner_ink=2, depth=12)
        cw = self.card_shell.w
        gap = (L[2] - L[0] - 3 * cw) / 4
        self.cards = []
        for i, (rar, mid, ico, price) in enumerate((('epic', 'crystal_ice', 'gem', '2,500'), ('legendary', 'molten_core', 'sword', '5,000'),
                                                    ('mythic', 'holo_foil', 'potion', '9,900'))):
            cx = int(L[0] + gap * (i + 1) + cw * (i + .5)); cy = 296
            sh = self.card_shell
            mat = M.REGISTRY[mid](sh.face_w, sh.face_h, seed=seed + i)
            tint = M.REGISTRY[mid].tint(); tint['rim'] = hex_rgb(RARITY[rar])
            ic = icon(ico, 120)
            dim = ImageEnhance.Brightness(ImageEnhance.Color(ic).enhance(.55)).enhance(.62)
            self.cards.append(dict(rar=rar, mat=mat, tint=tint, icon=ic, icon_dim=dim if hierarchy else ic, cx=cx, cy=cy, price=price, name={'gem': 'Star Gem', 'sword': 'Ember Blade', 'potion': 'Prism Tonic'}[ico]))
        self.owner_card = 1
        self.btn_shell = kc.Shell(w=206, h=64, radius=10, ink=4, bezel=6, inner_ink=2, depth=8)
        self.buy = M.REGISTRY['bio_slime'](self.btn_shell.face_w, self.btn_shell.face_h, seed=seed + 9)
        self.buy_tint = M.REGISTRY['bio_slime'].tint()
        self.flat_shell = self.btn_shell
        # inventory 4x3
        self.slot_shell = kc.Shell(w=88, h=92, radius=8, ink=3, bezel=5, inner_ink=1.5, depth=7)
        self.slots = []
        items = ['coin', 'scroll', 'paw', 'gem', 'potion', None, 'coin', 'gear', 'scroll', None, None, None]
        rar = ['common', 'uncommon', 'rare', 'epic', 'uncommon', None, 'common', 'rare', 'common', None, None, None]
        for k in range(12):
            c, r = k % 4, k // 4
            cx = R[0] + 58 + c * 100; cy = 190 + r * 118
            ic = icon(items[k], 56) if items[k] else None
            if ic is not None and hierarchy:             # calm inventory: icons at 80% value until selected
                ic = ImageEnhance.Brightness(ImageEnhance.Color(ic).enhance(.75)).enhance(.8)
            self.slots.append(dict(cx=cx, cy=cy, icon=ic, rar=rar[k]))
        self.new_slot = 5
        self.slot_mat = M.REGISTRY['molten_core'](self.slot_shell.face_w, self.slot_shell.face_h, seed=seed + 20)
        # taskbar
        self.tb_shell = kc.Shell(w=78, h=76, radius=8, ink=3, bezel=5, inner_ink=1.5, depth=7)
        self.tabs = []
        for k, ico in enumerate(('shop', 'bag', 'paw', 'scroll', 'gear')):
            self.tabs.append(dict(name=ico, cx=448 + k * 96, cy=652, icon=icon(ico, 44)))
        self.tab_mat = M.REGISTRY['hydroglass'](self.tb_shell.face_w, self.tb_shell.face_h, seed=seed + 30)
        self.coin = icon('coin', 44); self.crown = icon('crown', 40)
        # HUD coin is tier 3: readable, but calmer than the purchase owner (audit round 2 found it was first fixation)
        self.hud_coin = ImageEnhance.Brightness(ImageEnhance.Color(icon('coin', 36)).enhance(.7)).enhance(.85) if hierarchy else self.coin
        self.dark_face_cache = {}
        self.timing = []

    def dark_face(self, shell, rar):
        key = (shell, rar)
        if key not in self.dark_face_cache:
            fh, fw = shell.face_h, shell.face_w
            y = np.linspace(0, 1, fh, dtype=F32)[:, None, None]
            base = hex_rgb('#16224a') * (1 - .45 * y) + hex_rgb('#0a1026') * .3
            if rar:
                base = base + hex_rgb(RARITY[rar]) * .05 * (1 - y)
            self.dark_face_cache[key] = np.broadcast_to(base, (fh, fw, 3)).astype(F32).copy()
        return self.dark_face_cache[key]

    def render(self, t):
        t0 = time.perf_counter()
        cv = self.bg.copy()
        overlays = []           # (image, x, y) drawn after sRGB conversion
        texts = []
        # --- shop cards
        bp = ev('buy_press')['t']
        buy_p, _ = press_curve(t - bp)
        for i, c in enumerate(self.cards):
            owner = i == self.owner_card or not self.hierarchy
            rate = 1.0 if owner else .3
            p = max(buy_p, 0) if owner else 0.0
            face, glow = c['mat'].frame(t * rate, p)
            # protected region behind the icon: material backs off so the icon reads
            fh, fw = face.shape[:2]
            yy, xx = np.mgrid[0:fh, 0:fw].astype(F32)
            prot = np.exp(-(((xx - fw / 2) / (fw * .34)) ** 2 + ((yy - fh * .44) / (fh * .3)) ** 2) * 1.2)
            if owner and self.hierarchy:
                # Legendary ladder step: warm halo behind the item (rays) instead of a dim protected zone
                face = face * (1 - .35 * prot)[..., None] * 1.15 + hex_rgb(RARITY['legendary']) * (prot ** 1.5 * .55)[..., None]
            else:
                face = face * (1 - .45 * prot)[..., None] * (1.0 if owner else .42)
            sweep = ((t % 2.6) / 1.2) if (c['rar'] in ('legendary',) and (t % 2.6) < 1.2) else -1
            kc.compose(cv, c['cx'], c['cy'], self.card_shell, face, glow * (1 if owner else .4), c['tint'], t, sweep=sweep, press=p * .6)
            if owner and self.hierarchy:                 # outer glow outside the ink (Legendary only)
                gy0, gx0 = c['cy'] - 170, c['cx'] - 150
                yy2, xx2 = np.mgrid[0:340, 0:300].astype(F32)
                dd = kc.sd_round_rect(xx2 - 150, yy2 - 170 + 6, 118, 147, 14)
                halo = np.exp(-np.clip(dd, 0, None) / 9.0) * (dd > 0) * (.28 + .06 * math.sin(t * 2.4))
                cv[gy0:gy0 + 340, gx0:gx0 + 300] += hex_rgb(RARITY['legendary']) * halo[..., None]
            ic = c['icon'] if owner else c['icon_dim']
            overlays.append((ic, c['cx'] - 60, c['cy'] - 92))
            texts.append((c['cx'], c['cy'] + 64, c['name'], 21, (255, 255, 255)))
            texts.append((c['cx'], c['cy'] + 90, c['rar'].upper(), 14, tuple(int(v * 255) for v in linear_to_srgb(hex_rgb(RARITY[c['rar']])))))
            # buy buttons: only the owner's is a live material (one loud element per panel)
            by = c['cy'] + 196
            if owner:
                bface, bglow = self.buy.frame(t, max(buy_p, 0))
                kc.compose(cv, c['cx'], by, self.btn_shell, bface * (1 + .2 * max(buy_p, 0)), bglow, self.buy_tint, t, press=max(buy_p, 0))
            else:
                kc.compose(cv, c['cx'], by, self.btn_shell, self.dark_face(self.btn_shell, None), np.zeros((self.btn_shell.face_h, self.btn_shell.face_w), F32),
                           {'rim': hex_rgb('#2a3a6a'), 'shadow': hex_rgb('#070b18'), 'highlight': hex_rgb('#8fa8e0')}, t)
            overlays.append((self.coin.resize((26, 26), Image.LANCZOS), c['cx'] - 70, by - 18))
            texts.append((c['cx'] + 14, by - 4, c['price'], 24, (255, 255, 255)))
        # --- currency HUD (top-left), counts down after the purchase
        de = ev('currency_debit')
        u = np.clip((t - de['t']) / de['dur'], 0, 1)
        val = int(round(de['from'] + (de['to'] - de['from']) * (1 - (1 - u) ** 3)))
        flash = math.exp(-max(t - de['t'], 0) * 5) if t >= de['t'] else 0
        hud = (28, 18, 300, 64)
        yy0, xx0 = np.mgrid[hud[1]:hud[3], hud[0]:hud[2]].astype(F32)
        d = kc.sd_round_rect(xx0 - (hud[0] + hud[2]) / 2, yy0 - (hud[1] + hud[3]) / 2, (hud[2] - hud[0]) / 2, (hud[3] - hud[1]) / 2, 14)
        m = kc.cover(d)[..., None]; ink = (kc.cover(d) * (1 - kc.cover(d + 3)))[..., None]
        reg = cv[hud[1]:hud[3], hud[0]:hud[2]]
        reg[:] = reg * (1 - m) + hex_rgb('#0b1430') * m
        reg[:] = reg * (1 - ink) + hex_rgb('#010204') * ink
        overlays.append((self.hud_coin, hud[0] + 10 + (4 if self.hierarchy else 0), hud[1] + 1 + (4 if self.hierarchy else 0)))
        texts.append((hud[0] + 62, (hud[1] + hud[3]) // 2, f'{val:,}', 28, (255, int(220 - 80 * flash), int(74 - 40 * flash)), 'lm'))
        # --- inventory
        rv = ev('item_reveal')['t']
        rp, _ = press_curve(t - rv)
        for k, s in enumerate(self.slots):
            is_new = k == self.new_slot
            if is_new and t >= rv - .2:
                face, glow = self.slot_mat.frame(t, max(rp, 0))
                tint = M.MoltenCore.tint(); tint['rim'] = hex_rgb(RARITY['legendary'])
                calm = 1.0 if t < ev('settle')['t'] else .85
                kc.compose(cv, s['cx'], s['cy'], self.slot_shell, face * calm, glow, tint, t, press=max(rp, 0))
                if t >= rv + .12:
                    sc = 1 + .18 * math.exp(-(t - rv - .12) * 9) * math.cos((t - rv - .12) * 20)
                    ic = icon('sword', int(56 * sc))
                    overlays.append((ic, s['cx'] - ic.width // 2, s['cy'] - 4 - ic.height // 2))
            else:
                rar = s['rar']
                tint = {'rim': hex_rgb(RARITY[rar]) if rar else hex_rgb('#1e2a50'), 'shadow': hex_rgb('#070b18'), 'highlight': hex_rgb('#9fb4e8')}
                kc.compose(cv, s['cx'], s['cy'], self.slot_shell, self.dark_face(self.slot_shell, rar), np.zeros((self.slot_shell.face_h, self.slot_shell.face_w), F32), tint, t)
                if s['icon'] is not None:
                    overlays.append((s['icon'], s['cx'] - 28, s['cy'] - 32))
        texts.append(((self.R[0] + self.R[2]) // 2, 112, 'INVENTORY', 26, (255, 255, 255)))
        texts.append(((self.L[0] + self.L[2]) // 2, 112, 'SHOP', 26, (255, 255, 255)))
        filled = 9 + (1 if t >= rv + .12 else 0)          # the counter is part of 'what changed'
        texts.append(((self.R[0] + self.R[2]) // 2, 520, f'{filled} / 12 slots', 18, (170, 186, 220) if t < rv + .12 or t > rv + 1.2 else (255, 214, 120)))
        # --- taskbar
        sw = ev('tab_switch')['t']
        active = 'shop' if t < sw else 'bag'
        sp, _ = press_curve(t - sw)
        for tb in self.tabs:
            if tb['name'] == active:
                face, glow = self.tab_mat.frame(t, max(sp, 0) if active == 'bag' else 0)
                kc.compose(cv, tb['cx'], tb['cy'], self.tb_shell, face * .85, glow, M.Hydroglass.tint(), t, press=max(sp, 0))
            else:
                kc.compose(cv, tb['cx'], tb['cy'], self.tb_shell, self.dark_face(self.tb_shell, None), np.zeros((self.tb_shell.face_h, self.tb_shell.face_w), F32),
                           {'rim': hex_rgb('#24345f'), 'shadow': hex_rgb('#070b18'), 'highlight': hex_rgb('#9fb4e8')}, t)
            overlays.append((tb['icon'], tb['cx'] - 22, tb['cy'] - 26))
        img = Image.fromarray(np.clip(linear_to_srgb(cv) * 255 + .5, 0, 255).astype(np.uint8))
        for (ic, x, y) in overlays:
            img.alpha_composite(ic, (int(x), int(y))) if img.mode == 'RGBA' else img.paste(ic, (int(x), int(y)), ic)
        dr = ImageDraw.Draw(img)
        bt = ev('badge_pop')['t']
        if t >= bt and t < sw + .3:
            u = t - bt
            sc = 1 + .35 * math.exp(-u * 10) * math.cos(u * 26) if u < .6 else 1
            r = 13 * sc; bx, by = self.tabs[1]['cx'] + 30, self.tabs[1]['cy'] - 30
            dr.ellipse((bx - r, by - r, bx + r, by + r), fill=(255, 61, 90), outline=(6, 7, 12), width=3)
            text(dr, (bx, by), '1', int(17 * sc), stroke=2)
        for tx in texts:
            x, y, s, sz, col = tx[:5]
            text(dr, (x, y), s, sz, fill=col, stroke=3, anchor=tx[5] if len(tx) > 5 else 'mm')
        self.timing.append((time.perf_counter() - t0) * 1000)
        return np.asarray(img.convert('RGB'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--still', type=float, default=None)
    ap.add_argument('--no-hierarchy', action='store_true', help='control: every card and BUY button loud')
    a = ap.parse_args()
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    sc = Scene(hierarchy=not a.no_hierarchy)
    if a.still is not None:
        img = None
        for i in range(int(a.still * a.fps) + 1):
            img = sc.render(i / a.fps)
        Image.fromarray(img).save(out.with_suffix('.png')); print('still'); return
    total = int(a.seconds * a.fps)
    keep = {int(x * a.fps) for x in (1.0, 2.45, 3.9, 5.0, 6.7, 9.0)}
    stills = {}

    def gen():
        for i in range(total):
            f = sc.render(i / a.fps)
            if i in keep:
                stills[i] = f
            yield f
    n = encode(gen(), out.with_suffix('.mp4'), W, H, a.fps)
    make_gif(out.with_suffix('.mp4'), out.with_suffix('.gif'), width=560, fps=15, start=1.8, dur=6)
    ks = sorted(stills)
    sheet = Image.new('RGB', (W * 2, H * 3))
    for j, k in enumerate(ks):
        sheet.paste(Image.fromarray(stills[k]), ((j % 2) * W, (j // 2) * H))
    sheet.resize((W, int(H * 1.5)), Image.LANCZOS).save(out.with_name(out.name + '-sheet.png'), optimize=True)
    pr = probe(out.with_suffix('.mp4')); st = pr['streams'][0]
    meta = {'frames_rendered': n, 'mp4': st, 'events': EVENTS, 'offline_ms_per_frame_mean': round(float(np.mean(sc.timing)), 1),
            'note': 'Offline NumPy render; 60 fps is output cadence only. Hierarchy: one loud element per panel (HIERARCHY.md s13).'}
    out.with_suffix('.json').write_text(json.dumps(meta, indent=1))
    print(json.dumps({'frames': n, 'fps': st.get('avg_frame_rate'), 'ms': meta['offline_ms_per_frame_mean']}))


if __name__ == '__main__':
    main()
