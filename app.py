import multiprocessing as mp
import os
import time

from flask import Flask, abort, redirect, render_template, request, send_file, url_for
import pygame

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


def _ensure_snapshot_exists():
    os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
    if os.path.exists(SNAPSHOT_PATH):
        return

    if not pygame.get_init():
        pygame.init()

    surface = pygame.Surface((game.BOARD_COLS * 50, game.BOARD_ROWS * 50))
    surface.fill((15, 23, 42))
    pygame.image.save(surface, SNAPSHOT_PATH)


def _run_game_process(config, shared_state):
    build_runtime_catalog(config)
    runtime_labels = build_room_labels()
    game.GLOBAL_STATE = shared_state

    display = DummyDisplay(room_labels=runtime_labels, snapshot_path=SNAPSHOT_PATH)
    tetris = game.Tetris(display=display)
    tetris.play()


def start_workflow(config):
    global WORKFLOW_PROCESS, CURRENT_RUNTIME_CONFIG, STATE_MANAGER, SHARED_STATE

    CURRENT_RUNTIME_CONFIG = config.copy()

    if WORKFLOW_PROCESS is not None and WORKFLOW_PROCESS.is_alive():
        WORKFLOW_PROCESS.terminate()
        WORKFLOW_PROCESS.join(timeout=1)

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


@APP.route("/pygame-snapshot")
def pygame_snapshot():
    _ensure_snapshot_exists()
    response = send_file(SNAPSHOT_PATH, mimetype="image/png")
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
    APP.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
