"""
space.py

A minimal "Space" module for laying out a floor plan.

Design idea:
  - A Space only knows WHAT it is (name) and HOW BIG it is (size).
  - It does NOT know WHERE it goes until you call .place(x, y).
  This keeps "define the rooms" and "arrange the rooms" as two
  separate, independently-editable steps.
"""


class Space:
    def __init__(self, space_name, size, category="room", dims_label=None):
        """
        space_name : str            e.g. "BEDROOM 2"
        size       : (width, height) in feet, e.g. (12, 13)
        category   : str            used for floor color / grouping,
                                     e.g. "bedroom", "bath", "closet",
                                     "kitchen", "living", "garage",
                                     "porch", "hallway"
        dims_label : str|None       text shown under the name, defaults
                                     to "W' x H'"
        """
        self.space_name = space_name
        self.size = size
        self.category = category
        self.dims_label = dims_label or f"{size[0]}' x {size[1]}'"
        self.x = None
        self.y = None
        self.doors = []
        self.windows = []

    # ---- size -----------------------------------------------------
    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    @property
    def area(self):
        return self.size[0] * self.size[1]

    # ---- placement --------------------------------------------------
    def place(self, x, y):
        """Set this space's bottom-left corner coordinates. Returns self
        so placement calls can be chained/read fluently."""
        self.x = x
        self.y = y
        return self

    @property
    def is_placed(self):
        return self.x is not None and self.y is not None

    def bounds(self):
        """(x_min, y_min, x_max, y_max) — raises if not placed yet."""
        if not self.is_placed:
            raise ValueError(f"'{self.space_name}' has not been placed yet")
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def overlaps(self, other):
        ax0, ay0, ax1, ay1 = self.bounds()
        bx0, by0, bx1, by1 = other.bounds()
        return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1

    # ---- openings ---------------------------------------------------
    def add_door(self, door):
        """Attach a Door instance (see door.py) to this room."""
        self.doors.append(door)
        return door

    def add_window(self, window):
        """Attach a Window instance (see window.py) to this room."""
        self.windows.append(window)
        return window

    def __repr__(self):
        pos = f"({self.x},{self.y})" if self.is_placed else "unplaced"
        return f"<Space {self.space_name!r} {self.width}x{self.height} @ {pos}>"


def total_area(spaces):
    return sum(s.area for s in spaces)


def window_count(length, spacing=6, min_windows=1):
    """How many windows a wall of this length needs so that spacing
    between windows never exceeds `spacing` feet (default: one window
    every 6 ft)."""
    import math
    return max(min_windows, math.ceil(length / spacing))


def find_overlaps(spaces):
    """Returns a list of (space_a, space_b) pairs whose footprints overlap.
    Handy sanity check after adjusting coordinates."""
    clashes = []
    placed = [s for s in spaces if s.is_placed]
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            if placed[i].overlaps(placed[j]):
                clashes.append((placed[i], placed[j]))
    return clashes
