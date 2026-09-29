#!/usr/bin/env python3
"""Draws the Batcomputer logo and writes every size the site and phone install need.

  python3 tools/make_logo.py [output_dir]      # default: batcomputer-web/

The mark: a chamfered HUD frame (the console), a blocky terminal "B" (the name), and a scan-line with a bright
sweep along the bottom (the STANDBY line that runs across the real app). Amber on near-black, like the app.
Needs Pillow:  pip install pillow
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "batcomputer-web")

BG, AMBER, HOT, DIM, LINE = "#0a0705", "#e0921f", "#ffc45a", "#6d4712", "#3a2308"

# --- geometry, in a 512 x 512 box -----------------------------------------------------------------------
FRAME = (64, 64, 448, 448); CH = 60                 # chamfered square and its cut corners
CELL, GAP = 34, 6                                    # the B is 5 x 7 blocks
B_ROWS = ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."]
B_W = 5 * CELL + 4 * GAP; B_H = 7 * CELL + 6 * GAP
B_X, B_Y = 256 - B_W // 2, 252 - B_H // 2 - 10
SWEEP_Y = 396

def frame_poly(box, ch):
    x0, y0, x1, y1 = box
    return [(x0 + ch, y0), (x1 - ch, y0), (x1, y0 + ch), (x1, y1 - ch), (x1 - ch, y1), (x0 + ch, y1), (x0, y1 - ch), (x0, y0 + ch)]

def b_cells():
    for r, row in enumerate(B_ROWS):
        for c, ch in enumerate(row):
            if ch == "#":
                x = B_X + c * (CELL + GAP); y = B_Y + r * (CELL + GAP)
                yield x, y, x + CELL, y + CELL

def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def draw_mark(size, bg=True, rounded=True, scale=1.0, glow=True):
    """Returns an RGBA image of the mark. scale < 1 leaves extra margin (used for the phone 'maskable' icon)."""
    S = 4                                            # supersample, then shrink for smooth edges
    N = 512 * S
    def render(layer_fn):
        im = Image.new("RGBA", (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(im); layer_fn(d); return im
    k = S * scale; off = (512 * S - 512 * k) / 2
    def P(v): return v * k + off
    def poly(d, pts, **kw): d.polygon([(P(x), P(y)) for x, y in pts], **kw)
    def rect(d, b, r=0, **kw):
        d.rounded_rectangle([P(b[0]), P(b[1]), P(b[2]), P(b[3])], radius=r * k, **kw)
    def line(d, pts, w, fill): d.line([(P(x), P(y)) for x, y in pts], fill=fill, width=int(w * k))

    def bright(d):
        # frame
        pts = frame_poly(FRAME, CH); pp = [(P(x), P(y)) for x, y in pts]
        d.line(pp + [pp[0], pp[1]], fill=AMBER, width=int(13 * k), joint="curve")
        ins = frame_poly((FRAME[0] + 26, FRAME[1] + 26, FRAME[2] - 26, FRAME[3] - 26), CH - 14)
        ip = [(P(x), P(y)) for x, y in ins]; d.line(ip + [ip[0], ip[1]], fill=DIM, width=int(3 * k), joint="curve")
        # the B, brighter toward the top
        for x0, y0, x1, y1 in b_cells():
            t = (y0 - B_Y) / B_H; c = tuple(int(a + (b - a) * t) for a, b in zip(hexrgb(HOT), hexrgb(AMBER)))
            rect(d, (x0, y0, x1, y1), r=5, fill=c)
        # scan line and the bright sweep
        line(d, [(118, SWEEP_Y), (394, SWEEP_Y)], 5, DIM)
        line(d, [(236, SWEEP_Y), (318, SWEEP_Y)], 6, HOT)
        cx, cy, r = P(318), P(SWEEP_Y), 9 * k
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=HOT)
    top = render(bright)
    canvas = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    if bg:
        def back(d):
            if rounded: d.rounded_rectangle([0, 0, N - 1, N - 1], radius=112 * S, fill=BG)
            else: d.rectangle([0, 0, N, N], fill=BG)
        canvas = Image.alpha_composite(canvas, render(back))
    if glow:
        g = top.filter(ImageFilter.GaussianBlur(14 * S)); a = g.split()[3].point(lambda v: min(255, int(v * 0.9))); g.putalpha(a)
        canvas = Image.alpha_composite(canvas, g)
        g2 = top.filter(ImageFilter.GaussianBlur(5 * S)); a2 = g2.split()[3].point(lambda v: int(v * 0.6)); g2.putalpha(a2)
        canvas = Image.alpha_composite(canvas, g2)
    canvas = Image.alpha_composite(canvas, top)
    return canvas.resize((512, 512), Image.LANCZOS)

def mono(size):
    for p in ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/SFNSMono.ttf", "/Library/Fonts/Courier New Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size, index=1) if p.endswith(".ttc") else ImageFont.truetype(p, size)
            except Exception:
                try: return ImageFont.truetype(p, size)
                except Exception: pass
    return ImageFont.load_default()

def spaced(d, xy, text, font, fill, spacing):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill); x += d.textlength(ch, font=font) + spacing
    return x

def lockup(w, h, tagline=None):
    """mark + wordmark on the app's dark background (used for the GitHub social preview and a README banner)"""
    im = Image.new("RGBA", (w, h), BG)
    sl = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sd = ImageDraw.Draw(sl)
    for y in range(0, h, 4): sd.line([(0, y), (w, y)], fill=(255, 190, 90, 9), width=1)   # faint scanlines
    im = Image.alpha_composite(im, sl); d = ImageDraw.Draw(im)
    m = draw_mark(0, bg=False, glow=True).resize((int(h * .62),) * 2, Image.LANCZOS)
    mx = int(w * .07); my = (h - m.height) // 2; im.alpha_composite(m, (mx, my))
    tx = mx + m.width + int(h * .07); big = mono(int(h * .15)); small = mono(int(h * .07)); tiny = mono(int(h * .045))
    ty = my + int(m.height * .18)
    spaced(d, (tx, ty), "BATCOMPUTER", big, HOT, int(h * .012))
    spaced(d, (tx, ty + int(h * .19)), "MK-IV", small, AMBER, int(h * .02))
    if tagline: spaced(d, (tx, ty + int(h * .33)), tagline, tiny, "#a5701f", int(h * .006))
    d.line([(tx, ty + int(h * .17)), (tx + int(w * .42), ty + int(h * .17))], fill=LINE, width=2)
    return im.convert("RGB")

SVG_DEFS = f'''<defs><filter id="g" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{HOT}"/><stop offset="1" stop-color="{AMBER}"/></linearGradient></defs>'''

def svg_mark(bg=True):
    pts = " ".join(f"{x},{y}" for x, y in frame_poly(FRAME, CH))
    ins = " ".join(f"{x},{y}" for x, y in frame_poly((FRAME[0] + 26, FRAME[1] + 26, FRAME[2] - 26, FRAME[3] - 26), CH - 14))
    cells = "".join(f'<rect x="{x0}" y="{y0}" width="{CELL}" height="{CELL}" rx="5"/>' for x0, y0, x1, y1 in b_cells())
    back = f'<rect width="512" height="512" rx="112" fill="{BG}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Batcomputer">{SVG_DEFS}{back}'
            f'<g filter="url(#g)"><polygon points="{pts}" fill="none" stroke="{AMBER}" stroke-width="13" stroke-linejoin="round"/>'
            f'<polygon points="{ins}" fill="none" stroke="{DIM}" stroke-width="3" stroke-linejoin="round"/>'
            f'<g fill="url(#bg)">{cells}</g>'
            f'<line x1="118" y1="{SWEEP_Y}" x2="394" y2="{SWEEP_Y}" stroke="{DIM}" stroke-width="5" stroke-linecap="round"/>'
            f'<line x1="236" y1="{SWEEP_Y}" x2="318" y2="{SWEEP_Y}" stroke="{HOT}" stroke-width="6" stroke-linecap="round"/>'
            f'<circle cx="318" cy="{SWEEP_Y}" r="9" fill="{HOT}"/></g></svg>')

def svg_lockup():
    inner = svg_mark(bg=False).replace('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Batcomputer">', "").replace("</svg>", "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" role="img" aria-label="Batcomputer MK-IV"><rect width="1200" height="400" fill="{BG}"/>'
            f'<g transform="translate(40,40) scale(.625)">{inner}</g>'
            f'<text x="420" y="205" font-family="\'Share Tech Mono\',\'IBM Plex Mono\',Menlo,Consolas,monospace" font-size="110" letter-spacing="10" fill="{HOT}">BATCOMPUTER</text>'
            f'<text x="424" y="285" font-family="\'Share Tech Mono\',\'IBM Plex Mono\',Menlo,Consolas,monospace" font-size="52" letter-spacing="14" fill="{AMBER}">MK-IV</text></svg>')

def main():
    icons = os.path.join(OUT, "icons"); logo = os.path.join(OUT, "logo")
    os.makedirs(icons, exist_ok=True); os.makedirs(logo, exist_ok=True)
    full = draw_mark(512)
    full.resize((512, 512), Image.LANCZOS).save(os.path.join(icons, "icon-512.png"))
    full.resize((192, 192), Image.LANCZOS).save(os.path.join(icons, "icon-192.png"))
    # phone home-screen icons get their own corner rounding, so they want a square, full-bleed background
    sq = draw_mark(512, rounded=False)
    sq.resize((180, 180), Image.LANCZOS).convert("RGB").save(os.path.join(icons, "apple-touch-icon.png"))
    # 'maskable': Android crops icons to circles/squircles, so the mark stays inside the safe centre 60%
    draw_mark(512, rounded=False, scale=.66).save(os.path.join(icons, "icon-maskable-512.png"))
    draw_mark(512, glow=False).resize((48, 48), Image.LANCZOS).save(os.path.join(icons, "favicon-48.png"))
    draw_mark(512, glow=False).resize((32, 32), Image.LANCZOS).save(os.path.join(icons, "favicon-32.png"))
    open(os.path.join(icons, "favicon.svg"), "w").write(svg_mark())
    open(os.path.join(logo, "logo-mark.svg"), "w").write(svg_mark())
    open(os.path.join(logo, "logo-mark-transparent.svg"), "w").write(svg_mark(bg=False))
    open(os.path.join(logo, "logo-wordmark.svg"), "w").write(svg_lockup())
    full.save(os.path.join(logo, "logo-mark.png"))
    draw_mark(512, bg=False).save(os.path.join(logo, "logo-mark-transparent.png"))
    lockup(1200, 400).save(os.path.join(logo, "logo-wordmark.png"))
    lockup(1280, 640, "VOICE-FIRST PROJECT CONSOLE").save(os.path.join(logo, "social-preview.png"))
    print("logo assets written to", OUT)

if __name__ == "__main__":
    main()
