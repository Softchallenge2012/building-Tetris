import multiprocessing as mp
import os
import shutil
import time

from flask import Flask, abort, redirect, render_template, request, send_file, url_for
import pygame
from PIL import Image, ImageDraw

import building_design as game
from utilities.dummy import DummyDisplay

APP = Flask(__name__)

ROOM_SPECS = [
    {"key": "master_bedroom", "label": "Master Bedroom", "count_label": "master bedrooms", "size": "MASTER_BEDROOM", "count": "number_master_bedrooms"},
    {"key": "master_closet", "label": "Master Closet", "count_label": "master closets", "size": "MASTER_CLOSET", "count": "number_master_closets"},
    {"key": "master_bath", "label": "Master Bath", "count_label": "master baths", "size": "MASTER_BATH", "count": "number_master_baths"},
    {"key": "regular_bedroom", "label": "Regular Bedroom", "count_label": "regular bedrooms", "size": "REGULAR_BEDROOM", "count": "number_regular_bedrooms"},
    {"key": "regular_bath", "label": "Regular Bath", "count_label": "regular baths", "size": "REGULAR_BATH", "count": "number_regular_baths"},
    {"key": "regular_closet", "label": "Regular Closet", "count_label": "regular closets", "size": "REGULAR_CLOSET", "count": "number_regular_closets"},
    {"key": "garage", "label": "Garage", "count_label": "garage", "size": "GARAGE", "count": "number_garages"},
    {"key": "kitchen", "label": "Kitchen", "count_label": "kitchen", "size": "KITCHEN", "count": "number_kitchens"},
    {"key": "covered_porch", "label": "Covered Porch", "count_label": "covered porch", "size": "COVERED_PORCH", "count": "number_covered_porches"},
]

DEFAULT_RUNTIME_CONFIG = {
    "master_bedroom_width": game.MASTER_BEDROOM[0],
    "master_bedroom_height": game.MASTER_BEDROOM[1],
    "master_closet_width": game.MASTER_CLOSET[0],
    "master_closet_height": game.MASTER_CLOSET[1],
    "master_bath_width": game.MASTER_BATH[0],
    "master_bath_height": game.MASTER_BATH[1],
    "regular_bedroom_width": game.REGULAR_BEDROOM[0],
    "regular_bedroom_height": game.REGULAR_BEDROOM[1],
    "regular_bath_width": game.REGULAR_BATH[0],
    "regular_bath_height": game.REGULAR_BATH[1],
    "regular_closet_width": game.REGULAR_CLOSET[0],
    "regular_closet_height": game.REGULAR_CLOSET[1],
    "garage_width": game.GARAGE[0],
    "garage_height": game.GARAGE[1],
    "kitchen_width": game.KITCHEN[0],
    "kitchen_height": game.KITCHEN[1],
    "covered_porch_width": game.COVERED_PORCH[0],
    "covered_porch_height": game.COVERED_PORCH[1],
    "number_master_bedrooms": game.SHAPE_COUNTS["MASTER_BEDROOM"],
    "number_master_closets": game.SHAPE_COUNTS["MASTER_CLOSET"],
    "number_master_baths": game.SHAPE_COUNTS["MASTER_BATH"],
    "number_regular_bedrooms": game.SHAPE_COUNTS["REGULAR_BEDROOM"],
    "number_regular_baths": game.SHAPE_COUNTS["REGULAR_BATH"],
    "number_regular_closets": game.SHAPE_COUNTS["REGULAR_CLOSET"],
    "number_garages": game.SHAPE_COUNTS["GARAGE"],
    "number_kitchens": game.SHAPE_COUNTS["KITCHEN"],
    "number_covered_porches": game.SHAPE_COUNTS["COVERED_PORCH"],
}

CURRENT_RUNTIME_CONFIG = DEFAULT_RUNTIME_CONFIG.copy()
WORKFLOW_PROCESS = None
STATE_MANAGER = None
SHARED_STATE = None
SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "outputs", "pygame_snapshot.png")
TOP_VIEW_PATH = os.path.join(os.path.dirname(__file__), "outputs", "top_view.png")
PYGAME_SCALAR = 50
PYGAME_WIDTH = game.BOARD_COLS * PYGAME_SCALAR
PYGAME_HEIGHT = game.BOARD_ROWS * PYGAME_SCALAR


def _to_int(value, default):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def build_runtime_config(form_data=None):
    config = DEFAULT_RUNTIME_CONFIG.copy()
    if not form_data:
        return config

    for key in config:
        config[key] = _to_int(form_data.get(key), config[key])
    return config


def build_runtime_catalog(config):
    game.SPACE_SIZES = {
        "REGULAR_BEDROOM": (config["regular_bedroom_width"], config["regular_bedroom_height"]),
        "MASTER_BEDROOM": (config["master_bedroom_width"], config["master_bedroom_height"]),
        "REGULAR_CLOSET": (config["regular_closet_width"], config["regular_closet_height"]),
        "MASTER_CLOSET": (config["master_closet_width"], config["master_closet_height"]),
        "REGULAR_BATH": (config["regular_bath_width"], config["regular_bath_height"]),
        "MASTER_BATH": (config["master_bath_width"], config["master_bath_height"]),
        "GARAGE": (config["garage_width"], config["garage_height"]),
        "KITCHEN": (config["kitchen_width"], config["kitchen_height"]),
        "COVERED_PORCH": (config["covered_porch_width"], config["covered_porch_height"]),
    }

    game.SHAPE_COUNTS = {
        "MASTER_BEDROOM": config["number_master_bedrooms"],
        "MASTER_CLOSET": config["number_master_closets"],
        "MASTER_BATH": config["number_master_baths"],
        "REGULAR_BEDROOM": config["number_regular_bedrooms"],
        "REGULAR_BATH": config["number_regular_baths"],
        "REGULAR_CLOSET": config["number_regular_closets"],
        "KITCHEN": config["number_kitchens"],
        "GARAGE": config["number_garages"],
        "COVERED_PORCH": config["number_covered_porches"],
    }

    game.SHAPES = {
        name: game._make_rectangle_states(size, game.SPACE_COLORS[name])
        for name, size in game.SPACE_SIZES.items()
        if game.SHAPE_COUNTS.get(name, 0) > 0
    }

    game.KICK_TABLE = {shape_name: [] for shape_name in game.SHAPES.keys()}


def build_room_labels():
    return {
        (game.SPACE_COLORS["REGULAR_BEDROOM"].r, game.SPACE_COLORS["REGULAR_BEDROOM"].g, game.SPACE_COLORS["REGULAR_BEDROOM"].b): ("RB", f"{game.SPACE_SIZES['REGULAR_BEDROOM'][0]}x{game.SPACE_SIZES['REGULAR_BEDROOM'][1]}"),
        (game.SPACE_COLORS["MASTER_BEDROOM"].r, game.SPACE_COLORS["MASTER_BEDROOM"].g, game.SPACE_COLORS["MASTER_BEDROOM"].b): ("MB", f"{game.SPACE_SIZES['MASTER_BEDROOM'][0]}x{game.SPACE_SIZES['MASTER_BEDROOM'][1]}"),
        (game.SPACE_COLORS["REGULAR_CLOSET"].r, game.SPACE_COLORS["REGULAR_CLOSET"].g, game.SPACE_COLORS["REGULAR_CLOSET"].b): ("RC", f"{game.SPACE_SIZES['REGULAR_CLOSET'][0]}x{game.SPACE_SIZES['REGULAR_CLOSET'][1]}"),
        (game.SPACE_COLORS["MASTER_CLOSET"].r, game.SPACE_COLORS["MASTER_CLOSET"].g, game.SPACE_COLORS["MASTER_CLOSET"].b): ("MC", f"{game.SPACE_SIZES['MASTER_CLOSET'][0]}x{game.SPACE_SIZES['MASTER_CLOSET'][1]}"),
        (game.SPACE_COLORS["REGULAR_BATH"].r, game.SPACE_COLORS["REGULAR_BATH"].g, game.SPACE_COLORS["REGULAR_BATH"].b): ("RBath", f"{game.SPACE_SIZES['REGULAR_BATH'][0]}x{game.SPACE_SIZES['REGULAR_BATH'][1]}"),
        (game.SPACE_COLORS["MASTER_BATH"].r, game.SPACE_COLORS["MASTER_BATH"].g, game.SPACE_COLORS["MASTER_BATH"].b): ("MBath", f"{game.SPACE_SIZES['MASTER_BATH'][0]}x{game.SPACE_SIZES['MASTER_BATH'][1]}"),
        (game.SPACE_COLORS["GARAGE"].r, game.SPACE_COLORS["GARAGE"].g, game.SPACE_COLORS["GARAGE"].b): ("GAR", f"{game.SPACE_SIZES['GARAGE'][0]}x{game.SPACE_SIZES['GARAGE'][1]}"),
        (game.SPACE_COLORS["KITCHEN"].r, game.SPACE_COLORS["KITCHEN"].g, game.SPACE_COLORS["KITCHEN"].b): ("KIT", f"{game.SPACE_SIZES['KITCHEN'][0]}x{game.SPACE_SIZES['KITCHEN'][1]}"),
        (game.SPACE_COLORS["COVERED_PORCH"].r, game.SPACE_COLORS["COVERED_PORCH"].g, game.SPACE_COLORS["COVERED_PORCH"].b): ("POR", f"{game.SPACE_SIZES['COVERED_PORCH'][0]}x{game.SPACE_SIZES['COVERED_PORCH'][1]}"),
    }


def _render_canvas_lines(config):
    lines = []
    for spec in ROOM_SPECS:
        width = config[f"{spec['key']}_width"]
        height = config[f"{spec['key']}_height"]
        count = config[spec["count"]]
        lines.append((spec["label"], width, height, count))
    return lines


def _remove_generated_images():
    output_dir = os.path.dirname(SNAPSHOT_PATH)
    os.makedirs(output_dir, exist_ok=True)
    for filename in [
        "top_view.png",
        "front_view.png",
        "back_view.png",
        "left_view.png",
        "right_view.png",
    ]:
        path = os.path.join(output_dir, filename)
        if os.path.exists(path):
            os.remove(path)


def _ensure_snapshot_exists():
    os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)

    if not os.path.exists(SNAPSHOT_PATH) and os.path.exists(TOP_VIEW_PATH):
        shutil.copy2(TOP_VIEW_PATH, SNAPSHOT_PATH)
    elif not os.path.exists(TOP_VIEW_PATH) and os.path.exists(SNAPSHOT_PATH):
        shutil.copy2(SNAPSHOT_PATH, TOP_VIEW_PATH)
    elif not os.path.exists(SNAPSHOT_PATH) and not os.path.exists(TOP_VIEW_PATH):
        if not pygame.get_init():
            pygame.init()
        surface = pygame.Surface((game.BOARD_COLS * 50, game.BOARD_ROWS * 50))
        surface.fill((15, 23, 42))
        pygame.image.save(surface, TOP_VIEW_PATH)
        pygame.image.save(surface, SNAPSHOT_PATH)


def _generate_facade_views(snapshot_path=TOP_VIEW_PATH):
    from collections import Counter

    base_dir = os.path.dirname(snapshot_path)
    os.makedirs(base_dir, exist_ok=True)

    if not os.path.exists(snapshot_path):
        return {}

    try:
        src = Image.open(snapshot_path).convert('RGB')
    except Exception:
        return {}

    GRID_N = 10  # 10x10 cells, each 50px in 500x500 source = 10ft in real life
    CELL_PX = src.width // GRID_N

    def dominant_color(img, x0, y0, x1, y1):
        cnt = Counter()
        for x in range(x0, x1, 2):
            for y in range(y0, y1, 2):
                cnt[img.getpixel((x, y))] += 1
        return cnt.most_common(1)[0][0]

    grid = []
    for r in range(GRID_N):
        row = []
        for c in range(GRID_N):
            x0, x1 = c * CELL_PX + 5, (c + 1) * CELL_PX - 5
            y0, y1 = r * CELL_PX + 5, (r + 1) * CELL_PX - 5
            row.append(dominant_color(src, x0, y0, x1, y1))
        grid.append(row)

    BLACK = (0, 0, 0)

    def label(color):
        return {(0, 0, 0): 'ground', (0, 255, 0): 'green',
                (255, 170, 0): 'orange', (0, 255, 255): 'lightblue'}.get(color, 'ground')

    # Project footprint onto four outer faces
    top = []
    for c in range(GRID_N):
        val = 'ground'
        for r in range(GRID_N):
            if grid[r][c] != BLACK:
                val = label(grid[r][c]); break
        top.append(val)

    bottom = []
    for c in range(GRID_N):
        val = 'ground'
        for r in range(GRID_N - 1, -1, -1):
            if grid[r][c] != BLACK:
                val = label(grid[r][c]); break
        bottom.append(val)

    left = []
    for r in range(GRID_N):
        val = 'ground'
        for c in range(GRID_N):
            if grid[r][c] != BLACK:
                val = label(grid[r][c]); break
        left.append(val)

    right = []
    for r in range(GRID_N):
        val = 'ground'
        for c in range(GRID_N - 1, -1, -1):
            if grid[r][c] != BLACK:
                val = label(grid[r][c]); break
        right.append(val)

    elevations = {
        'Top elevation (north face)': top,
        'Bottom elevation (south face)': bottom,
        'Left elevation (west face)': left,
        'Right elevation (east face)': right,
    }

    FT_TO_PX = 12
    SEG_W = FT_TO_PX * 10
    WALL_H = FT_TO_PX * 10
    MARGIN = 60
    TITLE_H = 30
    PANEL_H = TITLE_H + WALL_H + 30
    IMG_W = MARGIN * 2 + SEG_W * GRID_N
    IMG_H = MARGIN * 2 + PANEL_H * 4 + 40

    COLOR_HEX = {
        'green': (0, 204, 0),
        'orange': (255, 170, 0),
        'lightblue': (51, 204, 255),
        'ground': None,
    }

    FEATURE_SIZE = FT_TO_PX * 3
    FEATURE_UP = FT_TO_PX * 3
    FEATURE_OUTLINE = (20, 20, 20)
    FEATURE_INSET = 5

    def draw_elevation(draw, title, seq, top_y):
        wall_top = top_y + TITLE_H
        baseline = wall_top + WALL_H
        for i, val in enumerate(seq):
            x0 = MARGIN + i * SEG_W
            x1 = x0 + SEG_W
            color = COLOR_HEX[val]
            if color:
                draw.rectangle([x0, wall_top, x1, baseline], fill=color, outline=(90, 90, 90), width=1)
        for i, val in enumerate(seq):
            if val != 'lightblue':
                continue
            cx = MARGIN + i * SEG_W + SEG_W / 2
            sq_bottom = baseline - FEATURE_UP
            sq_top = sq_bottom - FEATURE_SIZE
            sq_x0 = cx - FEATURE_SIZE / 2
            sq_x1 = cx + FEATURE_SIZE / 2
            draw.rectangle([sq_x0, sq_top, sq_x1, sq_bottom], outline=FEATURE_OUTLINE, width=2)
            draw.rectangle([sq_x0 + FEATURE_INSET, sq_top + FEATURE_INSET,
                             sq_x1 - FEATURE_INSET, sq_bottom - FEATURE_INSET],
                            outline=FEATURE_OUTLINE, width=1)

    def render_combined():
        img = Image.new('RGB', (IMG_W, IMG_H), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        y = MARGIN
        for title, seq in elevations.items():
            draw_elevation(draw, title, seq, y)
            y += PANEL_H
        return img

    def render_single(title, seq):
        h = MARGIN * 2 + PANEL_H
        img = Image.new('RGB', (IMG_W, h), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw_elevation(draw, title, seq, MARGIN)
        return img

    combined = render_combined()
    combined.save(os.path.join(base_dir, 'site_elevations_combined.png'))

    file_map = {
        'Top elevation (north face)': 'elevation_top_north.png',
        'Bottom elevation (south face)': 'elevation_bottom_south.png',
        'Left elevation (west face)': 'elevation_left_west.png',
        'Right elevation (east face)': 'elevation_right_east.png',
    }

    output_paths = {}
    for title, seq in elevations.items():
        img = render_single(title, seq)
        wall_top = MARGIN + TITLE_H
        baseline = wall_top + WALL_H
        wall_crop = img.crop((0, wall_top, IMG_W, baseline))

        stacked_h = WALL_H * 17
        stacked_img = Image.new('RGB', (IMG_W, stacked_h), (255, 255, 255))
        for f in range(17):
            stacked_img.paste(wall_crop, (0, f * WALL_H))

        out_file = file_map[title]
        out_path = os.path.join(base_dir, out_file)
        stacked_img.save(out_path)
        output_paths[title] = out_path

    return output_paths


def _run_game_process(config, shared_state):
    build_runtime_catalog(config)
    runtime_labels = build_room_labels()
    game.GLOBAL_STATE = shared_state

    display = DummyDisplay(room_labels=runtime_labels, snapshot_path=TOP_VIEW_PATH)
    tetris = game.Tetris(display=display)
    tetris.play()


def start_workflow(config):
    global WORKFLOW_PROCESS, CURRENT_RUNTIME_CONFIG, STATE_MANAGER, SHARED_STATE

    CURRENT_RUNTIME_CONFIG = config.copy()

    if WORKFLOW_PROCESS is not None and WORKFLOW_PROCESS.is_alive():
        WORKFLOW_PROCESS.terminate()
        WORKFLOW_PROCESS.join(timeout=1)

    _remove_generated_images()

    if STATE_MANAGER is None:
        STATE_MANAGER = mp.Manager()

    SHARED_STATE = STATE_MANAGER.dict(game.GLOBAL_STATE)
    _ensure_snapshot_exists()
    WORKFLOW_PROCESS = mp.Process(target=_run_game_process, args=(config, SHARED_STATE), daemon=True)
    WORKFLOW_PROCESS.start()


def _get_shared_state():
    global SHARED_STATE
    if SHARED_STATE is None:
        return game.GLOBAL_STATE
    return SHARED_STATE


@APP.route("/")
def index():
    return render_template(
        "index.html",
        config=CURRENT_RUNTIME_CONFIG,
        default_config=DEFAULT_RUNTIME_CONFIG,
        form_fields=ROOM_SPECS,
        status_text="Workflow running" if WORKFLOW_PROCESS is not None and WORKFLOW_PROCESS.is_alive() else "Workflow idle",
    )


@APP.route("/start", methods=["POST"])
def start_workflow_route():
    config = build_runtime_config(request.form)
    start_workflow(config)
    return redirect(url_for("index"))


@APP.route("/pygame-window")
def pygame_window_view():
    message = "Workflow running" if WORKFLOW_PROCESS is not None and WORKFLOW_PROCESS.is_alive() else "Workflow idle"
    return render_template(
        "pygame_view.html",
        timestamp=int(time.time()),
        message=message,
        pygame_width=PYGAME_WIDTH,
        pygame_height=PYGAME_HEIGHT,
    )


@APP.route("/second-screen")
def second_screen_view():
    state = _get_shared_state()
    return render_template(
        "second_screen.html",
        workflow_running=WORKFLOW_PROCESS is not None and WORKFLOW_PROCESS.is_alive(),
    )


@APP.route("/second-screen/pause", methods=["POST"])
def second_screen_pause():
    state = _get_shared_state()
    state["HOLD_REQUEST"] = True
    return redirect(url_for("pygame_window_view"))


@APP.route("/second-screen/reset", methods=["POST"])
def second_screen_reset():
    # Always restart with the same config currently shown in the left-side form.
    start_workflow(CURRENT_RUNTIME_CONFIG)
    return redirect(url_for("pygame_window_view"))


def generate_3d_building_view():
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    def load_img(fname, fallback):
        p = os.path.join(outputs_dir, fname)
        if not os.path.exists(p):
            p = os.path.join(outputs_dir, fallback)
        if not os.path.exists(p):
            im = Image.new('RGB', (150, 150), (255, 255, 255))
        else:
            im = Image.open(p).convert('RGB')
            arr = np.array(im)

            bg = (arr[:, :, 0] >= 240) & (arr[:, :, 1] >= 240) & (arr[:, :, 2] >= 240)
            mask = ~bg

            from scipy import ndimage
            struct = np.ones((3, 3), dtype=bool)
            cleaned = ndimage.binary_opening(mask, structure=struct, iterations=2)

            labeled, n = ndimage.label(cleaned)
            if n > 0:
                sizes = ndimage.sum(cleaned, labeled, range(1, n + 1))
                main_label = int(np.argmax(sizes)) + 1
                building = labeled == main_label
                rows = np.any(building, axis=1)
                cols = np.any(building, axis=0)
                if rows.any() and cols.any():
                    rmin, rmax = np.where(rows)[0][[0, -1]]
                    cmin, cmax = np.where(cols)[0][[0, -1]]
                    im = im.crop((cmin, rmin, cmax + 1, rmax + 1))

            # trimmed_path = os.path.join(outputs_dir, "trimmed_" + os.path.basename(p))
            # im.save(trimmed_path)
            im = im.resize((150, 150))
        return np.array(im) / 255.0

    south_img = load_img("facade_elevation_south.png", "elevation_bottom_south.png")
    north_img = load_img("facade_elevation_north.png", "elevation_top_north.png")
    west_img = load_img("facade_elevation_west.png", "elevation_left_west.png")
    east_img = load_img("facade_elevation_east.png", "elevation_right_east.png")

    fig = plt.figure(figsize=(10, 10), dpi=150)
    ax = fig.add_subplot(111, projection='3d')

    # South face (y = 0)
    X, Z = np.meshgrid(np.linspace(0, 10, south_img.shape[1]), np.linspace(17, 0, south_img.shape[0]))
    Y = np.full_like(X, 0)
    ax.plot_surface(X, Y, Z, facecolors=south_img, rstride=1, cstride=1, shade=False)

    # North face (y = 10)
    X, Z = np.meshgrid(np.linspace(10, 0, north_img.shape[1]), np.linspace(17, 0, north_img.shape[0]))
    Y = np.full_like(X, 10)
    ax.plot_surface(X, Y, Z, facecolors=north_img, rstride=1, cstride=1, shade=False)

    # West face (x = 0)
    Y, Z = np.meshgrid(np.linspace(0, 10, west_img.shape[1]), np.linspace(17, 0, west_img.shape[0]))
    X = np.full_like(Y, 0)
    ax.plot_surface(X, Y, Z, facecolors=west_img, rstride=1, cstride=1, shade=False)

    # East face (x = 10)
    Y, Z = np.meshgrid(np.linspace(10, 0, east_img.shape[1]), np.linspace(17, 0, east_img.shape[0]))
    X = np.full_like(Y, 10)
    ax.plot_surface(X, Y, Z, facecolors=east_img, rstride=1, cstride=1, shade=False)

    ax.set_xlim(-2, 12)
    ax.set_ylim(-2, 12)
    ax.set_zlim(0, 20)
    ax.set_box_aspect((1, 1, 1.7))
    ax.view_init(elev=25, azim=-45)
    ax.set_axis_off()

    out_3d = os.path.join(outputs_dir, "building_3d_view.png")
    fig.savefig(out_3d, bbox_inches='tight', pad_inches=0.1, facecolor='#0f172a')
    plt.close(fig)

    return out_3d


@APP.route("/second-screen/build-3d", methods=["POST"])
def second_screen_build_3d():
    from floors.generate_elevations import generate_elevations
    from floors.image_generation import generate_polished_images

    # 1. Generate 4 elevation views using floors/generate_elevations.py
    generate_elevations()

    # 2. Polish 4 elevation views using floors/image_generation.py
    generate_polished_images()

    # return redirect(url_for("pygame_window_view"))

    # 3. Generate 3D building view
    generate_3d_building_view()

    return redirect(url_for("pygame_window_view"))


@APP.route("/second-screen/view-3d", methods=["POST"])
def second_screen_view_3d():
    generate_3d_building_view()
    return redirect(url_for("pygame_window_view"))


@APP.route("/view-3d-image")
def view_3d_image():
    out_3d = os.path.join(os.path.dirname(__file__), "outputs", "building_3d_view.png")
    if not os.path.exists(out_3d):
        return "", 204
    response = send_file(out_3d, mimetype="image/png")
    response.cache_control.no_store = True
    response.cache_control.no_cache = True
    response.cache_control.must_revalidate = True
    response.expires = 0
    response.headers["Pragma"] = "no-cache"
    return response


@APP.route("/pygame-snapshot")
def pygame_snapshot():
    _ensure_snapshot_exists()
    if os.path.exists(SNAPSHOT_PATH):
        shutil.copy2(SNAPSHOT_PATH, TOP_VIEW_PATH)
        # _generate_facade_views(TOP_VIEW_PATH)
    target_path = SNAPSHOT_PATH if os.path.exists(SNAPSHOT_PATH) else TOP_VIEW_PATH
    response = send_file(target_path, mimetype="image/png")
    response.cache_control.no_store = True
    response.cache_control.no_cache = True
    response.cache_control.must_revalidate = True
    response.expires = 0
    response.headers["Pragma"] = "no-cache"
    return response


@APP.route("/canvas")
def canvas_view():
    return render_template(
        "canvas.html",
        canvas_rows=_render_canvas_lines(CURRENT_RUNTIME_CONFIG),
    )


if __name__ == "__main__":
    _ensure_snapshot_exists()
    if os.path.exists(SNAPSHOT_PATH):
        shutil.copy2(SNAPSHOT_PATH, TOP_VIEW_PATH)
        # _generate_facade_views(TOP_VIEW_PATH)
    APP.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
