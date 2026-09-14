"""
window.py

A standard window symbol. Every Window is the same size (WIDTH x
THICKNESS) — only its position and which wall it sits on differ.
"""

import matplotlib.patches as patches


class Window:
    WIDTH = 3.0          # feet — 36 inches wide
    THICKNESS = 4.0      # feet — 48 inches tall, centered in the wall thickness
    GLASS_COLOR = "#bfe0ee"
    FRAME_COLOR = "#1a1a1a"

    def __init__(self, x, y, orientation="horizontal", size_scale=1.0):
        """
        x, y        : the window's center point.
        orientation : 'horizontal' (window sits on a wall running east-west,
                      so the glass is wide and shallow) or 'vertical'
                      (wall runs north-south, glass is narrow and tall).
        size_scale  : scale factor applied to the nominal window size so
                      adjacent room windows can stay visually distinct.
        """
        self.x = x
        self.y = y
        self.orientation = orientation
        self.size_scale = size_scale

    def draw(self, ax):
        if self.orientation == "horizontal":
            w, h = self.WIDTH * self.size_scale, self.THICKNESS * self.size_scale
        else:
            w, h = self.THICKNESS * self.size_scale, self.WIDTH * self.size_scale

        # double-line frame for a clearer architectural window look
        outer = patches.Rectangle((self.x - w / 2, self.y - h / 2), w, h,
                                  facecolor=self.GLASS_COLOR,
                                  edgecolor=self.FRAME_COLOR,
                                  linewidth=1.4, zorder=6)
        inner = patches.Rectangle((self.x - w / 2 + 0.22, self.y - h / 2 + 0.22),
                                  max(w - 0.44, 0.5), max(h - 0.44, 0.5),
                                  facecolor="none", edgecolor=self.FRAME_COLOR,
                                  linewidth=0.8, zorder=7)
        ax.add_patch(outer)
        ax.add_patch(inner)

        # center line to suggest a pane divider
        if self.orientation == "horizontal":
            ax.plot([self.x - w / 2, self.x + w / 2], [self.y, self.y],
                     color=self.FRAME_COLOR, lw=0.8, zorder=8)
        else:
            ax.plot([self.x, self.x], [self.y - h / 2, self.y + h / 2],
                     color=self.FRAME_COLOR, lw=0.8, zorder=8)

    def __repr__(self):
        return f"<Window at ({self.x},{self.y}) {self.orientation}>"
