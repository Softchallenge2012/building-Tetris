import os
import pygame
import numpy as np
import time
import tkinter as tk
import threading
import multiprocessing as mp
import math

from utilities.input_manager import InputManager
from utilities.display import Color, Frame
from utilities.dummy import DummyDisplay

# Defining game constants
FPS = 30 # Screen refresh rate (CANNOT BE MODIFIED)
CLASSIC_SIMULATION_RATE = 60 # Classic input handling rate (e.g. NES Tetris, Tetris 99)
MODERN_SIMULATION_RATE = 1000 # Modern input handling rate (e.g. Tetr.io)

# Calculate equivalent ns per frame and subtick for both simulation rates
NS_PER_FRAME = 1_000_000_000 // FPS
CLASSIC_NS_PER_SUBTICK = 1_000_000_000 // CLASSIC_SIMULATION_RATE
MODERN_NS_PER_SUBTICK = 1_000_000_000 // MODERN_SIMULATION_RATE

# Defining stanndard Tetromino colors
X = Color() # Black
W = Color(255, 255, 255) # White
C = Color(0, 255, 255) # Cyan
B = Color(0, 0, 255) # Blue
O = Color(255, 170, 0) # Orange
Y = Color(255, 255, 0) # Yellow
G = Color(0, 255, 0) # Green
P = Color(153, 0, 255) # Purple
R = Color(255, 0, 0) # Red
A = Color(42, 42, 42) # Gray

# Logical board units requested for this mode.
BOARD_ROWS = 10
BOARD_COLS = 10

# Space sizes from build_floor_plan.py
MASTER_BEDROOM = (12, 26)
MASTER_CLOSET = (6, 12)
MASTER_BATH = (6, 14)
REGULAR_BEDROOM = (12, 13)
REGULAR_CLOSET = (6, 6)
REGULAR_BATH = (6, 7)
GARAGE = (24, 24)
KITCHEN = (15, 18)
COVERED_PORCH = (34, 6)

SPACE_SIZES = {
    "REGULAR_BEDROOM": REGULAR_BEDROOM,
    "MASTER_BEDROOM": MASTER_BEDROOM,
    "REGULAR_CLOSET": REGULAR_CLOSET,
    "MASTER_CLOSET": MASTER_CLOSET,
    "REGULAR_BATH": REGULAR_BATH,
    "MASTER_BATH": MASTER_BATH,
    "GARAGE": GARAGE,
    "KITCHEN": KITCHEN,
    "COVERED_PORCH": COVERED_PORCH,
}

SPACE_COLORS = {
    "REGULAR_BEDROOM": C,
    "MASTER_BEDROOM": B,
    "REGULAR_CLOSET": O,
    "MASTER_CLOSET": Y,
    "REGULAR_BATH": G,
    "MASTER_BATH": P,
    "GARAGE": R,
    "KITCHEN": Color(120, 210, 150),
    "COVERED_PORCH": Color(180, 150, 120),
}

SHAPE_COUNTS = {
    "MASTER_BEDROOM": 0,
    "MASTER_CLOSET": 0,
    "MASTER_BATH": 0,
    "REGULAR_BEDROOM": 9,
    "REGULAR_BATH": 9,
    "REGULAR_CLOSET": 9,
    "KITCHEN": 0,
    "GARAGE": 0,
    "COVERED_PORCH": 0,
}

LAND_WIDTH = 100
LAND_HEIGHT = 100


def _scaled_space_size(size):
    width, height = size
    return (
        max(0, int(math.ceil(width / LAND_WIDTH * BOARD_COLS))),
        max(0, int(math.ceil(height / LAND_HEIGHT * BOARD_ROWS))),
    )


def _make_rectangle_states(size, color):
    width, height = _scaled_space_size(size)
    state = np.full((height, width), color, dtype=object)
    if width == height:
        return [state]
    return [state, np.full((width, height), color, dtype=object)]


SHAPES = {
    name: _make_rectangle_states(size, SPACE_COLORS[name])
    for name, size in SPACE_SIZES.items()
    if SHAPE_COUNTS.get(name, 0) > 0
}

# Defining wall kick data for Arika SRS. Source: https://tetris.fandom.com/wiki/Super_Rotation_System
#TODO: Implement wall kicks
KICK_TABLE = {shape_name: [] for shape_name in SHAPES.keys()}

# Defining gravity values for each level.
GRAVITY = [1/48, 1/43, 1/38, 1/33, 1/28, 1/23, 1/18, 1/13, 1/8, 1/6,
           1/5, 1/5, 1/5, 1/4, 1/4, 1/4, 1/3, 1/3, 1/3, 1/2,
           1/2, 1/2, 1/2, 1/2, 1/2, 1/2, 1/2, 1/2, 1/2, 1]

# Countdown at the start of the game
COUNTDOWN = {
    "3": np.array([
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,X,X,X,W,W,X,X],
        [X,X,X,X,X,W,W,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,X,X,X,W,W,X,X],
        [X,X,X,X,X,W,W,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
    ]),

    "2": np.array([
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,X,X,X,W,W,X,X],
        [X,X,X,X,X,W,W,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,W,W,X,X,X,X,X],
        [X,X,W,W,X,X,X,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,W,W,W,W,W,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
    ]),

    "1": np.array([
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,W,W,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
        [X,X,X,X,X,X,X,X,X],
    ]),
}


def _half_countdown(pattern):
    return pattern[::2, ::2]


COUNTDOWN = {k: _half_countdown(v) for k, v in COUNTDOWN.items()}

class Tetromino:
    """Represents a Tetromino piece in the game."""
    def __init__(self, shape):
        self._shape = shape
        self._states = SHAPES[shape]
        self._position = [0, 0] # in padded background coordinates
        self._rotation = 0
        self._lockDelay = 30
        self._lockResets = 15
        self._landed = False

    def getState(self, offset=0):
        return self._states[(self._rotation + offset) % len(self._states)]

    def getPosition(self, offset=[0,0]):
        return [self._position[0] + offset[0], self._position[1] + offset[1]]

    def setPosition(self, position):
        self._position = position

    def setLanded(self, state):
        self._landed = state

    def isLanded(self):
        return self._landed

    def setLockDelay(self, increment):
        self._lockDelay -= increment

    def resetLockDelay(self):
        self._lockDelay = 30

    def getLockDelay(self):
        return self._lockDelay

    def rotateCW(self):
        oldRotation = self._rotation
        self._rotation = (self._rotation + 1) % len(self._states)
        self._lockDelay = 30
        return (oldRotation, self._rotation)

    def rotateCCW(self):
        oldRotation = self._rotation
        self._rotation = (self._rotation - 1) % len(self._states)
        self._lockDelay = 30
        return (oldRotation, self._rotation)

    def moveLeft(self):
        self._position[1] -= 1
        self._lockDelay = 30

    def moveRight(self):
        self._position[1] += 1
        self._lockDelay = 30


    def moveDown(self):
        self._position[0] += 1
        self._lockDelay = 30

    def lock(self): #TODO: Might be able to remove
        self._lockDelay = 0

    def __str__(self):
        return f"Shape: {self._shape}, Rotation: {self._rotation}"

class Bag:
    """Implements a weighted bag randomizer for room-shape generation."""
    def __init__(self):
        self._bag = []
        self._index = 0

        self._newBag()

    def _newBag(self):
        """Generate a new randomized bag with the requested room counts."""
        self._bag = []
        for shape_name, count in SHAPE_COUNTS.items():
            if count <= 0:
                continue
            self._bag.extend([shape_name] * count)
        np.random.shuffle(self._bag)
        self._index = 0

    def isEmpty(self):
        """Return True when the current bag is exhausted and no more shapes remain."""
        return self._index >= len(self._bag)

    def isExhausted(self):
        """Return True after the last piece in the current bag has been used."""
        return len(self._bag) > 0 and self._index >= len(self._bag)

    def getTetromino(self):
        """Get the next Tetromino from the bag. If the bag is empty,
        generate a new randomized bag then get the next Tetromino.
        """

        if self.isEmpty():
            self._newBag()
            self._index = 0
        shape = self._bag[self._index]
        self._index += 1
        return Tetromino(shape)

GLOBAL_STATE = {
    "HOLD_PIECE": None,
    "PAUSED": False,
    "RESET": False,
    "HOLD_REQUEST": False,
    "RESET_REQUEST": False,
}

class Tetris:
    def __init__(self, display=None, modern=True, ghostPiece=True):
        # Defining standard keybinds
        KEYBINDS = {
            # Keyboard bindings
            pygame.K_UP: self._rotateCW,
            pygame.K_x: self._rotate180,
            pygame.K_LCTRL: self._rotateCCW,
            pygame.K_z: self._rotateCCW,
            pygame.K_w: self._moveUp,
            pygame.K_SPACE: self._hardDrop,
            pygame.K_DOWN: self._softDrop,
            pygame.K_LEFT: self._moveLeft,
            pygame.K_RIGHT: self._moveRight,
            pygame.K_LSHIFT: self._hold,
            pygame.K_c: self._rotateCW,

            # Controller bindings
            pygame.CONTROLLER_BUTTON_DPAD_UP: self._hardDrop,
            pygame.CONTROLLER_BUTTON_DPAD_DOWN: self._softDrop,
            pygame.CONTROLLER_BUTTON_DPAD_LEFT: self._moveLeft,
            pygame.CONTROLLER_BUTTON_DPAD_RIGHT: self._moveRight,
            pygame.JOYAXISMOTION: self._processJoystickAxis,
            pygame.CONTROLLER_BUTTON_A: self._rotateCW,
            pygame.CONTROLLER_BUTTON_B: self._rotateCCW,
            pygame.CONTROLLER_BUTTON_LEFTSHOULDER: self._hold,
            pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: self._hold,
            pygame.CONTROLLER_BUTTON_Y: self._hold
        }

        # Handling settings
        HANDLING = {
            "ARR": 2, # Auto Repeat Rate (frames)
            "DAS": 3, # Delayed Auto Shift (frames)
            "DCD": 2, # DAS Cut Delay (frames)
            "SDF": 6, # Soft Drop Factor (multiplier to gravity)
        }

        self._display = display if display is not None else DummyDisplay()
        self._displayFrame = Frame(rows=BOARD_ROWS, cols=BOARD_COLS)

        # Create background with white border padding around the active frame for collision detection and piece spawning
        self._background = Frame(rows=self._displayFrame.nrows()+3, cols=self._displayFrame.ncols()+2)
        for i in range(self._background.nrows()):
            for j in range(self._background.ncols()):
                if i == 0 or j == 0 or j == self._background.ncols()-1 or i == self._background.nrows()-1 or i == self._background.nrows()-2:
                    self._background.row(i)[j] = W

        self._foreground = Frame(rows=self._displayFrame.nrows()+3, cols=self._displayFrame.ncols()+2)

        self._DCD = HANDLING["DCD"]
        
        self._doCountdown()
        self._resetGame()

        # Set subtick processing rate
        if modern:
            self._subtickRate = MODERN_SIMULATION_RATE
        else:
            self._subtickRate = CLASSIC_SIMULATION_RATE

        self._ghostPiece = ghostPiece
        self._inputManager = InputManager(KEYBINDS)
        self._gameOverActive = False

        pygame.key.set_repeat(NS_PER_FRAME // 1_000_000 * HANDLING["DAS"], NS_PER_FRAME // 1_000_000 * HANDLING["ARR"])

    def play(self):
        """Main game loop."""
        fractionalPosition = 0
        wasPaused = False

        # TODO: Change to hyprid if, process, sleep, while structure with ns
        while self._playing:
            if GLOBAL_STATE.get("HOLD_REQUEST", False):
                self._hold(True)
                GLOBAL_STATE["HOLD_REQUEST"] = False

            if GLOBAL_STATE.get("RESET", False) or GLOBAL_STATE.get("RESET_REQUEST", False):
                self._reset()
                continue

            if self._gameOverActive:
                self._updateDisplayFrame()
                self._display.send(self._displayFrame)
                self._display.showMessage("Fill up")
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._playing = False
                        break
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                        self._playing = False
                        break
                time.sleep(1 / FPS)
                continue

            isPaused = GLOBAL_STATE.get("PAUSED", False)

            if isPaused:
                wasPaused = True
                self._updateDisplayFrame()
                self._display.send(self._displayFrame)
                time.sleep(1 / FPS)
                continue

            if wasPaused:
                # Reset one-shot input gates so controls reliably recover after resume.
                self._CWavailable = True
                self._CCWavailable = True
                self._180available = True
                self._hardDropAvailable = True
                self._DCDCounter = self._DCD
                wasPaused = False

            frameTime = time.perf_counter()
            fractionalPosition += self._gravity * 2 #Running at half normal FPS
            self._DCDCounter += 2

            self.time -= 1/FPS

            while time.perf_counter() - frameTime < 1/FPS:
                simTime = time.perf_counter()
                self._inputManager.process_events()

                while time.perf_counter() - simTime < 1/self._subtickRate:
                    pass # busy wait until next subtick

            self._checkLevelUp() # Check for level up every frame to update gravity if necessary

            #TODO: Fix gravity implementation
            if fractionalPosition >= 1:
                self._moveDown(True)
                fractionalPosition = 0

            self._updateDisplayFrame()

            #TODO: Change to single background thread instead of starting a new thread every frame
            # threading.Thread(target=self._display.send, args=(self._displayFrame,)).start()

            self._display.send(self._displayFrame) #non threaded for testing

        if not self._gameOverActive:
            self._display.send(Frame()) # Set display to black
        pygame.display.quit()
        pygame.quit()


    def _maskTetromino(self):
        '''Mask the active Tetromino onto the foreground frame.'''
        position = self._activeTetromino.getPosition()
        state = self._activeTetromino.getState()
        for i in range(state.shape[0]):
            for j in range(state.shape[1]):
                if state[i][j] != X:
                    self._foreground[position[0]+i][position[1]+j] = state[i][j]

    def _updateDisplayFrame(self):
        '''Update the display frame by masking the foreground frame onto the display frame.'''
        self._foreground[:] = self._background[:]
        if self._ghostPiece:
            self._ghostTetromino()
        self._maskTetromino()
        self._displayFrame[:] = self._foreground[1:self._displayFrame.nrows()+1, 1:self._displayFrame.ncols()+1]

    def _checkCollision(self, position, state):
        '''Check if the given position and state of the active Tetromino would collide with the background.'''
        for i in range(state.shape[0]):
            for j in range(state.shape[1]):
                if state[i][j] != X and self._background[position[0]+i][position[1]+j] != X:
                    return True
        return False

    def _rotateCW(self, eventDown):
        '''Rotate the active Tetromino clockwise.'''
        if eventDown and self._CWavailable:
            self._CWavailable = False
            pos = self._activeTetromino.getPosition()
            state = self._activeTetromino.getState(offset=1)
            if not self._checkCollision(pos, state) and self._DCDCounter >= self._DCD:
                self._activeTetromino.rotateCW()
                self._DCDCounter = 0
        elif not eventDown and not self._CWavailable:
            self._CWavailable = True


    def _rotateCCW(self, eventDown):
        '''Rotate the active Tetromino counterclockwise.'''
        if eventDown and self._CCWavailable:
            self._CCWavailable = False
            pos = self._activeTetromino.getPosition()
            state = self._activeTetromino.getState(offset=-1)
            if not self._checkCollision(pos, state) and self._DCDCounter >= self._DCD:
                self._activeTetromino.rotateCCW()
                self._DCDCounter = 0
        elif not eventDown and not self._CCWavailable:
            self._CCWavailable = True
            self._DCDCounter = 0

    def _rotate180(self, eventDown):
        '''Rotate the active Tetromino 180 degrees.'''
        if eventDown and self._180available:
            self._180available = False
            pos = self._activeTetromino.getPosition()
            state = self._activeTetromino.getState(offset=2)
            if not self._checkCollision(pos, state) and self._DCDCounter >= self._DCD:
                self._activeTetromino.rotateCW()
            self._activeTetromino.rotateCW()
            self._DCDCounter = 0
        elif not eventDown and not self._180available:
            self._180available = True

    def _moveLeft(self, eventDown):
        '''Move the active Tetromino left.'''
        if eventDown:
            pos = self._activeTetromino.getPosition(offset=[0,-1])
            state = self._activeTetromino.getState()
            if not self._checkCollision(pos, state):
                self._activeTetromino.moveLeft()

    def _moveUp(self, eventDown):
        '''Move the active Tetromino up.'''
        if eventDown:
            pos = self._activeTetromino.getPosition(offset=[-1,0])
            state = self._activeTetromino.getState()
            if not self._checkCollision(pos, state):
                self._activeTetromino.setPosition(pos)

    def _moveRight(self, eventDown):
        '''Move the active Tetromino right.'''
        if eventDown:
            pos = self._activeTetromino.getPosition(offset=[0,1])
            state = self._activeTetromino.getState()
            if not self._checkCollision(pos, state):
                self._activeTetromino.moveRight()

    def _moveDown(self, eventDown):
        '''Move the active Tetromino down.'''
        if eventDown:
            pos = self._activeTetromino.getPosition()
            state = self._activeTetromino.getState()
            newpos = [pos[0] + 1, pos[1]]
            if not self._checkCollision(newpos, state):
                self._activeTetromino.setLanded(False)
                self._activeTetromino.moveDown()
                return

            # Collision detected: lock the tetromino into the background and spawn next piece
            # TODO: implement lock delay and lock resets
            for i in range(state.shape[0]):
                for j in range(state.shape[1]):
                    if state[i][j] != X:
                        self._background[pos[0]+i][pos[1]+j] = state[i][j]
            self._checkForClears()
            if self._bag.isExhausted():
                self._gameOver()
                return
            self._activeTetromino = self._bag.getTetromino()
            self._spawnAtCenter(self._activeTetromino)
            self._holdAvailable = True
            if self._checkCollision(self._activeTetromino.getPosition(), self._activeTetromino.getState()):
                self._gameOver()

    def _softDrop(self, eventDown):
        '''Soft drop the active Tetromino.'''
        if eventDown:
            self._moveDown(eventDown)

    def _hardDrop(self, eventDown):
        '''Hard drop the active Tetromino.'''
        if eventDown and self._hardDropAvailable:
            # Move down until collision then lock into background
            self._hardDropAvailable = False
            pos = self._activeTetromino.getPosition()
            state = self._activeTetromino.getState()
            if self._DCDCounter >= self._DCD:
                while True:
                    newpos = [pos[0] + 1, pos[1]]
                    if self._checkCollision(newpos, state):
                        # lock into background
                        for i in range(state.shape[0]):
                            for j in range(state.shape[1]):
                                if state[i][j] != X:
                                    self._background[pos[0]+i][pos[1]+j] = state[i][j]
                        self._checkForClears()
                        if self._bag.isExhausted():
                            self._gameOver()
                            return
                        self._activeTetromino = self._bag.getTetromino()
                        self._spawnAtCenter(self._activeTetromino)
                        if self._checkCollision(self._activeTetromino.getPosition(), self._activeTetromino.getState()):
                            self._gameOver()
                        self._holdAvailable = True
                        self._DCDCounter = 0
                        break
                    self._holdAvailable = True # Allow hold after hard drop
                    self._activeTetromino.moveDown()
                    pos = self._activeTetromino.getPosition()
        elif not eventDown and not self._hardDropAvailable:
            self._hardDropAvailable = True
            self._DCDCounter = 0

    def _ghostTetromino(self):
        pos = self._activeTetromino.getPosition()
        state = self._activeTetromino.getState()
        ghostPos = pos.copy()
        while True:
            newGhostPos = [ghostPos[0] + 1, ghostPos[1]]
            if self._checkCollision(newGhostPos, state):
                break
            ghostPos = newGhostPos
        for i in range(state.shape[0]):
            for j in range(state.shape[1]):
                if state[i][j] != X:
                    self._foreground[ghostPos[0]+i][ghostPos[1]+j] = A

    def _processJoystickAxis(self, axis, value):
        if axis == 0:
            if value < -0.5:
                self._moveLeft(True)
            elif value > 0.5:
                self._moveRight(True)
        elif axis == 1:
            if value < -0.5:
                self._hardDrop(True)
            elif value > 0.5:
                self._softDrop(True)

    def _hold(self, eventDown):
        '''Hold the active Tetromino.'''
        global GLOBAL_STATE

        if not self._holdAvailable:
            return
        if eventDown:
            if self._holdTetromino is None:
                self._holdTetromino = self._activeTetromino
                self._activeTetromino = self._bag.getTetromino()
                self._spawnAtCenter(self._activeTetromino)
            else:
                self._holdTetromino, self._activeTetromino = self._activeTetromino, self._holdTetromino
                self._spawnAtCenter(self._activeTetromino)
            GLOBAL_STATE["HOLD_PIECE"] = self._holdTetromino
            self._holdTetromino.setPosition([0, 0])
            self._holdAvailable = False

    def _checkForClears(self, rows: list[int] | None = None):
        '''Check for completed lines without removing them from the board.'''
        global GLOBAL_STATE

        if rows is None:
            rows = [1, self._background.nrows()-2]

        clear = False
        for i in range(rows[0], rows[1]):
            if all(self._background.row(i)[j] != X for j in range(1, self._background.ncols()-1)):
                clear = True
                self._linesCleared += 1
        if clear:
            frameTime = time.perf_counter()
            self._displayFrame[:] = self._background[1:self._displayFrame.nrows()+1, 1:self._displayFrame.ncols()+1]
            self._display.send(self._displayFrame)
            while time.perf_counter() - frameTime < 5/FPS:
                pass

    def _checkLevelUp(self):
        '''Check if the player has leveled up and increase gravity if so.'''
        # lineTarget = max(self._level * 10 + 10, max(100, self._level * 10 - 50))
        lineTarget = min(self._level + 5, max(100, self._level * 5 - 50)) # Faster level progression for testing
        if lineTarget <= self._linesCleared:
            self._level += 1
            self._linesCleared = self._linesCleared - lineTarget
            self._gravity = GRAVITY[min(self._level, len(GRAVITY)-1)]

    def _fillUp(self):
        '''Fill the background after game over.'''
        for i in reversed(range(1, self._background.nrows()-2)):
            for j in range(1, self._background.ncols()-1):
                self._background.row(i)[j] = W
            frameTime = time.perf_counter()
            self._displayFrame[:] = self._background[1:self._displayFrame.nrows()+1, 1:self._displayFrame.ncols()+1]
            self._display.send(self._displayFrame)
            while time.perf_counter() - frameTime < 2/FPS:
                pass

        print("Waiting for quit")
        for i in range(5):
                print('.', end='')
                self._display.send(self._displayFrame)
                time.sleep(1)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        print("Quitting Tetris")
                        self._playing = False
                        return
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                        print("Quitting Tetris")
                        self._playing = False
                        return

    def _fallDown(self):
        '''Make the background fall down after game over.'''
        for i in range(1, self._background.nrows()-2):
            for j in range(1, self._background.ncols()-1):
                self._background.row(i)[j] = X
            frameTime = time.perf_counter()
            self._displayFrame[:] = self._background[1:self._displayFrame.nrows()+1, 1:self._displayFrame.ncols()+1]
            self._display.send(self._displayFrame)
            while time.perf_counter() - frameTime < 2/FPS:
                pass

    def _gameOver(self):
        '''Print summary and reset game.'''
        global GLOBAL_STATE

        # print(f"Level: {self._level}, Lines Cleared: {self._linesCleared}")
        self._gameOverActive = True
        self._updateDisplayFrame()
        self._display.send(self._displayFrame)
        self._display.showMessage("Fill up")

    def _doCountdown(self):
        for count in ("3", "2", "1"):
            f1 = Frame()
            f1._array = COUNTDOWN[count]
            self._display.send(f1)
            time.sleep(1)

        self._display.send(Frame())

    def _resetGlobal(self):
        global GLOBAL_STATE
        GLOBAL_STATE["HOLD_PIECE"] = None
        GLOBAL_STATE["PAUSED"] = False
        GLOBAL_STATE["RESET"] = False
        GLOBAL_STATE["HOLD_REQUEST"] = False
        GLOBAL_STATE["RESET_REQUEST"] = False

    def _reset(self):
        # Reset to a fresh running state while keeping the current configured catalog.
        self._resetGame()

    def _resetGame(self):
        pygame.event.clear()
        self._resetGlobal()
        self._bag = Bag()
        self._activeTetromino = self._bag.getTetromino()
        self._spawnAtCenter(self._activeTetromino)
        self._holdTetromino = None
        self._holdAvailable = True
        self._level = 0 # Start at level 0 for CPW
        self._gravity = GRAVITY[self._level]
        self._linesCleared = 0
        self.time = 300
        self._CWavailable = True
        self._CCWavailable = True
        self._180available = True
        self._hardDropAvailable = True
        self._DCDCounter = self._DCD
        self._playing = True
        self._gameOverActive = False

    def _spawnAtCenter(self, tetromino):
        state = tetromino.getState()
        playable_rows = self._displayFrame.nrows()
        playable_cols = self._displayFrame.ncols()
        start_row = max(0, (playable_rows - state.shape[0]) // 2)
        start_col = max(1, (playable_cols - state.shape[1]) // 2 + 1)
        tetromino.setPosition([start_row, start_col])

    def _clearBoardFromUI(self):
        for i in range(1, self._background.nrows()-2):
            for j in range(1, self._background.ncols()-1):
                self._background.row(i)[j] = X
        self._foreground[:] = self._background[:]
        self._holdTetromino = None
        GLOBAL_STATE["HOLD_PIECE"] = None
        self._activeTetromino = self._bag.getTetromino()
        self._spawnAtCenter(self._activeTetromino)
        self._linesCleared = 0

def second_screen(state_dict=None):
    if state_dict is None:
        state_dict = GLOBAL_STATE 

    root = tk.Tk()
    root.title("Tetris")
    root.geometry("500x600")
    root.configure(bg="black")

    cell_size = 100
    canvas_size = 4*cell_size
    canvas = tk.Canvas(root, width=canvas_size, height=canvas_size, bg="black", highlightthickness=0)
    cells = dict()
    colors = dict()
    canvas.pack(padx=8, pady=8)

    controls = tk.Frame(root, bg="black")
    controls.pack(padx=8, pady=8)

    pause_button = tk.Button(controls, text="Pause", width=12)
    pause_button.pack(side=tk.LEFT, padx=6)

    reset_button = tk.Button(controls, text="Reset", width=12)
    reset_button.pack(side=tk.LEFT, padx=6)

    def empty_canvas():
        for r in range(4):
            for c in range(4):
                x0 = c*cell_size
                y0 = r*cell_size
                rect = canvas.create_rectangle(x0,y0,x0+cell_size,y0+cell_size, fill="black")
                cells[(r,c)] = rect
                colors[(r,c)] = "black"

    def toggle_pause():
        paused = not state_dict.get("PAUSED", False)
        state_dict["PAUSED"] = paused
        pause_button.config(text="Resume" if paused else "Pause")

    def on_pause_shortcut(_event):
        toggle_pause()
        return "break"

    def reset_board():
        state_dict["RESET_REQUEST"] = True
        state_dict["RESET"] = True
        state_dict["PAUSED"] = False
        pause_button.config(text="Pause")

    root.bind_all("<KeyPress-p>", on_pause_shortcut)
    root.bind_all("<KeyPress-P>", on_pause_shortcut)
    pause_button.config(command=toggle_pause)
    reset_button.config(command=reset_board)

    def update_canvas(hold_piece):
        piece_colors = hold_piece.getState()
        max_r = min(4, piece_colors.shape[0])
        max_c = min(4, piece_colors.shape[1])
        for r in range(4):
            for c in range(4):
                if r < max_r and c < max_c:
                    col = piece_colors[r][c]
                else:
                    col = X
                x0 = c*cell_size
                y0 = r*cell_size
                colors[(r,c)] = f"#{col.r:02x}{col.g:02x}{col.b:02x}"
                canvas.itemconfigure(cells[(r,c)], fill=colors[(r, c)])

    empty_canvas()

    def update_label():
        try:
            if state_dict["HOLD_PIECE"] is not None:
                update_canvas(state_dict["HOLD_PIECE"])
            else:
                empty_canvas()

            pause_button.config(text="Resume" if state_dict.get("PAUSED", False) else "Pause")
        except Exception:
            pass

        root.after(100, update_label)

    root.after(100, update_label)
    root.mainloop()

def background_logic():
    # Perform game calculations, network calls, or input processing here
    pass

if __name__ == "__main__":
    manager = mp.Manager()
    shared_state = manager.dict(GLOBAL_STATE)
    GLOBAL_STATE = shared_state

    p = mp.Process(target=second_screen, args=(shared_state,), daemon=True)
    p.start()

    tetris = Tetris()
    tetris.play()

