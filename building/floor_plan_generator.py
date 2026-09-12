import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import matplotlib.font_manager as fm

fig, ax = plt.subplots(figsize=(20, 14))

WALL = "#1a1a1a"
FLOOR = "#efe9de"      # interior beige floor
GARAGE_FLOOR = "#d9d9d9"
PORCH_FLOOR = "#f4f1ea"
WET_FLOOR = "#e6ecf0"  # bathrooms
CLOSET_FLOOR = "#eee7da"

rooms = []  # list of dicts

def add_room(name, dims_label, x, y, w, h, area, floor=FLOOR, fontsize=10.5, name_fontsize=11.5, wall_lw=2.4):
    rooms.append(dict(name=name, dims=dims_label, x=x, y=y, w=w, h=h, area=area,
                       floor=floor, fontsize=fontsize, name_fontsize=name_fontsize, wall_lw=wall_lw))

# ---------------------------------------------------------------
# GARAGE (2-car)
add_room("GARAGE\n(2 CARS)", "24' x 24'", 0, 0, 24, 24, 576, floor=GARAGE_FLOOR, name_fontsize=13)

# HALLWAY / MUDROOM (circulation spine connecting garage to house)
add_room("MUDROOM /\nHALLWAY", "10' x 24'", 24, 0, 10, 24, 240, name_fontsize=10)

# LIVING ROOM
add_room("LIVING ROOM", "19' x 18'", 0, 24, 19, 18, 342, name_fontsize=13)

# KITCHEN
add_room("KITCHEN", "15' x 18'", 19, 24, 15, 18, 270, name_fontsize=13)

# COVERED PORCH (back)
add_room("COVERED PORCH", "34' x 6'", 0, 42, 34, 6, 204, floor=PORCH_FLOOR, name_fontsize=11)

# ---------------- BEDROOM WING (x: 34 -> 88, y: 0 -> 26) ----------------
# Regular Suite 1 - Bedroom 2
add_room("BEDROOM 2", "12' x 13'", 34, 0, 12, 13, 156)
add_room("BATH 2", "6' x 7'", 46, 0, 6, 7, 42, floor=WET_FLOOR, fontsize=8.5, name_fontsize=9)
add_room("CLOSET", "6' x 6'", 46, 7, 6, 6, 36, floor=CLOSET_FLOOR, fontsize=8, name_fontsize=8.5)

# Regular Suite 2 - Bedroom 3
add_room("BEDROOM 3", "12' x 13'", 52, 0, 12, 13, 156)
add_room("BATH 3", "6' x 7'", 64, 0, 6, 7, 42, floor=WET_FLOOR, fontsize=8.5, name_fontsize=9)
add_room("CLOSET", "6' x 6'", 64, 7, 6, 6, 36, floor=CLOSET_FLOOR, fontsize=8, name_fontsize=8.5)

# Regular Suite 3 - Bedroom 4
add_room("BEDROOM 4", "12' x 13'", 34, 13, 12, 13, 156)
add_room("BATH 4", "6' x 7'", 46, 19, 6, 7, 42, floor=WET_FLOOR, fontsize=8.5, name_fontsize=9)
add_room("CLOSET", "6' x 6'", 46, 13, 6, 6, 36, floor=CLOSET_FLOOR, fontsize=8, name_fontsize=8.5)

# Regular Suite 4 - Bedroom 5
add_room("BEDROOM 5", "12' x 13'", 52, 13, 12, 13, 156)
add_room("BATH 5", "6' x 7'", 64, 19, 6, 7, 42, floor=WET_FLOOR, fontsize=8.5, name_fontsize=9)
add_room("CLOSET", "6' x 6'", 64, 13, 6, 6, 36, floor=CLOSET_FLOOR, fontsize=8, name_fontsize=8.5)

# Master Suite (2x regular bedroom / closet / bath)
add_room("MASTER BEDROOM", "12' x 26'", 70, 0, 12, 26, 312, name_fontsize=12)
add_room("MASTER BATH", "6' x 14'", 82, 0, 6, 14, 84, floor=WET_FLOOR, fontsize=9.5, name_fontsize=10)
add_room("MASTER\nCLOSET", "6' x 12'", 82, 14, 6, 12, 72, floor=CLOSET_FLOOR, fontsize=9, name_fontsize=9.5)

TOTAL_AREA = sum(r["area"] for r in rooms)

# ---------------------------------------------------------------
# DRAW ROOMS
for r in rooms:
    rect = patches.Rectangle((r["x"], r["y"]), r["w"], r["h"],
                              facecolor=r["floor"], edgecolor=WALL, linewidth=r["wall_lw"], zorder=2)
    ax.add_patch(rect)
    cx, cy = r["x"] + r["w"]/2, r["y"] + r["h"]/2
    ax.text(cx, cy + r["h"]*0.06, r["name"], ha="center", va="center",
             fontsize=r["name_fontsize"], fontweight="bold", color="#111111", zorder=4)
    ax.text(cx, cy - r["h"]*0.16, r["dims"], ha="center", va="center",
             fontsize=r["fontsize"], color="#333333", zorder=4)

# GARAGE hatch lines (floor texture)
for gx in range(1, 24, 2):
    ax.plot([gx, gx], [0.5, 23.5], color="#bbbbbb", lw=0.6, zorder=1)

# COVERED PORCH texture (vertical plank lines)
for px in range(1, 34, 2):
    ax.plot([px, px], [42.3, 47.7], color="#d8d2c4", lw=0.6, zorder=1)

# ---------------------------------------------------------------
# OUTER BOLD OUTLINE (overall footprint, L-shape)
outline = Path([
    (0, 0), (24, 0), (24, 0), (88, 0), (88, 26), (70, 26), (70, 42),
    (0, 42), (0, 0)
])
outer_pts = [
    (0, 0), (88, 0), (88, 26), (34, 26), (34, 42), (0, 42), (0, 0)
]
xs = [p[0] for p in outer_pts]
ys = [p[1] for p in outer_pts]
ax.plot(xs, ys, color=WALL, lw=4.0, zorder=5, solid_joinstyle="miter")

# Interior wing separators drawn already via individual room edges (zorder 2)
# Re-draw a few key structural walls a bit bolder for clarity
bold_walls = [
    [(24, 0), (24, 24)],      # garage/hallway wall
    [(34, 0), (34, 42)],      # hallway-kitchen / bedroom wing separation
    [(0, 24), (34, 24)],      # living-kitchen / garage-hallway separation
    [(19, 24), (19, 42)],     # living / kitchen divider
]
for (x1, y1), (x2, y2) in bold_walls:
    ax.plot([x1, x2], [y1, y2], color=WALL, lw=3.0, zorder=5)

# ---------------------------------------------------------------
# DOOR SWINGS (simple quarter-circle arcs) for a few key doors
def door(x, y, w, hinge="left", swing="up"):
    """Draw a simple door opening + swing arc."""
    from matplotlib.patches import Arc
    if hinge == "left":
        cx, cy = x, y
    else:
        cx, cy = x + w, y
    ax.add_patch(Arc((cx, cy), 2*w, 2*w, theta1=0 if swing=="up" else 180,
                      theta2=90 if swing=="up" else 270, color="#555555", lw=1.0, zorder=3))

door(19, 24, 2.6, hinge="left", swing="up")     # living/kitchen doorway (decorative)
door(34, 5, 2.6, hinge="left", swing="up")      # hallway -> bedroom wing
door(2, 24, 2.6, hinge="left", swing="up")      # garage -> hallway

# ---------------------------------------------------------------
# TITLE + TOTALS
ax.text(44, 50.5, "5-BEDROOM / 5-BATH / 5-CLOSET SINGLE-STORY HOME",
         ha="center", va="center", fontsize=17, fontweight="bold", color="#111111")
ax.text(44, 48.7, f"Total Living + Garage + Porch Area \u2248 {TOTAL_AREA:,.0f} sq ft   |   Scale in feet",
         ha="center", va="center", fontsize=11, color="#333333")

# North arrow
ax.annotate("N", xy=(85, 46), xytext=(85, 43.5), ha="center", va="center",
            fontsize=11, fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#333333"))

ax.set_xlim(-3, 92)
ax.set_ylim(-3, 53)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("outputs/floor_plan.png", dpi=220, facecolor="white", bbox_inches="tight")
print("TOTAL AREA:", TOTAL_AREA)
for r in rooms:
    print(f"{r['name']:20s} {r['dims']:10s} {r['area']:>6.0f} sqft")
