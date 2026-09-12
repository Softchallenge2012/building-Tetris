"""
floorplan.py

FloorPlan is the overall "space" (the house). You build it by adding
Space instances (rooms) to it one at a time, each already placed via
room.place(x, y). Doors and windows are not owned by the FloorPlan
directly — they live on the rooms themselves (see space.py's
add_door / add_window) — but FloorPlan.draw() renders everything:
every room, plus every door and window attached to every room.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from space import find_overlaps


class FloorPlan:
    def __init__(self, title=""):
        self.title = title
        self.rooms = []

    def add_room(self, room):
        """Add an already-sized (and usually already-placed) Space to the plan."""
        self.rooms.append(room)
        return room

    def add_rooms(self, *rooms):
        for room in rooms:
            self.add_room(room)
        return rooms

    def total_area(self):
        return sum(r.area for r in self.rooms)

    def find_overlaps(self):
        return find_overlaps(self.rooms)

    def draw(self, ax, floor_colors, font_main, font_dim, wall_color="#1a1a1a"):
        """Draw every room (rectangle + label) then every door/window
        attached to each room."""
        for room in self.rooms:
            rect = patches.Rectangle((room.x, room.y), room.width, room.height,
                                      facecolor=floor_colors.get(room.category, "#ffffff"),
                                      edgecolor=wall_color, linewidth=2.4, zorder=2)
            ax.add_patch(rect)
            cx, cy = room.x + room.width / 2, room.y + room.height / 2
            ax.text(cx, cy + room.height * 0.06, room.space_name, ha="center", va="center",
                    fontsize=font_main.get(room.category, 10), fontweight="bold",
                    color="#111111", zorder=4)
            ax.text(cx, cy - room.height * 0.16, room.dims_label, ha="center", va="center",
                    fontsize=font_dim.get(room.category, 9), color="#333333", zorder=4)

        for room in self.rooms:
            for window in room.windows:
                window.draw(ax)
            for door in room.doors:
                door.draw(ax)
