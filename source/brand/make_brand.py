import json, math
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

G = json.load(open("../icons/glyphs.json"))


def hua(cx, cy, height, fill):
    d, (x0, y0, x1, y1), _, _ = G["hua"]
    s = height / (y1 - y0)
    return f'<path d="{d}" fill="{fill}" transform="translate({cx - (x0 + x1) / 2 * s:.2f} {cy + (y0 + y1) / 2 * s:.2f}) scale({s:.5f} {-s:.5f})"/>'


def hexpts(cx, cy, r):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in (0, 60, 120, 180, 240, 300)]


def hexpath(cx, cy, r, tail = False):
    p = hexpts(cx, cy, r)
    if not tail:
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in p) + " Z"
    a, b = p[2], p[3]
    lerp = lambda t: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    t1, t2 = lerp(0.12), lerp(0.55)
    tip = (cx - r * 0.98, cy + r * 1.12)
    seq = [p[0], p[1], p[2], t1, tip, t2, p[3], p[4], p[5]]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in seq) + " Z"


def spark(cx, cy, r):
    k = r * 0.22
    pts = [(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k), (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"


def mark(fg, bg, ox = 0, oy = 0, s = 1.0):
    cx, cy, r = 212, 300, 150
    layers = []
    for i, (dx, dy, w, op) in enumerate([(84, -84, 13, 0.45), (42, -42, 15, 0.75)]):
        layers.append(f'<path d="{hexpath(cx + dx, cy + dy, r)}" fill="{bg}" stroke="{fg}" stroke-width="{w}" stroke-linejoin="round" opacity="{op}"/>')
    front = f'<path d="{hexpath(cx, cy, r, True)}" fill="{fg}" stroke="{bg}" stroke-width="24" stroke-linejoin="round" paint-order="stroke"/>'
    sp = f'<path d="{spark(424, 92, 34)}" fill="{fg}"/><path d="{spark(470, 160, 15)}" fill="{fg}"/>'
    return f'<g transform="translate({ox} {oy}) scale({s})">{"".join(layers)}{front}{hua(cx, cy + 4, 150, bg)}{sp}</g>'


def icon(rx = 112, pad = 0):
    bg, fg = "#111111", "#ffffff"
    vb = f"{-pad} {-pad} {512 + 2 * pad} {512 + 2 * pad}"
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"><rect x="{-pad}" y="{-pad}" width="{512 + 2 * pad}" height="{512 + 2 * pad}" rx="{rx}" fill="{bg}"/>{mark(fg, bg, 22, 26, 0.9)}</svg>\n'


f = TTFont("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf")
gs = f.getGlyphSet(); cmap = f.getBestCmap()
upm = f["head"].unitsPerEm
xh = f["OS/2"].sxHeight


def wordmark():
    pen = SVGPathPen(gs)
    x = 0
    hexo = None
    for i, ch in enumerate("polyling"):
        g = cmap[ord(ch)]
        if i == 1:
            w = gs[g].width
            hexo = (x + w / 2, xh / 2, xh * 0.53, w)
            x += w - 20
            continue
        gs[g].draw(TransformPen(pen, (1, 0, 0, 1, x, 0)))
        x += gs[g].width - 20
    return pen.getCommands(), x, hexo


WD, WW, HEXO = wordmark()


def word_svg(fill, height, ox, oy):
    s = height / upm
    hx, hy, hr, _ = HEXO
    pts = hexpts(hx, hy, hr)
    inner = hexpts(hx, hy, hr * 0.47)
    hp = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + " Z M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in reversed(inner)) + " Z"
    return f'<g transform="translate({ox:.1f} {oy:.1f}) scale({s:.5f} {-s:.5f})" fill="{fill}"><path d="{WD}"/><path d="{hp}" fill-rule="evenodd"/></g>', WW * s


open("icon.svg", "w").write(icon())
open("icon-maskable.svg", "w").write(icon(rx = 0, pad = 64))

# mark alone (theme aware) for the in-app banner
open("mark-current.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">{mark("currentColor", "var(--banner-bg, #111)")}</svg>')

# wordmark-only path for the in-app banner (currentColor)
wsvg, ww = word_svg("currentColor", 100, 0, 78)
open("wordmark-current.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -2 {ww:.0f} 104">{wsvg}</svg>')
json.dump({"ww": ww}, open("dims.json", "w"))


def banner(W, H, title_h, path):
    bg, fg = "#111111", "#ffffff"
    ms = H * 0.78 / 512
    mx, my = H * 0.16, H * 0.1
    tx = mx + 512 * ms + H * 0.08
    wsvg, ww = word_svg(fg, title_h, tx, H * 0.5 + title_h * 0.08)
    sub_y = H * 0.5 + title_h * 0.08 + title_h * 0.5
    langs = "台山話 · 廣東話 · English · 普通話 · Español · Français · Deutsch"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<rect width="{W}" height="{H}" fill="{bg}"/>
<g opacity="0.08" stroke="{fg}" stroke-width="2" fill="none">{"".join(f'<path d="{hexpath(W - 120 - i * 150, 60 + (i % 2) * 90, 70)}"/>' for i in range(5))}{"".join(f'<path d="{hexpath(W - 45 - i * 150, H - 60 - (i % 2) * 80, 70)}"/>' for i in range(5))}</g>
{mark(fg, bg, mx, my, ms)}
{wsvg}
<text x="{tx + title_h * 0.04:.1f}" y="{sub_y:.1f}" fill="{fg}" font-family="Inter, sans-serif" font-weight="600" font-size="{title_h * 0.22:.1f}">Learn any language, word by word.</text>
<text x="{tx + title_h * 0.04:.1f}" y="{sub_y + title_h * 0.34:.1f}" fill="{fg}" fill-opacity="0.6" font-family="Inter, 'Noto Sans CJK TC', sans-serif" font-size="{title_h * 0.17:.1f}">{langs}</text>
</svg>'''
    open(path, "w").write(svg)


banner(1600, 480, 190, "banner.svg")
banner(1200, 630, 200, "og.svg")
print("ok", WW, HEXO)


import re
m = mark("currentColor", "#BGC")
m = m.replace('fill="#BGC"', 'class="bgf"').replace('stroke="#BGC"', 'class="bgs"')
m = re.sub(r'class="bgf" stroke="currentColor"', 'class="bgf" stroke="currentColor"', m)
open("mark-inline.svg", "w").write(f'<svg class="b-mark" viewBox="0 0 512 512" aria-hidden="true">{m}</svg>')
wsvg, ww = word_svg("currentColor", 100, 0, 78)
open("word-inline.svg", "w").write(f'<svg class="b-word" viewBox="0 -2 {ww:.0f} 104" role="img" aria-label="Polyling">{wsvg}</svg>')
