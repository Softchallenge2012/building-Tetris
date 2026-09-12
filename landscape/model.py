"""
Modern infill house — 3D massing model + orthographic elevations
Site: flat urban infill lot between two Victorian-era homes.
Design: two-story cantilevered volume, flat roofs, charcoal fiber-cement
cladding, vertical wood slat accents, floor-to-ceiling glazing, attached
carport with green roof strip.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image, ImageOps
import os

OUT = "images/"

# ---------------------------------------------------------------
# MATERIAL PALETTE
# ---------------------------------------------------------------
CHARCOAL   = "#33363a"   # dark fiber-cement panel cladding (upper mass)
LIGHT_STUCCO = "#e8e5df" # ground floor render / stucco
WOOD       = "#a97a4f"   # vertical cedar slat accent
WOOD_DARK  = "#8a6239"
GLASS      = "#9fc4d1"
GLASS_EDGE = "#20242a"
ROOF_CAP   = "#202225"
CONCRETE   = "#c9c6be"   # plinth / base
GREEN_ROOF = "#5c7a4a"   # carport green roof
GROUND     = "#8fae6b"
DOOR       = "#20242a"

def box(x0, x1, y0, y1, z0, z1):
    """Return the 6 faces of an axis-aligned box as lists of (x,y,z) verts."""
    p = {
        'lbb': (x0, y0, z0), 'rbb': (x1, y0, z0), 'rfb': (x1, y1, z0), 'lfb': (x0, y1, z0),
        'lbt': (x0, y0, z1), 'rbt': (x1, y0, z1), 'rft': (x1, y1, z1), 'lft': (x0, y1, z1),
    }
    faces = {
        'front': [p['lfb'], p['rfb'], p['rft'], p['lft']],   # +y face
        'back':  [p['lbb'], p['rbb'], p['rbt'], p['lbt']],   # -y face
        'right': [p['rbb'], p['rfb'], p['rft'], p['rbt']],   # +x face
        'left':  [p['lbb'], p['lfb'], p['lft'], p['lbt']],   # -x face
        'top':   [p['lft'], p['rft'], p['rbt'], p['lbt']],   # +z face
        'bottom':[p['lfb'], p['rfb'], p['rbb'], p['lbb']],   # -z face
    }
    return faces

def add_box(ax, x0, x1, y0, y1, z0, z1, color, edge="#1a1a1a", lw=0.4,
            alpha=1.0, faces_only=None):
    faces = box(x0, x1, y0, y1, z0, z1)
    use = faces_only if faces_only else faces.keys()
    polys = [faces[f] for f in use]
    coll = Poly3DCollection(polys, facecolor=color, edgecolor=edge,
                             linewidths=lw, alpha=alpha)
    ax.add_collection3d(coll)

def add_panel(ax, verts, color, edge="#1a1a1a", lw=0.5, alpha=1.0):
    coll = Poly3DCollection([verts], facecolor=color, edgecolor=edge,
                             linewidths=lw, alpha=alpha)
    ax.add_collection3d(coll)

def vert_rect(axis_fixed, fixed_val, u0, u1, v0, v1, order='xy_at_z'):
    pass  # helper not needed; panels built inline below

# ---------------------------------------------------------------
# BUILD GEOMETRY  (units: meters)
# Site: x = width (0 left .. 14 right), y = depth (0 street/front .. 12 rear/back)
# ---------------------------------------------------------------
def build(ax):
    # Ground / lot patch (kept close to the footprint so mplot3d's
    # painter's-algorithm depth sort doesn't misorder it against the house)
    add_panel(ax, [(-2,-3,-0.02), (15.5,-3,-0.02), (15.5,9.5,-0.02), (-2,9.5,-0.02)],
              GROUND, edge="none", alpha=1.0)

    # --- Concrete plinth / base (slightly larger footprint, low) ---
    add_box(ax, 0, 10.2, 0.2, 8.2, 0, 0.35, CONCRETE)

    # --- Ground floor volume (light stucco), set back slightly from plinth edge ---
    gx0, gx1, gy0, gy1, gz0, gz1 = 0.2, 10.0, 0.4, 8.0, 0.35, 3.3
    add_box(ax, gx0, gx1, gy0, gy1, gz0, gz1, LIGHT_STUCCO)

    # Floor-to-ceiling glazing strip on front (street) face, ground floor
    gw0, gw1 = 2.4, 8.6
    add_panel(ax, [(gw0, gy0-0.02, 0.5), (gw1, gy0-0.02, 0.5),
                   (gw1, gy0-0.02, 3.0), (gw0, gy0-0.02, 3.0)], GLASS,
              edge=GLASS_EDGE, lw=1.0, alpha=0.85)
    # mullions
    for mx in np.linspace(gw0, gw1, 7):
        add_panel(ax, [(mx, gy0-0.03, 0.5), (mx+0.03, gy0-0.03, 0.5),
                       (mx+0.03, gy0-0.03, 3.0), (mx, gy0-0.03, 3.0)],
                  GLASS_EDGE, edge="none")

    # Entry door (recessed, dark) on left portion of front, ground floor
    add_panel(ax, [(0.9, gy0-0.02, 0.5), (1.9, gy0-0.02, 0.5),
                   (1.9, gy0-0.02, 2.6), (0.9, gy0-0.02, 2.6)], DOOR,
              edge="#000000", lw=1.0)

    # --- Vertical cedar slat accent wall (left side, wraps corner near entry) ---
    n_slats = 14
    slat_w, gap = 0.10, 0.09
    x_start = 0.25
    for i in range(n_slats):
        xs = x_start + i * (slat_w + gap)
        if xs > 2.0:
            break
        add_box(ax, xs, xs+slat_w, gy0-0.05, gy0+0.02, 0.35, 3.3, WOOD,
                edge="none")

    # --- Second floor volume — cantilevers forward (toward street, -y) and
    #     left (-x) past the ground floor, dark charcoal cladding ---
    fx0, fx1, fy0, fy1, fz0, fz1 = -1.2, 9.4, -0.9, 7.6, 3.3, 6.5
    add_box(ax, fx0, fx1, fy0, fy1, fz0, fz1, CHARCOAL)

    # Roof parapet cap (thin dark trim) on upper volume
    add_box(ax, fx0-0.05, fx1+0.05, fy0-0.05, fy1+0.05, fz1, fz1+0.18, ROOF_CAP)

    # Ribbon window on upper floor, front face
    rw0, rw1 = -0.7, 8.9
    add_panel(ax, [(rw0, fy0-0.02, 4.0), (rw1, fy0-0.02, 4.0),
                   (rw1, fy0-0.02, 5.7), (rw0, fy0-0.02, 5.7)], GLASS,
              edge=GLASS_EDGE, lw=1.0, alpha=0.85)
    for mx in np.linspace(rw0, rw1, 11):
        add_panel(ax, [(mx, fy0-0.03, 4.0), (mx+0.03, fy0-0.03, 4.0),
                       (mx+0.03, fy0-0.03, 5.7), (mx, fy0-0.03, 5.7)],
                  GLASS_EDGE, edge="none")

    # Upper floor window on the RIGHT side (x=fx1 face)
    add_panel(ax, [(fx1+0.02, 1.0, 4.0), (fx1+0.02, 6.6, 4.0),
                   (fx1+0.02, 6.6, 5.7), (fx1+0.02, 1.0, 5.7)], GLASS,
              edge=GLASS_EDGE, lw=1.0, alpha=0.85)

    # Upper floor window on the BACK face
    add_panel(ax, [(0.5, fy1+0.02, 4.0), (6.0, fy1+0.02, 4.0),
                   (6.0, fy1+0.02, 5.7), (0.5, fy1+0.02, 5.7)], GLASS,
              edge=GLASS_EDGE, lw=1.0, alpha=0.85)

    # Ground floor window on the BACK face (rear yard)
    add_panel(ax, [(1.0, gy1+0.02, 0.6), (5.0, gy1+0.02, 0.6),
                   (5.0, gy1+0.02, 2.8), (1.0, gy1+0.02, 2.8)], GLASS,
              edge=GLASS_EDGE, lw=1.0, alpha=0.85)
    # back door (patio)
    add_panel(ax, [(6.2, gy1+0.02, 0.5), (7.6, gy1+0.02, 0.5),
                   (7.6, gy1+0.02, 2.6), (6.2, gy1+0.02, 2.6)], GLASS,
              edge=DOOR, lw=1.2, alpha=0.9)

    # --- Slim steel support column under the cantilever (front-left corner) ---
    add_box(ax, -0.65, -0.45, -0.5, -0.3, 0.35, 3.3, "#4a4d51")

    # --- Attached carport / flat-roof volume to the right ---
    cx0, cx1, cy0, cy1, cz0, cz1 = 10.0, 14.4, 0.4, 6.4, 0, 2.9
    # slim steel posts
    for px in (cx0+0.3, cx1-0.3):
        for py in (cy0+0.3, cy1-0.3):
            add_box(ax, px-0.1, px+0.1, py-0.1, py+0.1, 0, cz1, "#4a4d51")
    # flat roof slab with green-roof cap
    add_box(ax, cx0-0.2, cx1+0.2, cy0-0.2, cy1+0.2, cz1, cz1+0.25, ROOF_CAP)
    add_box(ax, cx0-0.15, cx1+0.15, cy0-0.15, cy1+0.15, cz1+0.25, cz1+0.38,
            GREEN_ROOF)
    # low wood-slat screen wall along right edge of carport
    for i in range(18):
        xs = cx1 + 0.15
        ys = cy0 + i * 0.34
        if ys > cy1:
            break
        add_box(ax, xs, xs+0.08, ys, ys+0.06, 0, 1.1, WOOD_DARK, edge="none")

    # --- Thin roof overhang / canopy above entry, cantilevered from upper mass ---
    add_box(ax, 0.6, 2.3, -1.3, 0.5, 3.28, 3.42, ROOF_CAP)

    # --- Low landscape wall / planter along the street edge of the lot ---
    add_box(ax, -3.0, 10.6, -2.6, -2.2, 0, 0.55, CONCRETE)
    for i in range(6):
        add_box(ax, -2.6 + i*2.2, -2.6 + i*2.2 + 0.8, -2.55, -2.25, 0.55, 1.15,
                "#4c6b3a", edge="none")  # simple hedge boxes

def set_axes(ax, lim=(-6, 18, -5, 18, 0, 8)):
    ax.set_xlim(lim[0], lim[1])
    ax.set_ylim(lim[2], lim[3])
    ax.set_zlim(lim[4], lim[5])
    ax.set_box_aspect((lim[1]-lim[0], lim[3]-lim[2], lim[5]-lim[4]))
    ax.set_axis_off()

def render(elev, azim, fname, lim=(-6,18,-5,18,0,8), title=None):
    fig = plt.figure(figsize=(9,9), dpi=200)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_proj_type('ortho')
    # keep matplotlib's per-vertex depth sort for true elevations so
    # far-side elements don't bleed through near-side ones
    build(ax)
    set_axes(ax, lim)
    ax.view_init(elev=elev, azim=azim)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(os.path.join(OUT, fname), facecolor="white")
    plt.close(fig)

def autocrop(path, pad=20):
    im = Image.open(path).convert("RGB")
    bg = Image.new("RGB", im.size, (255,255,255))
    diff = ImageOps.invert(im.convert("L"))
    bbox = diff.getbbox()
    if bbox:
        l,t,r,b = bbox
        l = max(l-pad,0); t = max(t-pad,0)
        r = min(r+pad, im.size[0]); b = min(b+pad, im.size[1])
        im = im.crop((l,t,r,b))
    im.save(path)

# ---------------------------------------------------------------
# RENDER 5 VIEWS
# front = camera at -y looking toward +y
# back  = camera at +y looking toward -y
# right = camera at +x looking toward -x
# left  = camera at -x looking toward +x
# top   = camera looking straight down
# ---------------------------------------------------------------
views = [
    ("front.png",   0,  -90, "FRONT"),
    ("back.png",    0,   90, "BACK"),
    ("right.png",   0,    0, "RIGHT"),
    ("left.png",    0,  180, "LEFT"),
    ("top.png",    89.9, -90, "TOP-DOWN"),
]

for fname, elev, azim, label in views:
    render(elev, azim, fname)
    autocrop(os.path.join(OUT, fname))
    print("rendered", fname)

# Bonus perspective (not orthographic) for context
fig = plt.figure(figsize=(9,9), dpi=200)
ax = fig.add_subplot(111, projection='3d')
ax.computed_zorder = False
build(ax)
set_axes(ax)
ax.view_init(elev=22, azim=-55)
fig.patch.set_facecolor("white")
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
fig.savefig(os.path.join(OUT, "perspective.png"), facecolor="white")
plt.close(fig)
autocrop(os.path.join(OUT, "perspective.png"))
print("rendered perspective.png")

print("done")
