"""Contains dummy display class that displays the frame in a window."""

import pygame
from utilities.display import Display, Frame


ROOM_LABELS = {
    (0, 255, 255): ("RB", "12x13"),
    (0, 0, 255): ("MB", "12x26"),
    (255, 170, 0): ("RC", "6x6"),
    (255, 255, 0): ("MC", "6x12"),
    (0, 255, 0): ("RBath", "6x7"),
    (153, 0, 255): ("MBath", "6x14"),
    (255, 0, 0): ("GAR", "24x24"),
    (120, 210, 150): ("KIT", "15x18"),
    (180, 150, 120): ("POR", "34x6"),
}

SKIP_LABEL_COLORS = {
    (0, 0, 0),
    (255, 255, 255),
    (42, 42, 42),
}

GRID_COLOR = (85, 85, 85)
GRID_BORDER_COLOR = (200, 200, 200)

class DummyDisplay(Display):
    """Display that displays the frame in a window."""

    def __init__(self, scalar=50, room_labels=None, snapshot_path=None):
        self._scalar = scalar
        self._room_labels = room_labels if room_labels is not None else ROOM_LABELS
        self._snapshot_path = snapshot_path
        if not pygame.get_init():
            pygame.init()
            self._screen = pygame.display.set_mode((Frame.DISPLAY_COLS * self._scalar, Frame.DISPLAY_ROWS * self._scalar))
            self._screen.fill((0, 0, 0))
        self._font = pygame.font.SysFont("Arial", max(8, self._scalar // 4), bold=True)
        self._small_font = pygame.font.SysFont("Arial", max(7, self._scalar // 5))
        self._banner_font = pygame.font.SysFont("Arial", max(14, self._scalar // 2), bold=True)

    def makeframe(self):
        return Frame()

    def _find_components(self, frame):
        visited = set()
        components = []

        for row in range(frame.nrows()):
            for col in range(frame.ncols()):
                color = frame[row][col]
                rgb = (color.r, color.g, color.b)
                if rgb in SKIP_LABEL_COLORS or (row, col) in visited:
                    continue

                stack = [(row, col)]
                visited.add((row, col))
                cells = []

                while stack:
                    cur_row, cur_col = stack.pop()
                    cells.append((cur_row, cur_col))

                    for next_row, next_col in (
                        (cur_row - 1, cur_col),
                        (cur_row + 1, cur_col),
                        (cur_row, cur_col - 1),
                        (cur_row, cur_col + 1),
                    ):
                        if not (0 <= next_row < frame.nrows() and 0 <= next_col < frame.ncols()):
                            continue
                        if (next_row, next_col) in visited:
                            continue
                        next_color = frame[next_row][next_col]
                        next_rgb = (next_color.r, next_color.g, next_color.b)
                        if next_rgb != rgb:
                            continue
                        visited.add((next_row, next_col))
                        stack.append((next_row, next_col))

                components.append((rgb, cells))

        return components

    def _draw_component_overlay(self, rgb, cells):
        if rgb not in self._room_labels:
            return

        acronym, dimensions = self._room_labels[rgb]
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        left = min_col * self._scalar
        top = min_row * self._scalar
        width = (max_col - min_col + 1) * self._scalar
        height = (max_row - min_row + 1) * self._scalar

        outline = pygame.Rect(left, top, width, height)
        pygame.draw.rect(self._screen, (255, 255, 255), outline, width=max(2, self._scalar // 14))

        center_x = left + width // 2
        center_y = top + height // 2

        label_surface = self._font.render(acronym, True, (255, 255, 255))
        dims_surface = self._small_font.render(dimensions, True, (255, 255, 255))

        label_rect = label_surface.get_rect(center=(center_x, center_y - dims_surface.get_height() // 2))
        dims_rect = dims_surface.get_rect(center=(center_x, center_y + label_surface.get_height() // 2))
        self._screen.blit(label_surface, label_rect)
        self._screen.blit(dims_surface, dims_rect)

    def _draw_land_grid(self, frame):
        board_width = frame.ncols() * self._scalar
        board_height = frame.nrows() * self._scalar

        for col in range(frame.ncols() + 1):
            x = col * self._scalar
            pygame.draw.line(self._screen, GRID_COLOR, (x, 0), (x, board_height), width=1)

        for row in range(frame.nrows() + 1):
            y = row * self._scalar
            pygame.draw.line(self._screen, GRID_COLOR, (0, y), (board_width, y), width=1)

        pygame.draw.rect(self._screen, GRID_BORDER_COLOR, pygame.Rect(0, 0, board_width, board_height), width=2)

    def send(self, frame):
        for i in range(0, frame.nrows()):
            row = frame.row(i)

            for j in range(0, frame.ncols()):
                color = row[j]
                pixel = pygame.Rect(j * self._scalar, i * self._scalar, self._scalar, self._scalar)
                pygame.draw.rect(self._screen, (color.r, color.g, color.b), pixel)

        self._draw_land_grid(frame)

        for rgb, cells in self._find_components(frame):
            self._draw_component_overlay(rgb, cells)

        pygame.display.flip()

        if self._snapshot_path:
            pygame.image.save(self._screen, self._snapshot_path)

    def showMessage(self, message):
        text_surface = self._banner_font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(midtop=(self._screen.get_width() // 2, 5))
        shadow_rect = text_rect.move(2, 2)
        shadow_surface = self._banner_font.render(message, True, (0, 0, 0))
        self._screen.blit(shadow_surface, shadow_rect)
        self._screen.blit(text_surface, text_rect)
        pygame.display.flip()
