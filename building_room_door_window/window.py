"""
window.py

A standard window symbol. Every Window is the same size (WIDTH x
THICKNESS) — only its position and which wall it sits on differ.
"""

import matplotlib.patches as patches


class Window:
    WIDTH = 3.0          # feet — standard window width, identical for every window
    THICKNESS = 0.55     # feet — how deep the window symbol is drawn into the wall
    GLASS_COLOR = "#bfe0ee"
    FRAME_COLOR = "#1a1a1a"

    def __init__(self, x, y, orientation="horizontal"):
        """
        x, y        : the window's center point.
        orientation : 'horizontal' (window sits on a wall running east-west,
                      so the glass is wide and shallow) or 'vertical'
                      (wall runs north-south, glass is narrow and tall).
        """
        self.x = x
        self.y = y
        self.orientation = orientation

    def draw(self, ax):
        if self.orientation == "horizontal":
            w, h = self.WIDTH, self.THICKNESS
        else:
            w, h = self.THICKNESS, self.WIDTH

        ax.add_patch(patches.Rectangle((self.x - w / 2, self.y - h / 2), w, h,
                                        facecolor=self.GLASS_COLOR,
                                        edgecolor=self.FRAME_COLOR,
                                        linewidth=1.2, zorder=6))
        # center line to suggest a pane divider
        if self.orientation == "horizontal":
            ax.plot([self.x - w / 2, self.x + w / 2], [self.y, self.y],
                     color=self.FRAME_COLOR, lw=0.8, zorder=7)
        else:
            ax.plot([self.x, self.x], [self.y - h / 2, self.y + h / 2],
                     color=self.FRAME_COLOR, lw=0.8, zorder=7)

    def __repr__(self):
        return f"<Window at ({self.x},{self.y}) {self.orientation}>"
