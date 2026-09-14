import matplotlib.pyplot as plt

from space import Space, window_count
from door import Door
from window import Window
from floorplan import FloorPlan

# =================================================================
# 1. STANDARD SIZES  (the "twice as big" rules live only here)
# =================================================================
REGULAR_BEDROOM = (12, 13)
MASTER_BEDROOM = (12, 26)     # 2x regular bedroom (same width, double depth)

REGULAR_CLOSET = (6, 6)
MASTER_CLOSET = (6, 12)       # 2x regular closet

REGULAR_BATH = (6, 7)
MASTER_BATH = (6, 14)         # 2x regular bath

WINDOW_SPACING = 6            # feet — every exterior wall gets a window at least this often

# =================================================================
# 2. CREATE ROOM (Space) INSTANCES  — what each room IS, not yet WHERE
# =================================================================
garage = Space("GARAGE\n(2 CARS)", (24, 24), category="garage")
hallway = Space("MUDROOM /\nHALLWAY", (10, 24), category="hallway")
living = Space("LIVING ROOM", (19, 18), category="living")
kitchen = Space("KITCHEN", (15, 18), category="kitchen")
porch = Space("COVERED PORCH", (34, 6), category="porch")

bedroom2 = Space("BEDROOM 2", REGULAR_BEDROOM, category="bedroom")
bath2 = Space("BATH 2", REGULAR_BATH, category="bath")
closet2 = Space("CLOSET", REGULAR_CLOSET, category="closet")

bedroom3 = Space("BEDROOM 3", REGULAR_BEDROOM, category="bedroom")
bath3 = Space("BATH 3", REGULAR_BATH, category="bath")
closet3 = Space("CLOSET", REGULAR_CLOSET, category="closet")

bedroom4 = Space("BEDROOM 4", REGULAR_BEDROOM, category="bedroom")
bath4 = Space("BATH 4", REGULAR_BATH, category="bath")
closet4 = Space("CLOSET", REGULAR_CLOSET, category="closet")

bedroom5 = Space("BEDROOM 5", REGULAR_BEDROOM, category="bedroom")
bath5 = Space("BATH 5", REGULAR_BATH, category="bath")
closet5 = Space("CLOSET", REGULAR_CLOSET, category="closet")

master_bedroom = Space("MASTER BEDROOM", MASTER_BEDROOM, category="bedroom")
master_bath = Space("MASTER BATH", MASTER_BATH, category="bath")
master_closet = Space("MASTER\nCLOSET", MASTER_CLOSET, category="closet")

# =================================================================
# 3. PLACE ROOMS (assign coordinates)
# =================================================================
garage.place(0, 0)
hallway.place(24, 0)
living.place(0, 24)
kitchen.place(19, 24)
porch.place(0, 42)

bedroom2.place(34, 0)
bath2.place(46, 0)
closet2.place(46, 7)

bedroom3.place(52, 0)
bath3.place(64, 0)
closet3.place(64, 7)

bedroom4.place(34, 13)
closet4.place(46, 13)
bath4.place(46, 19)

bedroom5.place(52, 13)
closet5.place(64, 13)
bath5.place(64, 19)

master_bedroom.place(70, 0)
master_bath.place(82, 0)
master_closet.place(82, 14)

# =================================================================
# 4. BUILD THE FLOOR PLAN — add rooms to the (overall) space
# =================================================================
floor_plan = FloorPlan(title="5-BEDROOM / 5-BATH / 5-CLOSET SINGLE-STORY HOME")
floor_plan.add_rooms(
    garage, hallway, living, kitchen, porch,
    bedroom2, bath2, closet2,
    bedroom3, bath3, closet3,
    bedroom4, bath4, closet4,
    bedroom5, bath5, closet5,
    master_bedroom, master_bath, master_closet,
)

clashes = floor_plan.find_overlaps()
if clashes:
    for a, b in clashes:
        print(f"OVERLAP: {a.space_name} <-> {b.space_name}")
    raise SystemExit("Fix overlapping placements before rendering.")

# =================================================================
# 5. ADD WINDOWS TO ROOMS
#    Only regular rooms receive exterior windows. Other rooms (master
#    suite, kitchen, living, baths, closets, etc.) have no windows.
# =================================================================
# (room, x1, y1, x2, y2) — one exterior wall segment per entry
exterior_window_walls = [
    (bedroom2, 34, 0, 46, 0),
    (bedroom3, 52, 0, 64, 0),
    (bedroom4, 34, 26, 46, 26),
    (bedroom5, 52, 26, 64, 26),
]

WINDOW_INSET = 1.0  # feet; keep the opening a bit inside the wall edge
WINDOW_SCALE = 0.82  # slightly smaller when adjacent rooms could visually merge

for room, x1, y1, x2, y2 in exterior_window_walls:
    horizontal = (y1 == y2)
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    if horizontal:
        room.add_window(Window(cx, y1 + WINDOW_INSET, orientation="horizontal", size_scale=WINDOW_SCALE))
    else:
        room.add_window(Window(x1 + WINDOW_INSET, cy, orientation="vertical", size_scale=WINDOW_SCALE))

# =================================================================
# 6. ADD DOORS TO ROOMS
#    All Doors are the same size (Door.WIDTH) — see door.py.
# =================================================================
hallway.add_door(Door(24, 3, orientation="vertical", quadrant="NE"))    # garage -> hallway
bedroom2.add_door(Door(34, 3, orientation="vertical", quadrant="NE"))   # hallway -> bedroom 2
kitchen.add_door(Door(19, 26, orientation="vertical", quadrant="NE"))   # living -> kitchen
living.add_door(Door(0, 30, orientation="vertical", quadrant="NE"))     # front door

# =================================================================
# RENDER
# =================================================================
FLOOR_COLORS = {
    "bedroom": "#efe9de", "living": "#efe9de", "kitchen": "#efe9de",
    "hallway": "#efe9de", "bath": "#e6ecf0", "closet": "#eee7da",
    "garage": "#d9d9d9", "porch": "#f4f1ea",
}
FONT_MAIN = {
    "bedroom": 12, "living": 13, "kitchen": 13, "hallway": 10,
    "garage": 13, "porch": 11, "bath": 9, "closet": 8.5,
}
FONT_DIM = {
    "bedroom": 10.5, "living": 10.5, "kitchen": 10.5, "hallway": 9,
    "garage": 10.5, "porch": 10, "bath": 8.5, "closet": 8,
}
WALL = "#1a1a1a"

fig, ax = plt.subplots(figsize=(20, 14))

floor_plan.draw(ax, FLOOR_COLORS, FONT_MAIN, FONT_DIM, wall_color=WALL)

# garage floor hatch
gx0, gy0, gx1, gy1 = garage.bounds()
for gx in range(int(gx0) + 1, int(gx1), 2):
    ax.plot([gx, gx], [gy0 + 0.5, gy1 - 0.5], color="#bbbbbb", lw=0.6, zorder=1)

# porch plank texture
px0, py0, px1, py1 = porch.bounds()
for px in range(int(px0) + 1, int(px1), 2):
    ax.plot([px, px], [py0 + 0.3, py1 - 0.3], color="#d8d2c4", lw=0.6, zorder=1)

# outer footprint outline
outer_pts = [(0, 0), (88, 0), (88, 26), (34, 26), (34, 42), (0, 42), (0, 0)]
xs, ys = zip(*outer_pts)
ax.plot(xs, ys, color=WALL, lw=4.0, zorder=5, solid_joinstyle="miter")

# a few key structural walls, bolder
bold_walls = [
    [(24, 0), (24, 24)],
    [(34, 0), (34, 42)],
    [(0, 24), (34, 24)],
    [(19, 24), (19, 42)],
]
for (x1, y1), (x2, y2) in bold_walls:
    ax.plot([x1, x2], [y1, y2], color=WALL, lw=3.0, zorder=5)

TOTAL_AREA = floor_plan.total_area()
ax.text(44, 50.5, floor_plan.title, ha="center", va="center",
        fontsize=17, fontweight="bold", color="#111111")
ax.text(44, 48.7, f"Total Area \u2248 {TOTAL_AREA:,.0f} sq ft   |   Scale in feet",
        ha="center", va="center", fontsize=11, color="#333333")

ax.annotate("N", xy=(85, 46), xytext=(85, 43.5), ha="center", va="center",
            fontsize=11, fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#333333"))

ax.set_xlim(-3, 92)
ax.set_ylim(-3, 53)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("outputs/floor_plan.png", dpi=220, facecolor="white", bbox_inches="tight")
print(f"Total area: {TOTAL_AREA:,.0f} sq ft")
