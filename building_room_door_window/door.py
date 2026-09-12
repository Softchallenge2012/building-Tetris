"""
door.py

A standard swinging door. Every Door is the same size (WIDTH) — only
its position, which wall it's on, and which way it swings differ.
"""

import matplotlib.patches as patches


class Door:
    WIDTH = 3.0          # feet — standard door width, identical for every door
    COLOR = "#555555"
    LINEWIDTH = 1.0

    def __init__(self, x, y, orientation="horizontal", quadrant="NE"):
        """
        x, y        : the door's hinge point, in the same feet-coordinates
                      as the rooms it sits between.
        orientation : 'horizontal' or 'vertical' — which wall the door is cut
                      into (kept for bookkeeping / future use).
        quadrant    : which quarter-circle the door swings through, one of
                      'NE', 'NW', 'SE', 'SW'. Pick whichever one sweeps into
                      open floor space for the room this door belongs to.
        """
        self.x = x
        self.y = y
        self.orientation = orientation
        self.quadrant = quadrant

    _QUADRANT_ANGLES = {
        "NE": (0, 90),
        "NW": (90, 180),
        "SW": (180, 270),
        "SE": (270, 360),
    }

    def draw(self, ax):
        theta1, theta2 = self._QUADRANT_ANGLES[self.quadrant]
        ax.add_patch(patches.Arc((self.x, self.y), 2 * self.WIDTH, 2 * self.WIDTH,
                                  theta1=theta1, theta2=theta2,
                                  color=self.COLOR, lw=self.LINEWIDTH, zorder=6))

    def __repr__(self):
        return f"<Door at ({self.x},{self.y}) swing={self.quadrant}>"
