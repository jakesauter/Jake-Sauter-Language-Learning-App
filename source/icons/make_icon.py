import json

G = json.load(open("glyphs.json"))


def place(key, cx, cy, height, fill):
    d, (x0, y0, x1, y1), _, _ = G[key]
    s = height / (y1 - y0)
    tx = cx - (x0 + x1) / 2 * s
    ty = cy + (y0 + y1) / 2 * s
    return f'<path d="{d}" fill="{fill}" transform="translate({tx:.2f} {ty:.2f}) scale({s:.5f} {-s:.5f})"/>'


def bubble(x, y, w, h, r, tail):
    tx, ty, side = tail
    if side == "bl":
        return (f"M{x + r},{y} H{x + w - r} Q{x + w},{y} {x + w},{y + r} V{y + h - r} Q{x + w},{y + h} {x + w - r},{y + h} "
                f"H{x + 118} L{tx},{ty} L{x + 66},{y + h} H{x + r} Q{x},{y + h} {x},{y + h - r} V{y + r} Q{x},{y} {x + r},{y} Z")
    return (f"M{x + r},{y} H{x + w - r} Q{x + w},{y} {x + w},{y + r} V{y + h - r} Q{x + w},{y + h} {x + w - r},{y + h} "
            f"H{x + w - 52} L{tx},{ty} L{x + w - 104},{y + h} H{x + r} Q{x},{y + h} {x},{y + h - r} V{y + r} Q{x},{y} {x + r},{y} Z")


def icon(bg = "#111111", fg = "#ffffff", rx = 112, pad = 0):
    back = bubble(214, 66, 236, 178, 46, (448, 300, "br"))
    front = bubble(62, 186, 286, 236, 58, (88, 476, "bl"))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad} {-pad} {512 + 2 * pad} {512 + 2 * pad}">
  <rect x="0" y="0" width="512" height="512" rx="{rx}" fill="{bg}"/>
  <path d="{back}" fill="none" stroke="{fg}" stroke-width="22" stroke-linejoin="round"/>
  {place("Aa", 340, 136, 70, fg)}
  <path d="{front}" fill="{fg}" stroke="{bg}" stroke-width="26" stroke-linejoin="round" paint-order="stroke"/>
  {place("hua", 205, 304, 168, bg)}
</svg>
'''


open("icon.svg", "w").write(icon())
open("icon-maskable.svg", "w").write(icon(rx = 0, pad = 0).replace('viewBox="0 0 512 512"', 'viewBox="-64 -64 640 640"').replace('<rect x="0" y="0" width="512" height="512" rx="0"', '<rect x="-64" y="-64" width="640" height="640" rx="0"'))
print("ok")
